"""
User Service

Responsibility:
    Handles user-related business logic.

Used By:
    User APIs
"""

from uuid import UUID

from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.core.security import hash_password
from src.models.user import User


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register_user(
    self,
    username: str,
    email: str,
    password: str,
) -> User:
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

    async def get_by_username(self, username: str) -> User | None:
        return await self.repository.get_by_username(username)

    async def get_all_users(self) -> list[User]:
        return await self.repository.get_all()

    async def delete_user(self, user: User) -> None:
        await self.repository.delete(user)
