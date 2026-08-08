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
from src.models.user import User
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
        current_user: User,
        name: str,
    ) -> SchoolClass:
        """
        Create a class under a school.
        """

        school = await self.school_repository.get_by_id(current_user.school_id)

        if school is None:
            raise ValueError("School not found.")
        class_existing = await self.class_repository.get_by_name(
            current_user.school_id,
            name,
        )
        if class_existing:
            raise ValueError("Class already exists.")
        logger.info(
            "Creating class",
            school_id=current_user.school_id,
            class_name=name,
        )

        school_class = SchoolClass(
            school_id=current_user.school_id,
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

    async def update_class(
        self,
        class_id: uuid.UUID,
        name: str,
    ) -> SchoolClass:
        """
        Update a class's name.
        """

        school_class = await self.class_repository.get_by_id(class_id)

        if school_class is None:
            raise ValueError("Class not found.")

        logger.info(
            "Updating class",
            class_id=class_id,
            new_name=name,
        )

        school_class.name = name

        return await self.class_repository.update(school_class)

    async def delete_class(
        self,
        class_id: uuid.UUID,
    ) -> None:
        """
        Delete a class.
        """

        school_class = await self.class_repository.get_by_id(class_id)

        if school_class is None:
            raise ValueError("Class not found.")

        logger.info(
            "Deleting class",
            class_id=class_id,
        )

        await self.class_repository.delete(school_class)

    async def get_class_by_teacher(
        self,
        teacher_id: uuid.UUID,
    ) -> list[SchoolClass]:
        """
        Fetch all classes assigned to a teacher.
        """

        return await self.class_repository.get_by_teacher(teacher_id)
