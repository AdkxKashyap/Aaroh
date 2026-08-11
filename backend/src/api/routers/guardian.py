"""
Guardian APIs

Responsibility:
    Guardian relationship endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import get_current_user, require_role
from src.dependencies.services import get_guardian_service, get_user_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.guardian import CreateGuardianRequest, GuardianLinkResponse
from src.schemas.student import StudentResponse
from src.schemas.user import UserResponse
from src.services.guardian_service import GuardianService
from src.services.user_service import UserService

router = APIRouter(
    prefix="/guardians",
    tags=["Guardians"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_guardian(
    request: CreateGuardianRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
    guardian_service: Annotated[
        GuardianService,
        Depends(get_guardian_service),
    ],
):
    try:
        return await guardian_service.create_guardian(
            current_user=current_user,
            username=request.username,
            email=request.email,
            password=request.password,
            user_service=user_service,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{guardian_user_id}/students/{student_id}",
    response_model=GuardianLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def link_guardian_to_student(
    guardian_user_id: uuid.UUID,
    student_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    guardian_service: Annotated[
        GuardianService,
        Depends(get_guardian_service),
    ],
):
    try:
        return await guardian_service.link_guardian_to_student(
            guardian_user_id=guardian_user_id,
            student_id=student_id,
            current_user=current_user,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.get(
    "/students",
    response_model=list[StudentResponse],
)
async def get_linked_students(
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.GUARDIAN, RoleName.ADMIN)),
    ],
    guardian_service: Annotated[
        GuardianService,
        Depends(get_guardian_service),
    ],
):
    return await guardian_service.get_linked_students(current_user.id)
