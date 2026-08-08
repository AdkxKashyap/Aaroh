"""
Assignment Repository

Responsibility:
    Handles database operations related to assignments.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logger import logger
from src.models.assignment import Assignment


class AssignmentRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def create(
        self,
        assignment: Assignment,
    ) -> Assignment:
        """
        Creates a new assignment.
        """

        try:
            self.db.add(assignment)

            await self.db.flush()
            await self.db.refresh(assignment)

            return assignment

        except SQLAlchemyError:

            logger.exception(
                "Failed to create assignment",
                title=assignment.title,
            )

            raise

    async def get_by_id(
        self,
        assignment_id: uuid.UUID,
    ) -> Assignment | None:
        """
        Returns assignment by id.
        """

        try:

            result = await self.db.execute(
                select(Assignment).where(
                    Assignment.id == assignment_id,
                )
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:

            logger.exception(
                "Failed to fetch assignment",
                assignment_id=assignment_id,
            )

            raise

    async def get_by_class(
        self,
        class_id: uuid.UUID,
    ) -> list[Assignment]:
        """
        Returns all assignments
        for a class.
        """

        try:

            result = await self.db.execute(
                select(Assignment).where(
                    Assignment.class_id == class_id,
                )
            )

            return list(result.scalars().all())

        except SQLAlchemyError:

            logger.exception(
                "Failed to fetch assignments",
                class_id=class_id,
            )

            raise

    async def update(
        self,
        assignment: Assignment,
    ) -> Assignment:
        """
        Updates an assignment.
        """

        try:

            await self.db.flush()
            await self.db.refresh(
                assignment,
            )

            return assignment

        except SQLAlchemyError:

            logger.exception(
                "Failed to update assignment",
                assignment_id=assignment.id,
            )

            raise

    async def delete(
        self,
        assignment: Assignment,
    ) -> None:
        """
        Deletes an assignment.
        """

        try:

            await self.db.delete(
                assignment,
            )

        except SQLAlchemyError:

            logger.exception(
                "Failed to delete assignment",
                assignment_id=assignment.id,
            )

            raise
