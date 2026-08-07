"""
User APIs

Responsibility:
    Handles user registration.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies.services import get_user_service
from src.schemas.user import (
    UserRegistrationRequest,
    UserResponse,
)
from src.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: UserRegistrationRequest,
    service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    """
    Register a new user.
    """

    try:
        return await service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )
