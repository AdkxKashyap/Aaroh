"""
User Repository

Responsibility:
    Handles all database operations related to users.

Used By:
    UserService
"""

from unittest import result
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.user import User
from src.models.user_role import UserRole

logger = structlog.get_logger(__name__)


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        """
        Create a new user.
        """
        self.db.add(user)
        await self.db.flush()
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

    async def update(self, user: User) -> User:
        """
        Update an existing user.
        """
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id_with_roles(
        self,
        user_id: UUID,
    ) -> User | None:
        """
        Fetch user along with assigned roles.

        Used By:
            Authentication & Authorization

        Loads:
            User
                └── UserRole
                        └── Role
        """

        try:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.roles).selectinload(UserRole.role))
                .where(User.id == user_id)
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch user with roles",
                user_id=user_id,
            )
            raise

    async def get_by_school(self, school_id: UUID) -> list[User]:
        """
        Fetch all users belonging to a specific school.
        """

        try:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.roles).selectinload(UserRole.role))
                .where(User.school_id == school_id)
            )

            return list(result.scalars().all())

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch users by school",
                school_id=school_id,
            )
            raise
