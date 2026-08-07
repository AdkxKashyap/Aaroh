"""
Service Dependencies

Responsibility:
    Central place for creating and injecting services.
"""

"""
Repository Dependencies

Responsibility:
    Creates repository instances.
"""

from fastapi import Depends

from src.dependencies.database import DbSession
from src.repositories.role_repository import RoleRepository
from src.repositories.user_repository import UserRepository


def get_user_repository(
    db: DbSession,
) -> UserRepository:
    return UserRepository(db)


def get_role_repository(
    db: DbSession,
) -> RoleRepository:
    return RoleRepository(db)
