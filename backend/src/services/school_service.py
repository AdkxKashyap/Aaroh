"""
School Service

Responsibility:
    Handles school-related business logic.

Used By:
    School APIs
"""

import uuid

import structlog
from src.models.school import School
from src.models.user import User
from src.repositories.school_repository import SchoolRepository
from src.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class SchoolService:

    def __init__(
        self,
        school_repository: SchoolRepository,
        user_repository: UserRepository,
    ):
        self.school_repository = school_repository
        self.user_repository = user_repository

    async def create_school(
        self,
        name: str,
        address: str | None,
    ) -> School:
        """
        Create a new school.
        """

        logger.info(
            "Creating school",
            school_name=name,
        )

        existing_school = await self.school_repository.get_by_name(name)

        if existing_school:
            logger.warning(
                "School already exists",
                school_name=name,
            )
            raise ValueError("School already exists.")

        school = School(
            name=name,
            address=address,
        )

        try:
            school = await self.school_repository.create(school)

            logger.info(
                "School created successfully",
                school_id=school.id,
            )

            return school

        except Exception:
            logger.exception(
                "Failed to create school",
                school_name=name,
            )
            raise

    async def register_school(
        self,
        current_user: User,
        name: str,
        address: str | None,
    ) -> School:
        """
        Register a school and link it to the current admin.
        """

        logger.info(
            "Registering school",
            user_id=current_user.id,
            school_name=name,
        )

        if current_user.school_id is not None:

            logger.warning(
                "User already belongs to a school",
                user_id=current_user.id,
            )

            raise ValueError("User already belongs to a school.")

        existing_school = await self.school_repository.get_by_name(name)

        if existing_school:
            logger.warning(
                "School already exists",
                school_name=name,
            )
            raise ValueError("School already exists.")
        school = School(
            name=name,
            address=address,
        )
        try:
            return await self.school_repository.register_school(
                school=school,
                user=current_user,
            )
        except Exception:

            logger.exception(
                "Failed to register school",
                user_id=current_user.id,
            )

            raise

    async def get_school(
        self,
        school_id: uuid.UUID,
    ) -> School | None:
        """
        Fetch school by ID.
        """

        return await self.repository.get_by_id(school_id)

    async def get_all_schools(
        self,
    ) -> list[School]:
        """
        Fetch all schools.
        """

        return await self.repository.get_all()

    async def update_school(
        self,
        school_id: uuid.UUID,
        name: str,
        address: str | None,
    ) -> School | None:
        """
        Update school.
        """

        school = await self.repository.get_by_id(school_id)

        if school is None:
            logger.warning(
                "School not found",
                school_id=school_id,
            )
            return None

        school.name = name
        school.address = address

        logger.info(
            "Updating school",
            school_id=school.id,
        )

        return await self.repository.update(school)

    async def delete_school(
        self,
        school: School,
    ) -> None:
        """
        Delete school.
        """

        logger.info(
            "Deleting school",
            school_id=school.id,
        )

        await self.repository.delete(school)
