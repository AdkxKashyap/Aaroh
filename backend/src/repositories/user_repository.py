"""
User Repository

Responsibility:
    Handles all database operations related to users.

Used By:
    UserService
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        """
        Create a new user.
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Fetch user by ID.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """
        Fetch user by username.
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Fetch user by email.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[User]:
        """
        Fetch all users.
        """
        result = await self.db.execute(select(User))
        return list(result.scalars().all())

    async def delete(self, user: User) -> None:
        """
        Delete a user.
        """
        await self.db.delete(user)
        await self.db.commit()

    async def update(self, user: User) -> User:
        """
        Update an existing user.
        """
        await self.db.commit()
        await self.db.refresh(user)
        return user
