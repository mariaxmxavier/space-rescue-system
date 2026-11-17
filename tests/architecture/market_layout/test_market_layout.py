import ast
import enum
import importlib
import importlib.util
import inspect
import pathlib
import pkgutil
import re
import unittest

import rescue.market
import rescue.market.models

ROOT = pathlib.Path(__file__).resolve().parents[3]
MODELS = ROOT / "rescue" / "market" / "models"
CATEGORIES = ("fleet", "availability", "procurement", "quotes", "offers", "inventory")
RULE_SECTIONS = ("## What", "## When", "## Why", "## Refuses")
MODELS_PREFIX = "rescue.market.models"
SHARED_MODULES = ("b3_market", "named_value")
DIAGRAM_REFERENCE = re.compile(r"diagram", re.IGNORECASE)
DIAGRAM_LINK = re.compile(r"\]\([^)]*(class-diagram|entity-relationship-diagram)\.mmd\)")
MMD_TARGET = re.compile(r"\]\(([^)]*\.mmd)\)")


def snake(name):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name).lower()


def market_modules():
    yield rescue.market
    for info in pkgutil.walk_packages(rescue.market.__path__, "rescue.market."):
        yield importlib.import_module(info.name)


def category(name):
    return importlib.import_module(f"{MODELS_PREFIX}.{name}")


def rules(name):
    if importlib.util.find_spec(f"{MODELS_PREFIX}.{name}.rules") is None:
        return None
    return importlib.import_module(f"{MODELS_PREFIX}.{name}.rules")


def rule_documents():
    for name in CATEGORIES:
        module = rules(name)
        for rule_name in module.__all__ if module else ():
            rule = getattr(module, rule_name)
            yield name, rule_name, rule, pathlib.Path(inspect.getfile(rule)).with_suffix(".md")


def documented_items(module):
    yield module
    for name, value in vars(module).items():
        if (
            not name.startswith("_")
            and (inspect.isclass(value) or inspect.isfunction(value))
            and value.__module__ == module.__name__
        ):
            yield value


