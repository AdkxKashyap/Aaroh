"""
Submission Repository

Responsibility:
    Handles persistence operations for Submission.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.core.logger import logger
from src.models.student import Student
from src.models.submission import Submission


class SubmissionRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def create(
        self,
        submission: Submission,
    ) -> Submission:
        try:
            self.db.add(submission)

            await self.db.flush()
            await self.db.refresh(submission)

            logger.info(
                "Submission created",
                submission_id=submission.id,
                assignment_id=submission.assignment_id,
                student_id=submission.student_id,
            )

            return submission

        except SQLAlchemyError:
            logger.exception(
                "Failed to create submission",
                assignment_id=submission.assignment_id,
                student_id=submission.student_id,
            )
            raise

    async def get_by_id(
        self,
        submission_id: uuid.UUID,
    ) -> Submission | None:
        try:
            result = await self.db.execute(
                select(Submission)
                .options(
                    selectinload(Submission.assignment),
                    selectinload(Submission.student).selectinload(Student.user),
                    selectinload(Submission.student).selectinload(Student.school_class),
                )
                .where(Submission.id == submission_id)
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch submission",
                submission_id=submission_id,
            )
            raise

    async def get_by_assignment_and_student(
        self,
        assignment_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> Submission | None:
        try:
            result = await self.db.execute(
                select(Submission).where(
                    Submission.assignment_id == assignment_id,
                    Submission.student_id == student_id,
                )
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch student submission",
                assignment_id=assignment_id,
                student_id=student_id,
            )
            raise

    async def update(
        self,
        submission: Submission,
    ) -> Submission:
        try:
            await self.db.flush()
            await self.db.refresh(submission)

            logger.info(
                "Submission updated",
                submission_id=submission.id,
            )

            return submission

        except SQLAlchemyError:
            logger.exception(
                "Failed to update submission",
                submission_id=submission.id,
            )
            raise

    async def get_by_assignment(
        self,
        assignment_id: uuid.UUID,
    ) -> list[Submission]:
        try:
            result = await self.db.execute(
                select(Submission)
                .options(
                    selectinload(Submission.assignment),
                    selectinload(Submission.student).selectinload(Student.user),
                    selectinload(Submission.student).selectinload(Student.school_class),
                )
                .where(Submission.assignment_id == assignment_id)
            )

            return list(result.scalars().all())
        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch submissions for assignment",
                assignment_id=assignment_id,
            )
            raise
