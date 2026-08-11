"""
Guardian Link Repository

Responsibility:
    Handles persistence operations for GuardianLink.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.core.logger import logger
from src.models.guardian_links import GuardianLink
from src.models.student import Student


class GuardianLinkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, guardian_user_id: uuid.UUID, student_id: uuid.UUID
    ) -> GuardianLink:
        try:
            link = GuardianLink(
                guardian_user_id=guardian_user_id,
                student_id=student_id,
            )
            self.db.add(link)
            await self.db.flush()
            await self.db.refresh(link)
            return link
        except SQLAlchemyError:
            logger.exception(
                "Failed to create guardian link",
                guardian_user_id=guardian_user_id,
                student_id=student_id,
            )
            raise

    async def exists(self, guardian_user_id: uuid.UUID, student_id: uuid.UUID) -> bool:
        try:
            result = await self.db.execute(
                select(GuardianLink).where(
                    GuardianLink.guardian_user_id == guardian_user_id,
                    GuardianLink.student_id == student_id,
                )
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError:
            logger.exception(
                "Failed to check guardian link existence",
                guardian_user_id=guardian_user_id,
                student_id=student_id,
            )
            raise

    async def get_by_student_id(self, student_id: uuid.UUID) -> GuardianLink | None:
        try:
            result = await self.db.execute(
                select(GuardianLink).where(GuardianLink.student_id == student_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception(
                "Failed to check guardian link existence",
                guardian_user_id=guardian_user_id,
                student_id=student_id,
            )
            raise

    async def get_students_by_guardian(
        self, guardian_user_id: uuid.UUID
    ) -> list[Student]:
        try:
            result = await self.db.execute(
                select(Student)
                .join(GuardianLink, GuardianLink.student_id == Student.id)
                .options(
                    selectinload(Student.user),
                    selectinload(Student.school),
                    selectinload(Student.school_class),
                )
                .where(GuardianLink.guardian_user_id == guardian_user_id)
            )
            return list(result.scalars().all())
        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch linked students",
                guardian_user_id=guardian_user_id,
            )
            raise
