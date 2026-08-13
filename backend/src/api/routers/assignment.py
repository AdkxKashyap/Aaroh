"""
Assignment APIs

Responsibility:
    Assignment creation and retrieval.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import require_role
from src.dependencies.services import get_assignment_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.assignment import (
    AssignmentResponse,
    CreateAssignmentRequest,
)
from src.services.assignment_service import AssignmentService

router = APIRouter(
    prefix="/assignments",
    tags=["Assignments"],
)


@router.post(
    "",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    request: CreateAssignmentRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
):
    """
    Create an assignment for a class
    assigned to the current teacher.
    """

    try:
        return await assignment_service.create_assignment(
            current_user=current_user,
            title=request.title,
            description=request.description,
            due_date=request.due_date,
            class_id=request.class_id or None,
            class_name=request.class_name or None,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.get(
    "/class/{class_id}",
    response_model=list[AssignmentResponse],
)
async def get_assignments(
    class_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
):
    """
    Get assignments for a class
    assigned to the current teacher.
    """

    try:
        return await assignment_service.get_assignments(
            current_user=current_user,
            class_id=class_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{assignment_id}/submit-review",
    response_model=AssignmentResponse,
)
async def submit_assignment_for_review(
    assignment_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
):
    try:
        return await assignment_service.submit_for_review(
            current_user=current_user,
            assignment_id=assignment_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{assignment_id}/approve",
    response_model=AssignmentResponse,
)
async def approve_assignment(
    assignment_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
):
    try:
        return await assignment_service.approve(
            current_user=current_user,
            assignment_id=assignment_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{assignment_id}/activate",
    response_model=AssignmentResponse,
)
async def activate_assignment(
    assignment_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
):
    try:
        return await assignment_service.activate(
            current_user=current_user,
            assignment_id=assignment_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{assignment_id}/complete",
    response_model=AssignmentResponse,
)
async def complete_assignment(
    assignment_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
):
    try:
        return await assignment_service.complete(
            current_user=current_user,
            assignment_id=assignment_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{assignment_id}/cancel",
    response_model=AssignmentResponse,
)
async def cancel_assignment(
    assignment_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
):
    try:
        return await assignment_service.cancel(
            current_user=current_user,
            assignment_id=assignment_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )
