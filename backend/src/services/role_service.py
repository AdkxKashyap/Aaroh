"""
Role Service

Responsibility:
    Handles business logic related to roles.
"""

import uuid

from src.core.logger import logger
from src.models.role import Role
from src.models.user_role import UserRole
from src.repositories.role_repository import RoleRepository
from src.repositories.user_repository import UserRepository


class RoleService:

    def __init__(
        self,
        role_repository: RoleRepository,
        user_repository: UserRepository,
    ):
        self.role_repository = role_repository
        self.user_repository = user_repository

    async def create_role(
        self,
        name: str,
        description: str | None,
    ) -> Role:
        """
        Create a new role.
        """

        logger.info(
            "Creating role",
            role_name=name,
        )

        existing_role = await self.role_repository.get_by_name(name)

        if existing_role:
            raise ValueError("Role already exists.")

        role = Role(
            name=name,
            description=description,
        )

        role = await self.role_repository.create(role)

        logger.info(
            "Role created successfully",
            role_id=role.id,
        )

        return role

    async def get_roles(
        self,
    ) -> list[Role]:
        """
        Fetch all roles.
        """

        logger.info(
            "Fetching all roles",
        )

        return await self.role_repository.get_all()

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> UserRole:
        """
        Assign role to user.
        """

        logger.info(
            "Assigning role",
            user_id=user_id,
            role_id=role_id,
        )

        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        role = await self.role_repository.get_by_id(role_id)

        if role is None:
            raise ValueError("Role not found.")
        existing_user_role = await self.role_repository.get_user_role(
            user_id=user_id,
            role_id=role_id,
        )

        if existing_user_role:
            logger.warning(
                "Role already assigned",
                user_id=user_id,
                role_id=role_id,
            )

            raise ValueError("Role already assigned.")
        return await self.role_repository.assign_role(
            user,
            role,
        )
