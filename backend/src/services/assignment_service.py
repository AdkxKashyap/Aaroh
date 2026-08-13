import uuid
from datetime import datetime, timezone

from src.core.logger import logger
from src.db.transaction import transactional
from src.enums.assignment import AssignmentStatus
from src.models.assignment import Assignment
from src.models.user import User
from src.repositories.assignment_repository import AssignmentRepository
from src.repositories.school_class_repository import SchoolClassRepository
from src.repositories.teacher_class_repository import TeacherClassRepository
from src.schemas.assignment import AssignmentResponse
from src.utils.class_name import normalize_class_name

"""
Assignment Service

Responsibility:
    Handles assignment management.
"""

"""
This dictionary defines the allowed state transitions for assignments.
The keys are the current states, and the values are sets of states to which the assignment can transition. This is used to enforce the assignment state machine.
"""
ALLOWED_ASSIGNMENT_TRANSITIONS = {
    AssignmentStatus.DRAFT: {
        AssignmentStatus.REVIEW_REQUIRED,
    },
    AssignmentStatus.REVIEW_REQUIRED: {
        AssignmentStatus.APPROVED,
    },
    AssignmentStatus.APPROVED: {
        AssignmentStatus.ACTIVE,
    },
    AssignmentStatus.ACTIVE: {
        AssignmentStatus.COMPLETED,
        AssignmentStatus.CANCELLED,
    },
    AssignmentStatus.COMPLETED: set(),
    AssignmentStatus.CANCELLED: set(),
}


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

    def _to_response(self, assignment: Assignment) -> AssignmentResponse:
        return AssignmentResponse(
            id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            due_date=assignment.due_date,
            teacher_id=assignment.teacher_id,
            class_id=assignment.class_id,
            status=assignment.status,
            teacher_name=assignment.teacher.username if assignment.teacher else None,
            class_name=(
                assignment.school_class.name if assignment.school_class else None
            ),
        )

    async def create_assignment(
        self,
        current_user: User,
        title: str,
        description: str,
        due_date: datetime,
        class_id: uuid.UUID | None = None,
        class_name: str | None = None,
    ) -> AssignmentResponse:
        """
        Creates an assignment.
        """

        if class_id is None:
            if not class_name:
                raise ValueError("Class ID or class name is required.")

            normalized_name = normalize_class_name(class_name)
            school_class = await self.class_repository.get_by_name(
                current_user.school_id,
                normalized_name,
            )
            if school_class is None:
                raise ValueError("Class not found.")
            class_id = school_class.id
        else:
            school_class = await self.class_repository.get_by_id(class_id)
            if school_class is None:
                raise ValueError("Class not found.")

        if school_class.school_id != current_user.school_id:
            raise ValueError("Class does not belong to your school.")

        logger.info(
            "Creating assignment",
            teacher_id=current_user.id,
            class_id=class_id,
        )

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
            async with transactional(self.assignment_repository.db):
                assignment = await self.assignment_repository.create(
                    assignment,
                )

                logger.info(
                    "Assignment created",
                    assignment_id=assignment.id,
                )

                return self._to_response(assignment)

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
    ) -> list[AssignmentResponse]:
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

        assignments = await self.assignment_repository.get_by_class(
            class_id,
        )

        return [self._to_response(assignment) for assignment in assignments]

    async def transition_status(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
        new_status: AssignmentStatus,
    ) -> AssignmentResponse:
        """
        Transition an assignment to a valid next state.
        """

        logger.info(
            "Transitioning assignment",
            assignment_id=assignment_id,
            user_id=current_user.id,
            target_status=new_status,
        )

        assignment = await self.assignment_repository.get_by_id(
            assignment_id,
        )

        if assignment is None:
            raise ValueError("Assignment not found.")

        # Assignment ownership
        if assignment.teacher_id != current_user.id:
            raise ValueError("You do not own this assignment.")

        allowed_states = ALLOWED_ASSIGNMENT_TRANSITIONS[assignment.status]

        if new_status not in allowed_states:
            logger.warning(
                "Invalid assignment state transition",
                assignment_id=assignment.id,
                current_status=assignment.status,
                target_status=new_status,
            )

            raise ValueError(
                f"Invalid transition from " f"{assignment.status} to {new_status}."
            )

        old_status = assignment.status
        assignment.status = new_status

        try:
            async with transactional(self.assignment_repository.db):
                assignment = await self.assignment_repository.update(
                    assignment,
                )

                logger.info(
                    "Assignment status transitioned",
                    assignment_id=assignment.id,
                    old_status=old_status,
                    new_status=new_status,
                )

                return assignment

        except Exception:
            logger.exception(
                "Failed to transition assignment",
                assignment_id=assignment.id,
                old_status=old_status,
                new_status=new_status,
            )
            raise

    async def submit_for_review(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> AssignmentResponse:

        return await self.transition_status(
            current_user=current_user,
            assignment_id=assignment_id,
            new_status=AssignmentStatus.REVIEW_REQUIRED,
        )

    async def approve(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> AssignmentResponse:

        return await self.transition_status(
            current_user=current_user,
            assignment_id=assignment_id,
            new_status=AssignmentStatus.APPROVED,
        )

    async def activate(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> AssignmentResponse:

        return await self.transition_status(
            current_user=current_user,
            assignment_id=assignment_id,
            new_status=AssignmentStatus.ACTIVE,
        )

    async def complete(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> AssignmentResponse:

        return await self.transition_status(
            current_user=current_user,
            assignment_id=assignment_id,
            new_status=AssignmentStatus.COMPLETED,
        )

    async def cancel(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> AssignmentResponse:

        return await self.transition_status(
            current_user=current_user,
            assignment_id=assignment_id,
            new_status=AssignmentStatus.CANCELLED,
        )
