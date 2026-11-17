"""scripted_outcome turns a scripted rule into an outcome and a confirmed seat count."""

import random
import unittest

from rescue.experiments.models import ScriptedResponse
from rescue.experiments.simulation.scripted_outcome import scripted_outcome
from rescue.mission.models import RequestOutcome


def rule(outcome, seats=None) -> ScriptedResponse:
    return ScriptedResponse(ship_id="s1", request_ordinal=1, outcome=outcome, confirmed_seats=seats)


class ScriptedOutcomeTests(unittest.TestCase):
    def test_table(self) -> None:
        cases = (
            (rule(RequestOutcome.REFUSED), 4, (RequestOutcome.REFUSED, 0)),
            (rule(RequestOutcome.ACCEPTED), 4, (RequestOutcome.ACCEPTED, 4)),
            (rule(RequestOutcome.PARTIALLY_ACCEPTED), 1, (RequestOutcome.REFUSED, 0)),
            (rule(RequestOutcome.ACCEPTED, 0), 4, (RequestOutcome.REFUSED, 0)),
            (rule(RequestOutcome.PARTIALLY_ACCEPTED, 2), 4, (RequestOutcome.PARTIALLY_ACCEPTED, 2)),
            (rule(RequestOutcome.ACCEPTED, 9), 4, (RequestOutcome.ACCEPTED, 4)),
        )
        for scripted, seats, expected in cases:
            with self.subTest(scripted=scripted, seats=seats):
                self.assertEqual(scripted_outcome(scripted, seats, random.Random(1)), expected)

    def test_partial_without_seats_draws_between_one_and_n_minus_one(self) -> None:
        outcome, confirmed = scripted_outcome(
            rule(RequestOutcome.PARTIALLY_ACCEPTED), 5, random.Random(3)
        )
        self.assertEqual(outcome, RequestOutcome.PARTIALLY_ACCEPTED)
        self.assertEqual(confirmed, random.Random(3).randint(1, 4))


if __name__ == "__main__":
    unittest.main()
