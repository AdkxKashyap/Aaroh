"""
User APIs

Responsibility:
    Handles user registration.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from src.core.auth import get_current_user
from src.dependencies.services import get_user_service
from src.schemas.user import (
    UserRegistrationRequest,
    UserResponse,
    UserUpdateRequest,
    UserUpdateRequest,
)
from src.services.user_service import UserService
from src.models.user import User

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


@router.get(
    "", dependencies=[Depends(get_current_user)], response_model=list[UserResponse]
)
async def get_users(
    service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    return await service.get_all_users()


@router.get(
    "/{user_id}", dependencies=[Depends(get_current_user)], response_model=UserResponse
)
async def get_user(
    user_id: UUID,
    service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    user = await service.get_user(user_id)

    if user is None:
        raise HTTPException(404, "User not found")

    return user


@router.put(
    "/{user_id}", dependencies=[Depends(get_current_user)], response_model=UserResponse
)
async def update_user(
    user_id: UUID,
    request: UserUpdateRequest,
    service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    user = await service.update_user(
        user_id,
        request.email,
        request.is_active,
    )

    if user is None:
        raise HTTPException(404, "User not found")

    return user


@router.delete(
    "/{user_id}", dependencies=[Depends(get_current_user)], status_code=204
)
async def delete_user(
    user_id: UUID,
    service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    user = await service.get_user(user_id)

    if user is None:
        raise HTTPException(404, "User not found")

    await service.delete_user(user)
