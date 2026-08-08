"""
Teacher Service

Responsibility:
    Handles teacher management.

A Teacher is simply:
    - User
    - TEACHER Role
    - Belongs to a School
"""

import uuid

from src.core.logger import logger
from src.enums.role import RoleName
from src.models.teacher_class import TeacherClass
from src.models.user import User
from src.repositories.role_repository import RoleRepository
from src.repositories.school_class_repository import SchoolClassRepository
from src.repositories.teacher_class_repository import TeacherClassRepository
from src.repositories.user_repository import UserRepository
from src.schemas.teacher import InviteTeacherRequest
from src.services.user_service import UserService

# =============================================================================
# TODO (Post MVP)
#
# Improve teacher invitation workflow:
#
# 1. Generate a temporary password instead of accepting one from the admin.
# 2. Email the temporary password to the teacher.
# 3. Create the teacher with is_active = False.
# 4. On first login:
#    - Force the teacher to change the temporary password.
#    - Set is_active = True after successful password update.
# 5. Periodically clean up invited accounts that were never activated
#    (e.g., is_active = False for more than 30 days).
#
# This is intentionally deferred to keep the MVP simple.
# =============================================================================


class TeacherService:

    def __init__(
        self,
        user_service: UserService,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        class_repository: SchoolClassRepository,
        teacher_class_repository: TeacherClassRepository,
    ):
        self.user_service = user_service
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.class_repository = class_repository
        self.teacher_class_repository = teacher_class_repository

    async def invite_teacher(
        self,
        current_user: User,
        request: InviteTeacherRequest,
    ) -> User:
        """
        Invite a teacher.

        Flow:
            Register User
            -> Assign School
            -> Assign Teacher Role
        """

        logger.info(
            "Inviting teacher",
            admin_id=current_user.id,
            username=request.username,
        )
        if current_user.school_id is None:
            raise ValueError("Admin does not belong to a school.")
        teacher = await self.user_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
        )

        teacher.school_id = current_user.school_id

        await self.user_repository.update(
            teacher,
        )

        teacher_role = await self.role_repository.get_by_name(
            RoleName.TEACHER,
        )

        if teacher_role is None:
            raise ValueError("Teacher role does not exist.")

        await self.role_repository.assign_role(
            user=teacher,
            role=teacher_role,
        )

        logger.info(
            "Teacher invited successfully",
            teacher_id=teacher.id,
        )

        return teacher

    async def get_teachers(
        self,
        current_user: User,
    ) -> list[User]:
        """
        Returns all teachers
        belonging to the admin's school.
        """
        logger.info(
            "Fetching teachers for school",
            school_id=current_user.school_id,
        )
        users = await self.user_repository.get_by_school(
            current_user.school_id,
        )

        return [
            user
            for user in users
            if RoleName.TEACHER in {user_role.role.name for user_role in user.roles}
        ]

    async def assign_teacher(
        self,
        current_user: User,
        teacher_id: uuid.UUID,
        class_id: uuid.UUID,
    ) -> TeacherClass:
        """
        Assign teacher to a class.
        """

        teacher = await self.user_repository.get_by_id_with_roles(
            teacher_id,
        )

        if teacher is None:
            raise ValueError("Teacher not found.")

        if teacher.school_id != current_user.school_id:
            raise ValueError("Teacher does not belong to your school.")

        if RoleName.TEACHER not in {user_role.role.name for user_role in teacher.roles}:
            raise ValueError("User is not a teacher.")

        school_class = await self.class_repository.get_by_id(
            class_id,
        )

        if school_class is None:
            raise ValueError("Class not found.")

        if school_class.school_id != current_user.school_id:
            raise ValueError("Class does not belong to your school.")

        existing = await self.teacher_class_repository.get(
            teacher_id,
            class_id,
        )

        if existing:
            raise ValueError("Teacher already assigned.")

        mapping = TeacherClass(
            teacher_id=teacher.id,
            class_id=school_class.id,
        )

        return await self.teacher_class_repository.create(
            mapping,
        )
