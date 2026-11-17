"""Mission progress projection tests."""

import unittest

from rescue.mission.models.projections.mission_progress import MissionProgress
from rescue.mission.models.vocabulary import ProgressStatus
from rescue.values import DomainValidationError


class MissionProgressTests(unittest.TestCase):
    def test_complete_when_every_demanded_seat_is_confirmed(self):
        progress = MissionProgress(
            demand=5,
            confirmed=5,
            pending=0,
            unconfirmed=0,
            additional_needed=0,
            status=ProgressStatus.COMPLETE,
        )
        self.assertIs(progress.status, ProgressStatus.COMPLETE)

    def test_awaiting_responses_when_confirmed_and_pending_cover_demand(self):
        progress = MissionProgress(
            demand=5,
            confirmed=2,
            pending=3,
            unconfirmed=3,
            additional_needed=0,
            status=ProgressStatus.AWAITING_RESPONSES,
        )
        self.assertIs(progress.status, ProgressStatus.AWAITING_RESPONSES)

    def test_needs_more_help_when_pending_does_not_cover_demand(self):
        progress = MissionProgress(
            demand=5,
            confirmed=1,
            pending=2,
            unconfirmed=4,
            additional_needed=2,
            status=ProgressStatus.NEEDS_MORE_HELP,
        )
        self.assertIs(progress.status, ProgressStatus.NEEDS_MORE_HELP)

    def test_pending_seats_never_make_a_mission_complete(self):
        with self.assertRaisesRegex(DomainValidationError, "invalid mission progress status"):
            MissionProgress(
                demand=5,
                confirmed=4,
                pending=1,
                unconfirmed=1,
                additional_needed=0,
                status=ProgressStatus.COMPLETE,
            )

    def test_status_must_match_the_counts(self):
        with self.assertRaisesRegex(DomainValidationError, "invalid mission progress status"):
            MissionProgress(
                demand=5,
                confirmed=1,
                pending=2,
                unconfirmed=4,
                additional_needed=2,
                status=ProgressStatus.COMPLETE,
            )

    def test_wire_string_status_is_stored_as_the_member(self):
        progress = MissionProgress(
            demand=5,
            confirmed=2,
            pending=3,
            unconfirmed=3,
            additional_needed=0,
            status="awaiting_responses",
        )
        self.assertIs(progress.status, ProgressStatus.AWAITING_RESPONSES)

    def test_unknown_status_string_is_rejected_with_its_value(self):
        with self.assertRaisesRegex(
            DomainValidationError, "invalid mission progress status: 'finished'"
        ):
            MissionProgress(
                demand=5,
                confirmed=2,
                pending=3,
                unconfirmed=3,
                additional_needed=0,
                status="finished",
            )

    def test_confirmed_and_pending_cannot_exceed_demand(self):
        with self.assertRaisesRegex(DomainValidationError, "exceed mission demand"):
            MissionProgress(
                demand=5,
                confirmed=3,
                pending=3,
                unconfirmed=2,
                additional_needed=0,
                status=ProgressStatus.NEEDS_MORE_HELP,
            )

    def test_unconfirmed_must_be_demand_minus_confirmed(self):
        with self.assertRaisesRegex(DomainValidationError, "unconfirmed seats do not match"):
            MissionProgress(
                demand=5,
                confirmed=2,
                pending=1,
                unconfirmed=4,
                additional_needed=2,
                status=ProgressStatus.NEEDS_MORE_HELP,
            )

    def test_additional_must_be_demand_minus_confirmed_minus_pending(self):
        with self.assertRaisesRegex(DomainValidationError, "additional demand does not match"):
            MissionProgress(
                demand=5,
                confirmed=2,
                pending=1,
                unconfirmed=3,
                additional_needed=1,
                status=ProgressStatus.NEEDS_MORE_HELP,
            )


if __name__ == "__main__":
    unittest.main()
