"""
Role Repository

Responsibility:
    Handles database operations for roles.

Used By:
    RoleService
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.role import Role


class RoleRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, role: Role) -> Role:
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Role]:
        result = await self.db.execute(select(Role))
        return list(result.scalars().all())