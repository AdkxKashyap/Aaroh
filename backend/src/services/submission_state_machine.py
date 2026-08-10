from src.enums.submission import SubmissionStatus


class SubmissionStateMachine:
    _allowed_transitions = {
        SubmissionStatus.NOT_SUBMITTED: {SubmissionStatus.SUBMITTED},
        SubmissionStatus.SUBMITTED: {SubmissionStatus.UNDER_REVIEW},
        SubmissionStatus.UNDER_REVIEW: {
            SubmissionStatus.REVISION_REQUESTED,
            SubmissionStatus.COMPLETED,
        },
        SubmissionStatus.REVISION_REQUESTED: {SubmissionStatus.RESUBMITTED},
        SubmissionStatus.RESUBMITTED: {SubmissionStatus.UNDER_REVIEW},
        SubmissionStatus.COMPLETED: set(),
    }

    def can_transition(
        self, current: SubmissionStatus, target: SubmissionStatus
    ) -> bool:
        return target in self._allowed_transitions.get(current, set())

    def transition(
        self, current: SubmissionStatus, target: SubmissionStatus
    ) -> SubmissionStatus:
        if not self.can_transition(current, target):
            raise ValueError(
                f"Invalid transition from {current.value} to {target.value}"
            )
        return target
