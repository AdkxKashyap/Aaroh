"""
Guardian Service

Responsibility:
    Handles guardian business logic.
"""

import uuid

from src.core.logger import logger
from src.db.transaction import transactional
from src.enums.role import RoleName
from src.models.guardian_links import GuardianLink
from src.models.student import Student
from src.models.user import User
from src.repositories.guardian_link_repository import GuardianLinkRepository
from src.repositories.role_repository import RoleRepository
from src.repositories.student_repository import StudentRepository
from src.repositories.user_repository import UserRepository
from src.schemas.student import StudentResponse
from src.services.user_service import UserService


class GuardianService:
    def __init__(
        self,
        user_repository: UserRepository,
        student_repository: StudentRepository,
        guardian_link_repository: GuardianLinkRepository,
        role_repository: RoleRepository,
        db,
    ):
        self.user_repository = user_repository
        self.student_repository = student_repository
        self.guardian_link_repository = guardian_link_repository
        self.role_repository = role_repository
        self.db = db

    async def create_guardian(
        self,
        current_user: User,
        username: str,
        email: str,
        password: str,
        user_service: UserService,
    ) -> User:
        logger.info(
            "Creating guardian",
            admin_id=current_user.id,
            username=username,
        )

        if current_user.school_id is None:
            raise ValueError("Admin must belong to a school.")

        async with transactional(self.db):
            guardian_user = await user_service.register_user(
                username=username,
                email=email,
                password=password,
            )
            guardian_user.school_id = current_user.school_id
            await self.user_repository.update(guardian_user)

            guardian_role = await self.role_repository.get_by_name(RoleName.GUARDIAN)
            if guardian_role is None:
                raise ValueError("Guardian role not found.")

            await self.role_repository.assign_role(guardian_user, guardian_role)

            return guardian_user

    async def link_guardian_to_student(
        self,
        guardian_user_id: uuid.UUID,
        student_id: uuid.UUID,
        current_user: User | None = None,
    ) -> GuardianLink:
        logger.info(
            "Linking guardian to student",
            guardian_user_id=guardian_user_id,
            student_id=student_id,
        )

        guardian_user = await self.user_repository.get_by_id_with_roles(
            guardian_user_id
        )

        if guardian_user is None:
            raise ValueError("Guardian user not found.")

        if not any(
            user_role.role.name == RoleName.GUARDIAN
            for user_role in getattr(guardian_user, "roles", [])
        ):
            raise ValueError("User must be a guardian.")
        if guardian_user.school_id is None:
            raise ValueError("Guardian must belong to a school.")

        if (
            current_user is not None
            and current_user.school_id != guardian_user.school_id
        ):
            raise ValueError("Guardian and admin must belong to the same school.")

        student = await self.student_repository.get_by_id(student_id)

        if student is None:
            raise ValueError("Student not found.")

        if guardian_user.school_id is None:
            raise ValueError("Guardian must belong to a school.")

        existing_guardian_link = await self.guardian_link_repository.get_by_student_id(
            student_id=student_id
        )

        if existing_guardian_link is not None:
            raise ValueError("Student already has a guardian.")

        if student.school_id != guardian_user.school_id:
            raise ValueError("Guardian and student must belong to the same school.")

        exists = await self.guardian_link_repository.exists(
            guardian_user_id=guardian_user_id,
            student_id=student_id,
        )

        if exists:
            raise ValueError("Guardian is already linked to this student.")

        async with transactional(self.db):
            link = await self.guardian_link_repository.create(
                guardian_user_id=guardian_user_id,
                student_id=student_id,
            )
            return link

    def _to_student_response(self, student: Student) -> StudentResponse:
        return StudentResponse(
            id=student.id,
            user_id=student.user_id,
            school_id=student.school_id,
            class_id=student.class_id,
            username=student.user.username if student.user else None,
            class_name=student.school_class.name if student.school_class else None,
            school_name=student.school.name if student.school else None,
            student_name=student.user.username if student.user else None,
        )

    async def get_linked_students(
        self,
        guardian_user_id: uuid.UUID,
    ) -> list[StudentResponse]:
        logger.info(
            "Fetching guardian linked students",
            guardian_user_id=guardian_user_id,
        )

        students = await self.guardian_link_repository.get_students_by_guardian(
            guardian_user_id=guardian_user_id,
        )

        return [self._to_student_response(student) for student in students]
