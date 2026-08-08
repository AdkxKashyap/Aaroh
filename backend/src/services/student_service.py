"""
Student Service

Responsibility:
    Handles student business logic.
"""

import uuid

from src.core.logger import logger
from src.enums.role import RoleName
from src.models.student import Student
from src.models.user import User
from src.repositories.role_repository import RoleRepository
from src.repositories.school_class_repository import SchoolClassRepository
from src.repositories.student_repository import StudentRepository
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService


class StudentService:

    def __init__(
        self,
        user_service: UserService,
        user_repository: UserRepository,
        student_repository: StudentRepository,
        role_repository: RoleRepository,
        class_repository: SchoolClassRepository,
    ):
        self.user_service = user_service
        self.user_repository = user_repository
        self.student_repository = student_repository
        self.role_repository = role_repository
        self.class_repository = class_repository

    async def create_student(
        self,
        current_user: User,
        username: str,
        email: str,
        password: str,
        class_id: uuid.UUID,
    ) -> Student:
        """
        Creates a student in the current admin's school.
        """

        logger.info(
            "Creating student",
            admin_id=current_user.id,
            class_id=class_id,
            username=username,
        )

        school_class = await self.class_repository.get_by_id(
            class_id,
        )

        if school_class is None:
            raise ValueError("Class not found.")

        if school_class.school_id != current_user.school_id:
            raise ValueError("Class does not belong to your school.")

        existing_user = await self.user_repository.get_by_username(
            username,
        )

        if existing_user:
            raise ValueError("Username already exists.")

        existing_user = await self.user_repository.get_by_email(
            email,
        )

        if existing_user:
            raise ValueError("Email already exists.")

        try:
            student_user = await self.user_service.register_user(
                username=username,
                email=email,
                password=password,
            )

            student_user.school_id = current_user.school_id

            await self.user_repository.update(
                student_user,
            )

            student_role = await self.role_repository.get_by_name(
                RoleName.STUDENT,
            )

            if student_role is None:
                raise ValueError("Student role not found.")

            await self.role_repository.assign_role(
                student_user,
                student_role,
            )

            student = Student(
                user_id=student_user.id,
                school_id=current_user.school_id,
                class_id=class_id,
            )

            student = await self.student_repository.create(
                student,
            )

            logger.info(
                "Student created successfully",
                student_id=student.id,
                user_id=student_user.id,
                school_id=current_user.school_id,
                class_id=class_id,
            )

            return student

        except Exception:
            logger.exception(
                "Failed to create student",
                admin_id=current_user.id,
                username=username,
            )
            raise

    async def get_students(
        self,
        current_user: User,
        class_id: uuid.UUID,
    ) -> list[Student]:
        """
        Returns students belonging to a class
        in the current user's school.
        """

        logger.info(
            "Fetching students",
            user_id=current_user.id,
            class_id=class_id,
        )

        school_class = await self.class_repository.get_by_id(
            class_id,
        )

        if school_class is None:
            raise ValueError("Class not found.")

        if school_class.school_id != current_user.school_id:
            raise ValueError("Class does not belong to your school.")

        return await self.student_repository.get_by_class(
            class_id,
        )

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> Student | None:
        """
        Get student profile by authenticated user id.
        """

        logger.info(
            "Fetching student profile",
            user_id=user_id,
        )

        return await self.student_repository.get_by_user_id(
            user_id,
        )
