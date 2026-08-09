"""
Student Repository

Responsibility:
    Handles persistence operations for Student.
"""

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.student import Student

logger = structlog.get_logger(__name__)


class StudentRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def create(
        self,
        student: Student,
    ) -> Student:
        try:
            self.db.add(student)

            await self.db.flush()
            await self.db.refresh(student)

            loaded_student = await self.get_by_id(student.id)

            logger.info(
                "Student created",
                student_id=loaded_student.id if loaded_student else student.id,
                user_id=student.user_id,
            )

            return loaded_student or student

        except SQLAlchemyError:
            logger.exception(
                "Failed to create student",
                user_id=student.user_id,
            )
            raise

    async def get_by_id(
        self,
        student_id: uuid.UUID,
    ) -> Student | None:
        try:
            result = await self.db.execute(
                select(Student)
                .options(
                    selectinload(Student.user),
                    selectinload(Student.school_class),
                    selectinload(Student.school),
                )
                .where(Student.id == student_id)
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch student",
                student_id=student_id,
            )
            raise

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> Student | None:
        try:
            result = await self.db.execute(
                select(Student)
                .options(
                    selectinload(Student.user),
                    selectinload(Student.school_class),
                    selectinload(Student.school),
                )
                .where(Student.user_id == user_id)
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch student by user",
                user_id=user_id,
            )
            raise

    async def get_by_class(
        self,
        class_id: uuid.UUID,
    ) -> list[Student]:
        try:
            result = await self.db.execute(
                select(Student)
                .options(
                    selectinload(Student.user),
                    selectinload(Student.school_class),
                    selectinload(Student.school),
                )
                .where(Student.class_id == class_id)
            )

            return list(result.scalars().all())

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch students for class",
                class_id=class_id,
            )
            raise
