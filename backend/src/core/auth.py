"""
Authentication Dependencies

Responsibility:
    Extract and validate authenticated user.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.core.logger import logger
from src.core.security import decode_access_token
from src.dependencies.services import get_user_service
from src.models.user import User
from src.services.user_service import UserService
from typing_extensions import Annotated

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

    user = await user_service.get_user_with_roles(UUID(payload["sub"]))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


def require_role(
    *role_names: str,
):
    """
    Authorization dependency.

    Ensures current user has at least one of the required roles.
    """

    if len(role_names) == 1 and isinstance(role_names[0], (list, tuple, set)):
        role_names = tuple(role_names[0])

    required_roles = set(role_names)

    async def dependency(
        current_user: Annotated[
            User,
            Depends(get_current_user),
        ],
    ):

        for user_role in current_user.roles:
            if user_role.role.name in required_roles:
                return current_user

        logger.warning(
            "Authorization failed",
            user_id=current_user.id,
            required_roles=required_roles,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return dependency
