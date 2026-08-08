"""
Student APIs

Responsibility:
    Student management endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import get_current_user, require_role
from src.dependencies.services import get_student_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.student import (
    CreateStudentRequest,
    StudentResponse,
)
from src.services.student_service import StudentService

router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_student(
    request: CreateStudentRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    student_service: Annotated[
        StudentService,
        Depends(get_student_service),
    ],
):
    """
    Create a student in the current admin's school.
    """

    try:
        return await student_service.create_student(
            current_user=current_user,
            username=request.username,
            email=request.email,
            password=request.password,
            class_id=request.class_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.get(
    "/class/{class_id}",
    response_model=list[StudentResponse],
)
async def get_students(
    class_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    student_service: Annotated[
        StudentService,
        Depends(get_student_service),
    ],
):
    """
    Get students belonging to a class
    in the current admin's school.
    """

    try:
        return await student_service.get_students(
            current_user=current_user,
            class_id=class_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.get(
    "/me",
    response_model=StudentResponse,
)
async def get_current_student(
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.STUDENT)),
    ],
    student_service: Annotated[
        StudentService,
        Depends(get_student_service),
    ],
):
    """
    Get the student profile for the
    authenticated student.
    """

    try:
        student = await student_service.get_by_user_id(
            current_user.id,
        )

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found.",
            )

        return student

    except HTTPException:
        raise

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )
