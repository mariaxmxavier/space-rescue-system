import unittest

import grimp

APPLICATION = "rescue.application"


class NoCycleThroughApplicationTest(unittest.TestCase):
    def test_application_is_not_part_of_an_import_cycle(self):
        graph = grimp.build_graph("rescue")
        upstream = graph.find_upstream_modules(APPLICATION, as_package=True)
        downstream = graph.find_downstream_modules(APPLICATION, as_package=True)

        offenders = sorted(upstream & downstream)

        self.assertEqual(
            [],
            offenders,
            f"modules import {APPLICATION} and are imported by it: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
