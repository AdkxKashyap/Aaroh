"""
School Class Service

Responsibility:
    Handles school class business logic.
"""

import uuid

import structlog
from src.models.school_class import SchoolClass
from src.repositories.school_class_repository import SchoolClassRepository
from src.repositories.school_repository import SchoolRepository

logger = structlog.get_logger(__name__)


class SchoolClassService:

    def __init__(
        self,
        class_repository: SchoolClassRepository,
        school_repository: SchoolRepository,
    ):
        self.class_repository = class_repository
        self.school_repository = school_repository

    async def create_class(
        self,
        school_id: uuid.UUID,
        name: str,
    ) -> SchoolClass:
        """
        Create a class under a school.
        """

        school = await self.school_repository.get_by_id(school_id)

        if school is None:
            raise ValueError("School not found.")

        logger.info(
            "Creating class",
            school_id=school_id,
            class_name=name,
        )

        school_class = SchoolClass(
            school_id=school_id,
            name=name,
        )

        return await self.class_repository.create(school_class)

    async def get_classes(
        self,
        school_id: uuid.UUID,
    ) -> list[SchoolClass]:
        """
        Fetch all classes for a school.
        """

        return await self.class_repository.get_by_school(school_id)
