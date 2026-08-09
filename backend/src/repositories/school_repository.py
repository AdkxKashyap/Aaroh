"""
School Repository

Responsibility:
    Handles all database operations related to schools.

Used By:
    SchoolService
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logger import logger
from src.models.school import School
from src.models.user import User


class SchoolRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        school: School,
    ) -> School:
        """
        Create a new school.
        """

        try:
            self.db.add(school)

            await self.db.flush()
            await self.db.refresh(school)

            return school

        except SQLAlchemyError:
            logger.exception(
                "Failed to create school",
                school_name=school.name,
            )
            raise

    # TODO:
    # This method manages a cross-aggregate transaction.
    # As we migrate to service-managed transactions (Unit of Work),
    # move transaction ownership to the service layer and remove this method.
    async def register_school(
        self,
        school: School,
        user: User,
    ) -> School:
        """
        Atomically registers a school and links it to the admin user.
        """

        try:
            self.db.add(school)

            await self.db.flush()

            user.school_id = school.id

            await self.db.refresh(school)

            return school

        except SQLAlchemyError:
            logger.exception(
                "Failed to register school",
                school_name=school.name,
                user_id=user.id,
            )
            raise

    async def get_by_id(
        self,
        school_id: uuid.UUID,
    ) -> School | None:
        """
        Fetch school by ID.
        """

        try:
            result = await self.db.execute(select(School).where(School.id == school_id))

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch school",
                school_id=school_id,
            )
            raise

    async def get_by_name(
        self,
        name: str,
    ) -> School | None:
        """
        Fetch school by name.
        """

        try:
            result = await self.db.execute(select(School).where(School.name == name))

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch school",
                school_name=name,
            )
            raise

    async def get_all(
        self,
    ) -> list[School]:
        """
        Fetch all schools.
        """

        try:
            result = await self.db.execute(select(School))

            return list(result.scalars().all())

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch schools",
            )
            raise

    async def update(
        self,
        school: School,
    ) -> School:
        """
        Update school.
        """

        try:
            await self.db.flush()
            await self.db.refresh(school)

            return school

        except SQLAlchemyError:
            logger.exception(
                "Failed to update school",
                school_id=school.id,
            )
            raise

    async def delete(
        self,
        school: School,
    ) -> None:
        """
        Delete school.
        """

        try:
            await self.db.delete(school)

        except SQLAlchemyError:
            logger.exception(
                "Failed to delete school",
                school_id=school.id,
            )
            raise
