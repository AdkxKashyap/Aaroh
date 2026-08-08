"""
Teacher APIs

Responsibility:
    Teacher management endpoints.

Only School Admins can:
    - Invite teachers
    - View teachers
    - Assign teachers to classes
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import require_role
from src.dependencies.services import get_teacher_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.teacher import AssignTeacherRequest, InviteTeacherRequest
from src.schemas.user import UserResponse
from src.services.teacher_service import TeacherService

router = APIRouter(
    prefix="/teachers",
    tags=["Teachers"],
)


@router.post(
    "/invite",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_teacher(
    request: InviteTeacherRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    teacher_service: Annotated[
        TeacherService,
        Depends(get_teacher_service),
    ],
):
    """
    Invite a teacher to the current admin's school.
    """

    try:
        return await teacher_service.invite_teacher(
            current_user=current_user,
            request=request,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.get(
    "",
    response_model=list[UserResponse],
)
async def get_teachers(
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    teacher_service: Annotated[
        TeacherService,
        Depends(get_teacher_service),
    ],
):
    """
    Returns all teachers
    belonging to the current admin's school.
    """

    return await teacher_service.get_teachers(
        current_user=current_user,
    )

@router.post(
"/{teacher_id}/classes",
status_code=status.HTTP_200_OK,
)
async def assign_teacher(
    teacher_id: uuid.UUID,
    request: AssignTeacherRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    teacher_service: Annotated[
        TeacherService,
        Depends(get_teacher_service),
    ],
):
    """
    Assign a teacher to a class.
    """

    try:

        await teacher_service.assign_teacher(
            current_user=current_user,
            teacher_id=teacher_id,
            class_id=request.class_id,
        )

        return {
            "message": "Teacher assigned successfully."
        }

    except ValueError as ex:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )