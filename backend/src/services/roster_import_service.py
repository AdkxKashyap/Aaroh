from __future__ import annotations

from src.enums.role import RoleName
from src.repositories.school_class_repository import SchoolClassRepository
from src.services.school_class_service import SchoolClassService
from src.services.student_service import StudentService


class RosterImportService:
    def __init__(
        self,
        class_repository: SchoolClassRepository,
        class_service: SchoolClassService,
        student_service: StudentService,
    ):
        self.class_repository = class_repository
        self.class_service = class_service
        self.student_service = student_service

    @staticmethod
    def _role_names(current_user) -> set[str]:
        names: set[str] = set()
        for user_role in getattr(current_user, "roles", []) or []:
            role_name = getattr(getattr(user_role, "role", None), "name", None)
            if role_name:
                names.add(role_name)
        return names

    async def import_roster(self, current_user, rows, class_name=None, school_id=None):
        if RoleName.ADMIN not in self._role_names(current_user):
            raise ValueError("Only admins can import class rosters.")

        created_classes = 0
        created_students = 0

        for row in rows or []:
            row_class_name = (
                row.get("grade_class") or row.get("class_name") or class_name
            )
            if not row_class_name:
                raise ValueError("Roster row is missing class information.")

            school_class = await self.class_repository.get_by_name(
                current_user.school_id,
                row_class_name,
            )
            if school_class is None:
                school_class = await self.class_service.create_class(
                    current_user=current_user,
                    name=row_class_name,
                )
                created_classes += 1
                class_id = school_class.id
            else:
                class_id = school_class.id

            await self.student_service.create_student(
                current_user=current_user,
                username=row.get("username", ""),
                email=row.get("email", ""),
                password=row.get("password", ""),
                class_id=class_id,
            )
            created_students += 1

        return {
            "rows_processed": len(rows or []),
            "students_created": created_students,
            "classes_created": created_classes,
        }
