import uuid
from datetime import datetime, timezone

from src.core.logger import logger
from src.models.assignment import Assignment
from src.models.user import User
from src.repositories.assignment_repository import AssignmentRepository
from src.repositories.school_class_repository import SchoolClassRepository
from src.repositories.teacher_class_repository import TeacherClassRepository


class AssignmentService:

    def __init__(
        self,
        assignment_repository: AssignmentRepository,
        class_repository: SchoolClassRepository,
        teacher_class_repository: TeacherClassRepository,
    ):
        self.assignment_repository = assignment_repository
        self.class_repository = class_repository
        self.teacher_class_repository = teacher_class_repository

    async def create_assignment(
        self,
        current_user: User,
        title: str,
        description: str,
        due_date: datetime,
        class_id: uuid.UUID,
    ) -> Assignment:
        """
        Creates an assignment.
        """

        logger.info(
            "Creating assignment",
            teacher_id=current_user.id,
            class_id=class_id,
        )

        school_class = await self.class_repository.get_by_id(
            class_id,
        )

        if school_class is None:
            raise ValueError("Class not found.")

        if school_class.school_id != current_user.school_id:
            raise ValueError("Class does not belong to your school.")

        mapping = await self.teacher_class_repository.get(
            current_user.id,
            class_id,
        )

        if mapping is None:
            raise ValueError("Teacher is not assigned to this class.")

        if due_date <= datetime.now(timezone.utc):
            raise ValueError("Due date must be in the future.")

        assignment = Assignment(
            title=title,
            description=description,
            due_date=due_date,
            teacher_id=current_user.id,
            class_id=class_id,
        )

        try:

            assignment = await self.assignment_repository.create(
                assignment,
            )

            logger.info(
                "Assignment created",
                assignment_id=assignment.id,
            )

            return assignment

        except Exception:

            logger.exception(
                "Failed to create assignment",
                teacher_id=current_user.id,
            )

            raise

    async def get_assignments(
        self,
        current_user: User,
        class_id: uuid.UUID,
    ) -> list[Assignment]:
        school_class = await self.class_repository.get_by_id(
            class_id,
        )

        if school_class is None:
            raise ValueError("Class not found.")

        mapping = await self.teacher_class_repository.get(
            current_user.id,
            class_id,
        )

        if mapping is None:
            raise ValueError("Teacher is not assigned to this class.")

        return await self.assignment_repository.get_by_class(
            class_id,
        )
