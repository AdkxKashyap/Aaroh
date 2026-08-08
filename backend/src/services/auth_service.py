"""
Authentication Service

Responsibility:
    Handles user authentication.
"""

from src.core.logger import logger

from src.core.security import create_access_token, verify_password
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
        Authenticate user and return JWT.
        """

        logger.info(
            "User login started",
            username=username,
        )

        user = await self.repository.get_by_username(username)

        if not user:
            logger.warning(
                "User not found",
                username=username,
            )
            return None

        if not verify_password(password, user.password_hash):
            logger.warning(
                "Invalid password",
                username=username,
            )
            return None

        logger.info(
            "User login successful",
            user_id=user.id,
        )

        return create_access_token(str(user.id))
