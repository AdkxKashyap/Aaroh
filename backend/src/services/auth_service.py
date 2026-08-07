"""
Authentication Service

Responsibility:
    Handles authentication business logic.
"""

from src.core.security import (
    create_access_token,
    verify_password,
)
from src.repositories.user_repository import UserRepository


class AuthService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def authenticate(
        self,
        username: str,
        password: str,
    ) -> str | None:
        """
        Authenticate user and return JWT token.
        """

        user = await self.repository.get_by_username(username)

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return create_access_token(user.username)