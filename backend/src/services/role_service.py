"""
Role Service

Responsibility:
    Handles role-related business logic.
"""

from src.models.role import Role
from src.repositories.role_repository import RoleRepository


class RoleService:

    def __init__(self, repository: RoleRepository):
        self.repository = repository

    async def create_role(self, role: Role) -> Role:
        return await self.repository.create(role)

    async def get_role(self, name: str) -> Role | None:
        return await self.repository.get_by_name(name)

    async def get_all_roles(self) -> list[Role]:
        return await self.repository.get_all()
