---
kind: rule
id: P-0001
type: constraint
strength: default
status: active
scope:
  - activity:coding
when: writing Python code in this repository
do: give every module, class and public function a docstring that says what it does, when it is called and why it exists
instead_of: no docstrings (the global no-comments default)
because: the owner wants the code to explain itself to readers
source: "2026-11-16: 'all entities/ diffrent classes must be broken into nested files and folders format, docs string include in every code comment about what it dows, when is called, why'"
added: 2026-11-16
approved: 2026-11-16
last_confirmed: 2026-11-16
private: false
---
