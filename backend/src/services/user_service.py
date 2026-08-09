"""
User Service

Responsibility:
    Handles user-related business logic.

Used By:
    User APIs
"""

from uuid import UUID

from src.core.logger import logger
from src.core.security import hash_password
from src.db.transaction import transactional
from src.models.user import User
from src.repositories.user_repository import UserRepository


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
    ) -> User:
        async with transactional(self.repository.db):
            existing_user = await self.repository.get_by_username(username)

            if existing_user:
                raise ValueError("Username already exists.")

            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
            )

            return await self.repository.create(user)

    async def get_user(self, user_id: UUID) -> User | None:
        """
        Get user by ID.
        """
        return await self.repository.get_by_id(user_id)

    async def get_user_with_roles(
        self,
        user_id: UUID,
    ) -> User | None:
        """
        Fetch user along with assigned roles.
        """

        return await self.repository.get_by_id_with_roles(user_id)

    async def get_by_username(self, username: str) -> User | None:
        return await self.repository.get_by_username(username)

    async def get_all_users(self) -> list[User]:
        return await self.repository.get_all()

    async def delete_user(self, user: User) -> None:
        async with transactional(self.repository.db):
            await self.repository.delete(user)

    async def update_user(
        self,
        user_id: UUID,
        email: str,
        is_active: bool,
    ) -> User | None:
        async with transactional(self.repository.db):
            user = await self.repository.get_by_id(user_id)

            if user is None:
                logger.warning("User not found", user_id=user_id)
                return None

            user.email = email
            user.is_active = is_active

            logger.info("Updating user", user_id=user.id)

            return await self.repository.update(user)
