"""baseline_identity_ids lists every identity a baseline carries, sorted."""

import unittest
from dataclasses import dataclass

from rescue.experiments.simulation.baseline_identity_ids import baseline_identity_ids


@dataclass(frozen=True)
class Inner:
    ship_id: str
    label: str = "ignored"


@dataclass(frozen=True)
class Baseline:
    missions: tuple
    command_index: tuple = ()
    delivery_index: tuple = ()


class BaselineIdentityIdsTests(unittest.TestCase):
    def test_collects_id_fields_and_index_keys_sorted(self) -> None:
        baseline = Baseline(
            missions=(Inner("zeta"), (Inner("alpha"),)),
            command_index=(("run", "cmd-1", 1, 2, 3), ("short",)),
            delivery_index=(("d-1", "m-1", 7), ("only", "two")),
        )
        self.assertEqual(
            baseline_identity_ids(baseline),
            ("alpha", "cmd-1", "d-1", "m-1", "zeta"),
        )


if __name__ == "__main__":
    unittest.main()