def imported_modules(path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module
            if node.module in ("rescue.market", MODELS_PREFIX):
                for alias in node.names:
                    yield f"{node.module}.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name


def caller_files():
    this_file = pathlib.Path(__file__).resolve()
    for folder in ("rescue", "tests"):
        for path in (ROOT / folder).rglob("*.py"):
            if MODELS not in path.parents and path != this_file:
                yield path


def is_allowed_import(module_name):
    if module_name == "rescue.market":
        return True
    if module_name.startswith("rescue.market.rules"):
        return False
    if not module_name.startswith(MODELS_PREFIX):
        return True
    parts = module_name.split(".")[3:]
    if not parts:
        return False
    if parts[0] in SHARED_MODULES:
        return len(parts) == 1
    return parts[0] in CATEGORIES and (len(parts) == 1 or parts == [parts[0], "rules"])


class MarketLayoutTests(unittest.TestCase):
    def test_each_entity_lives_in_its_own_file_under_its_category(self):
        for name in CATEGORIES:
            for entity_name in category(name).__all__:
                with self.subTest(entity=entity_name):
                    entity = getattr(category(name), entity_name)
                    self.assertTrue(inspect.isclass(entity))
                    self.assertEqual(
                        entity.__module__, f"{MODELS_PREFIX}.{name}.{snake(entity_name)}"
                    )

    def test_each_category_file_defines_exactly_one_exported_class(self):
        for name in CATEGORIES:
            exported = set(category(name).__all__)
            for path in sorted((MODELS / name).glob("*.py")):
                if path.name == "__init__.py":
                    continue
                with self.subTest(file=f"{name}/{path.name}"):
                    module = importlib.import_module(f"{MODELS_PREFIX}.{name}.{path.stem}")
                    defined = [
                        value.__name__
                        for value in vars(module).values()
                        if inspect.isclass(value) and value.__module__ == module.__name__
                    ]
                    self.assertEqual(len(defined), 1)
                    self.assertIn(defined[0], exported)
                    self.assertEqual(snake(defined[0]), path.stem)

    def test_each_status_enum_lives_in_its_own_file(self):
        for name in CATEGORIES:
            for entity_name in category(name).__all__:
                entity = getattr(category(name), entity_name)
                if issubclass(entity, enum.Enum):
                    with self.subTest(status=entity_name):
                        self.assertEqual(
                            pathlib.Path(inspect.getfile(entity)).name,
                            f"{snake(entity_name)}.py",
                        )

    def test_each_rule_lives_in_its_own_file_with_a_markdown_beside_it(self):
        for name, rule_name, rule, document in rule_documents():
            with self.subTest(rule=rule_name):
                self.assertEqual(rule.__module__, f"{MODELS_PREFIX}.{name}.rules.{rule_name}")
                text = document.read_text(encoding="utf-8")
                self.assertTrue(text.startswith(f"# {rule_name}\n"))
                for section in RULE_SECTIONS:
                    self.assertIn(section, text)

    def test_each_rule_markdown_fills_every_section_and_links_a_diagram(self):
        for _, rule_name, _, document in rule_documents():
            with self.subTest(rule=rule_name):
                text = document.read_text(encoding="utf-8")
                for section in RULE_SECTIONS:
                    body = text.split(section, 1)[1].split("\n## ", 1)[0]
                    self.assertTrue(body.strip(), f"empty {section}")
                self.assertRegex(text, DIAGRAM_LINK)

    def test_each_rule_markdown_diagram_link_resolves(self):
        for _, rule_name, _, document in rule_documents():
            with self.subTest(rule=rule_name):
                targets = MMD_TARGET.findall(document.read_text(encoding="utf-8"))
                self.assertTrue(targets)
                for target in targets:
                    self.assertTrue((document.parent / target).is_file(), target)

    def test_market_has_no_single_entry_points(self):
        self.assertIsNone(importlib.util.find_spec("rescue.market.rules"))
        for package in (rescue.market, rescue.market.models):
            with self.subTest(package=package.__name__):
                exported = {
                    name
                    for name, value in vars(package).items()
                    if inspect.isclass(value) or inspect.isfunction(value)
                }
                self.assertEqual(exported, set())
                self.assertEqual(getattr(package, "__all__", []), [])

    def test_categories_export_entities_and_rules_packages_export_functions(self):
        for name in CATEGORIES:
            with self.subTest(category=name):
                for entity_name in category(name).__all__:
                    self.assertTrue(inspect.isclass(getattr(category(name), entity_name)))
                module = rules(name)
                for rule_name in module.__all__ if module else ():
                    self.assertTrue(inspect.isfunction(getattr(module, rule_name)))

    def test_callers_import_only_category_packages_and_category_rules(self):
        for path in caller_files():
            for module_name in imported_modules(path):
                if module_name.startswith("rescue.market"):
                    with self.subTest(file=str(path.relative_to(ROOT)), imported=module_name):
                        self.assertTrue(is_allowed_import(module_name))

    def test_every_module_class_and_public_function_says_what_when_and_why(self):
        for module in market_modules():
            for item in documented_items(module):
                with self.subTest(item=getattr(item, "__qualname__", item.__name__)):
                    doc = inspect.getdoc(item) or ""
                    self.assertTrue(doc.strip(), "missing docstring")
                    first_line = doc.splitlines()[0].strip()
                    self.assertFalse(first_line.startswith(("When:", "Why:")), "missing what")
                    self.assertIn("When:", doc)
                    self.assertIn("Why:", doc)

    def test_every_module_class_and_public_function_names_its_diagram(self):
        for module in market_modules():
            for item in documented_items(module):
                with self.subTest(item=getattr(item, "__qualname__", item.__name__)):
                    self.assertRegex(inspect.getdoc(item) or "", DIAGRAM_REFERENCE)


if __name__ == "__main__":
    unittest.main()
