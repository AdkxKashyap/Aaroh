from uuid import UUID

from src.enums.role import RoleName
from src.models.user import User
from src.repositories.school_class_repository import SchoolClassRepository
from src.repositories.teacher_class_repository import TeacherClassRepository
from src.repositories.user_repository import UserRepository
from src.models.teacher_class import TeacherClass

class TeacherService:

    def __init__(
        self,
        teacher_class_repository: TeacherClassRepository,
        class_repository: SchoolClassRepository,
        user_repository: UserRepository,
    ):
        self.teacher_class_repository = teacher_class_repository
        self.class_repository = class_repository
        self.user_repository = user_repository

    async def assign_teacher(
        self,
        current_user: User,
        teacher_id: UUID,
        class_id: UUID,
    ):
        teacher = await self.user_repository.get_by_id_with_roles(
            teacher_id,
        )

        if teacher is None:
            raise ValueError("Teacher not found.")
        if teacher.school_id != current_user.school_id:
            raise ValueError("Teacher does not belong to your school.")
        if RoleName.TEACHER not in {role.name for role in teacher.roles}:
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
