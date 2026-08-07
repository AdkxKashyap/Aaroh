from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies.services import get_auth_service
from src.schemas.auth import LoginRequest, TokenResponse
from src.services.auth_service import AuthService
from src.core.auth import get_current_user
from src.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
    service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
):
    """
    Authenticate user.
    """

    token = await service.authenticate(
        request.username,
        request.password,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


@router.get("/me")
async def me(
    user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }
