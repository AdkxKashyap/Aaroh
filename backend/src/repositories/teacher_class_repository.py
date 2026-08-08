"""
Teacher Class Repository

Responsibility:
    Handles teacher-class mappings.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logger import logger
from src.models.teacher_class import TeacherClass


class TeacherClassRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        mapping: TeacherClass,
    ) -> TeacherClass:

        try:
            self.db.add(mapping)

            await self.db.commit()
            await self.db.refresh(mapping)

            return mapping

        except SQLAlchemyError:
            logger.exception(
                "Failed to create teacher-class mapping",
            )
            raise

    async def get(
        self,
        teacher_id: uuid.UUID,
        class_id: uuid.UUID,
    ) -> TeacherClass | None:

        result = await self.db.execute(
            select(TeacherClass).where(
                TeacherClass.teacher_id == teacher_id,
                TeacherClass.class_id == class_id,
            )
        )

        return result.scalar_one_or_none()
