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


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user: User) -> User:
        """
        Create a new user.
        """
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