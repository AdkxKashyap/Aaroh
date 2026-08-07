"""
Role Repository

Responsibility:
    Handles all database operations related to roles.

Used By:
    RoleService
"""

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.role import Role
from src.models.user import User
from src.models.user_role import UserRole

logger = structlog.get_logger(__name__)


class RoleRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, role: Role) -> Role:
        """
        Create a new role.
        """
        try:
            self.db.add(role)

            await self.db.commit()
            await self.db.refresh(role)

            return role

        except SQLAlchemyError:
            logger.exception(
                "Failed to create role",
                role_name=role.name,
            )
            raise

    async def get_user_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> UserRole | None:
        """
        Fetch a user-role mapping.

        Used to prevent duplicate role assignments.
        """

        try:
            result = await self.db.execute(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                )
            )

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch user role",
                user_id=user_id,
                role_id=role_id,
            )
            raise

    async def get_all(self) -> list[Role]:
        """
        Fetch all roles.
        """
        try:
            result = await self.db.execute(select(Role))

            return list(result.scalars().all())

        except SQLAlchemyError:
            logger.exception("Failed to fetch roles")
            raise

    async def get_by_id(
        self,
        role_id: uuid.UUID,
    ) -> Role | None:
        """
        Fetch role by ID.
        """
        try:
            result = await self.db.execute(select(Role).where(Role.id == role_id))

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch role",
                role_id=role_id,
            )
            raise

    async def get_by_name(
        self,
        name: str,
    ) -> Role | None:
        """
        Fetch role by name.
        """
        try:
            result = await self.db.execute(select(Role).where(Role.name == name))

            return result.scalar_one_or_none()

        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch role",
                role_name=name,
            )
            raise

    async def assign_role(
        self,
        user: User,
        role: Role,
    ) -> UserRole:
        """
        Assign a role to a user.
        """

        try:

            user_role = UserRole(
                user_id=user.id,
                role_id=role.id,
            )

            self.db.add(user_role)

            await self.db.commit()
            await self.db.refresh(user_role)

            return user_role

        except SQLAlchemyError:
            logger.exception(
                "Failed to assign role",
                user_id=user.id,
                role_id=role.id,
            )
            raise
