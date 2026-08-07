"""
Authentication Dependencies

Responsibility:
    Extract and validate authenticated user.
"""

from typing import Annotated

from typing_extensions import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.core.security import decode_access_token
from src.dependencies.services import get_user_service
from src.services.user_service import UserService
from uuid import UUID
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = await user_service.get_user(UUID(payload["sub"]))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user
