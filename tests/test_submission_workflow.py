import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.enums.submission import SubmissionStatus
from src.services.submission_state_machine import SubmissionStateMachine


def test_allowed_transitions():
    machine = SubmissionStateMachine()

    assert (
        machine.transition(SubmissionStatus.NOT_SUBMITTED, SubmissionStatus.SUBMITTED)
        == SubmissionStatus.SUBMITTED
    )
    assert (
        machine.transition(SubmissionStatus.SUBMITTED, SubmissionStatus.UNDER_REVIEW)
        == SubmissionStatus.UNDER_REVIEW
    )
    assert (
        machine.transition(
            SubmissionStatus.UNDER_REVIEW, SubmissionStatus.REVISION_REQUESTED
        )
        == SubmissionStatus.REVISION_REQUESTED
    )
    assert (
        machine.transition(
            SubmissionStatus.REVISION_REQUESTED, SubmissionStatus.RESUBMITTED
        )
        == SubmissionStatus.RESUBMITTED
    )
    assert (
        machine.transition(SubmissionStatus.RESUBMITTED, SubmissionStatus.UNDER_REVIEW)
        == SubmissionStatus.UNDER_REVIEW
    )
    assert (
        machine.transition(SubmissionStatus.UNDER_REVIEW, SubmissionStatus.COMPLETED)
        == SubmissionStatus.COMPLETED
    )


def test_invalid_transition_raises_value_error():
    machine = SubmissionStateMachine()

    try:
        machine.transition(SubmissionStatus.SUBMITTED, SubmissionStatus.COMPLETED)
    except ValueError as exc:
        assert "Invalid transition" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid transition")
