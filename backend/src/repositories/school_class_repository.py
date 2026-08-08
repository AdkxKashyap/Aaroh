"""
School Class Repository

Responsibility:
    Handles database operations related to school classes.

Used By:
    SchoolService
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logger import logger
from src.models.school_class import SchoolClass
from src.models.teacher_class import TeacherClass


class SchoolClassRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        school_class: SchoolClass,
    ) -> SchoolClass:
        """
        Create a school class.
        """

        try:
            self.db.add(school_class)

            await self.db.commit()
            await self.db.refresh(school_class)

            return school_class

        except SQLAlchemyError:
            logger.exception(
                "Failed to create class",
                class_name=school_class.name,
            )
            raise

    async def get_by_id(
        self,
        class_id: uuid.UUID,
    ) -> SchoolClass | None:
        """
        Fetch class by ID.
        """

        try:
            result = await self.db.execute(
                select(SchoolClass).where(SchoolClass.id == class_id)
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch class",
                class_id=class_id,
            )
            raise

    async def get_by_school(
        self,
        school_id: uuid.UUID,
    ) -> list[SchoolClass]:
        """
        Fetch all classes for a school.
        """

        try:
            result = await self.db.execute(
                select(SchoolClass).where(SchoolClass.school_id == school_id)
            )

            return list(result.scalars().all())

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch classes",
                school_id=school_id,
            )
            raise

    async def get_by_name(
        self,
        school_id: uuid.UUID,
        name: str,
    ) -> SchoolClass | None:
        """
        Fetch class by name within a school.
        """

        try:
            result = await self.db.execute(
                select(SchoolClass).where(
                    SchoolClass.school_id == school_id,
                    SchoolClass.name == name,
                )
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch class",
                school_id=school_id,
                class_name=name,
            )
            raise

    async def get_by_teacher(
        self,
        teacher_id: uuid.UUID,
    ) -> list[SchoolClass]:
        """
        Fetch all classes assigned to a teacher.
        """

        try:
            result = await self.db.execute(
                select(SchoolClass)
                .join(TeacherClass, TeacherClass.class_id == SchoolClass.id)
                .where(TeacherClass.teacher_id == teacher_id)
            )

            return list(result.scalars().all())

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch classes by teacher",
                teacher_id=teacher_id,
            )
            raise

    async def update(
        self,
        school_class: SchoolClass,
    ) -> SchoolClass:
        """
        Update class.
        """

        try:

            await self.db.commit()
            await self.db.refresh(school_class)

            return school_class

        except SQLAlchemyError:

            logger.exception(
                "Failed to update class",
                class_id=school_class.id,
            )

            raise

    async def delete(
        self,
        school_class: SchoolClass,
    ):
        """
        Delete class.
        """

        try:

            await self.db.delete(
                school_class,
            )

            await self.db.commit()

        except SQLAlchemyError:

            logger.exception(
                "Failed to delete class",
                class_id=school_class.id,
            )

            raise
