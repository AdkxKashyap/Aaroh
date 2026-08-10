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


class SubmissionService:

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

    async def submit_assignment(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> Submission:
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

                submission = Submission(
                    assignment_id=assignment_id,
                    student_id=student.id,
                    status=SubmissionStatus.SUBMITTED,
                    submitted_at=now,
                )

                submission = await self.submission_repository.create(
                    submission,
                )

            else:

                submission.status = SubmissionStatus.SUBMITTED
                submission.submitted_at = now

                submission = await self.submission_repository.update(
                    submission,
                )

            logger.info(
                "Assignment submitted successfully",
                submission_id=submission.id,
                assignment_id=assignment_id,
                student_id=student.id,
            )

            return submission

    async def get_assignment_submissions(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> list[Submission]:
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

        return submissions

    async def review_submission(
        self,
        current_user: User,
        submission_id: uuid.UUID,
        feedback: str,
    ) -> Submission:
        """
        Review a submission for an assignment.
        """

        logger.info(
            "Reviewing submission",
            user_id=current_user.id,
            submission_id=submission_id,
        )

        submission = await self.submission_repository.get_by_id(
            submission_id,
        )

        if submission is None:
            raise ValueError("Submission not found.")

        assignment = submission.assignment

        if assignment is None:
            raise ValueError("Assignment not found.")

        if assignment.teacher_id != current_user.id:
            raise ValueError("You are not the teacher for this assignment.")

        submission.feedback = feedback
        submission.status = SubmissionStatus.UNDER_REVIEW

        async with transactional(self.db):
            submission = await self.submission_repository.update(
                submission,
            )

            logger.info(
                "Submission reviewed successfully",
                submission_id=submission.id,
                assignment_id=submission.assignment_id,
                student_id=submission.student_id,
                teacher_id=current_user.id,
            )

            return submission
