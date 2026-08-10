"""
Submission Service

Responsibility:
    Handles submission business logic.
"""

import uuid
from datetime import datetime, timezone

from src.core.logger import logger
from src.db.transaction import transactional
from src.enums.submission import SubmissionStatus
from src.models.submission import Submission
from src.models.user import User
from src.repositories.assignment_repository import AssignmentRepository
from src.repositories.student_repository import StudentRepository
from src.repositories.submission_repository import SubmissionRepository
from src.schemas.submission import SubmissionResponse
from src.services.submission_state_machine import SubmissionStateMachine


class SubmissionService:

    def _to_response(self, submission: Submission) -> SubmissionResponse:
        return SubmissionResponse(
            id=submission.id,
            assignment_id=submission.assignment_id,
            student_id=submission.student_id,
            status=submission.status,
            submitted_at=submission.submitted_at,
            feedback=submission.feedback,
            assignment_name=(
                submission.assignment.title if submission.assignment else None
            ),
            student_name=(
                submission.student.user.username
                if submission.student and submission.student.user
                else None
            ),
            class_name=(
                submission.student.school_class.name
                if submission.student and submission.student.school_class
                else None
            ),
            class_id=submission.student.class_id if submission.student else None,
        )

    def __init__(
        self,
        submission_repository: SubmissionRepository,
        student_repository: StudentRepository,
        assignment_repository: AssignmentRepository,
        db,
    ):
        self.submission_repository = submission_repository
        self.student_repository = student_repository
        self.assignment_repository = assignment_repository
        self.db = db
        self.state_machine = SubmissionStateMachine()

    async def submit_assignment(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> SubmissionResponse:
        """
        Submit an assignment for the authenticated student.

        For MVP, the actual submitted content/file reference
        will be added when we implement the submission payload.
        """

        logger.info(
            "Submitting assignment",
            user_id=current_user.id,
            assignment_id=assignment_id,
        )

        student = await self.student_repository.get_by_user_id(
            current_user.id,
        )

        if student is None:
            raise ValueError("Student profile not found.")

        assignment = await self.assignment_repository.get_by_id(
            assignment_id,
        )

        if assignment is None:
            raise ValueError("Assignment not found.")

        # Student must belong to the class
        # targeted by the assignment.
        if assignment.class_id != student.class_id:
            raise ValueError("Assignment does not belong to your class.")

        async with transactional(self.db):
            submission = await self.submission_repository.get_by_assignment_and_student(
                assignment_id=assignment_id,
                student_id=student.id,
            )

            now = datetime.now(timezone.utc)

            if submission is None:
                target_status = SubmissionStatus.SUBMITTED
                self.state_machine.transition(
                    SubmissionStatus.NOT_SUBMITTED,
                    target_status,
                )
                submission = Submission(
                    assignment_id=assignment_id,
                    student_id=student.id,
                    status=target_status,
                    submitted_at=now,
                )
                submission = await self.submission_repository.create(submission)
            else:
                if submission.status != SubmissionStatus.REVISION_REQUESTED:
                    raise ValueError(
                        "Resubmission is only allowed after revision is requested."
                    )

                target_status = SubmissionStatus.RESUBMITTED
                self.state_machine.transition(
                    submission.status,
                    target_status,
                )
                submission.status = target_status
                submission.submitted_at = now
                submission.feedback = None
                submission = await self.submission_repository.update(submission)

            logger.info(
                "Assignment submitted successfully",
                submission_id=submission.id,
                assignment_id=assignment_id,
                student_id=student.id,
            )

            return self._to_response(submission)

    async def get_assignment_submissions(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> list[SubmissionResponse]:
        """
        Get all submissions for an assignment.
        """

        logger.info(
            "Fetching assignment submissions",
            user_id=current_user.id,
            assignment_id=assignment_id,
        )

        assignment = await self.assignment_repository.get_by_id(
            assignment_id,
        )

        if assignment is None:
            raise ValueError("Assignment not found.")

        if assignment.teacher_id != current_user.id:
            raise ValueError("You are not the teacher for this assignment.")

        submissions = await self.submission_repository.get_by_assignment(
            assignment_id,
        )

        return [self._to_response(submission) for submission in submissions]

    async def start_review(
        self,
        current_user: User,
        submission_id: uuid.UUID,
    ) -> SubmissionResponse:
        logger.info(
            "Starting review",
            user_id=current_user.id,
            submission_id=submission_id,
        )

        submission = await self.submission_repository.get_by_id(submission_id)

        if submission is None:
            raise ValueError("Submission not found.")

        assignment = submission.assignment
        if assignment is None:
            raise ValueError("Assignment not found.")

        if assignment.teacher_id != current_user.id:
            raise ValueError("You are not the teacher for this assignment.")

        async with transactional(self.db):
            target_status = self.state_machine.transition(
                submission.status,
                SubmissionStatus.UNDER_REVIEW,
            )
            submission.status = target_status
            submission = await self.submission_repository.update(submission)

            logger.info(
                "Submission moved to under review",
                submission_id=submission.id,
                assignment_id=submission.assignment_id,
                student_id=submission.student_id,
                teacher_id=current_user.id,
            )
            return self._to_response(submission)

    async def request_revision(
        self,
        current_user: User,
        submission_id: uuid.UUID,
        feedback: str,
    ) -> SubmissionResponse:
        logger.info(
            "Requesting revision",
            user_id=current_user.id,
            submission_id=submission_id,
        )

        submission = await self.submission_repository.get_by_id(submission_id)
        if submission is None:
            raise ValueError("Submission not found.")

        assignment = submission.assignment
        if assignment is None:
            raise ValueError("Assignment not found.")

        if assignment.teacher_id != current_user.id:
            raise ValueError("You are not the teacher for this assignment.")

        async with transactional(self.db):
            target_status = self.state_machine.transition(
                submission.status,
                SubmissionStatus.REVISION_REQUESTED,
            )
            submission.status = target_status
            submission.feedback = feedback
            submission = await self.submission_repository.update(submission)

            logger.info(
                "Submission revision requested",
                submission_id=submission.id,
                assignment_id=submission.assignment_id,
                student_id=submission.student_id,
                teacher_id=current_user.id,
            )
            return self._to_response(submission)

    async def complete_submission(
        self,
        current_user: User,
        submission_id: uuid.UUID,
    ) -> SubmissionResponse:
        logger.info(
            "Completing submission",
            user_id=current_user.id,
            submission_id=submission_id,
        )

        submission = await self.submission_repository.get_by_id(submission_id)
        if submission is None:
            raise ValueError("Submission not found.")

        assignment = submission.assignment
        if assignment is None:
            raise ValueError("Assignment not found.")

        if assignment.teacher_id != current_user.id:
            raise ValueError("You are not the teacher for this assignment.")

        async with transactional(self.db):
            target_status = self.state_machine.transition(
                submission.status,
                SubmissionStatus.COMPLETED,
            )
            submission.status = target_status
            submission = await self.submission_repository.update(submission)

            logger.info(
                "Submission completed",
                submission_id=submission.id,
                assignment_id=submission.assignment_id,
                student_id=submission.student_id,
                teacher_id=current_user.id,
            )
            return self._to_response(submission)
