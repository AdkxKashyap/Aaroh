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
from typing import Annotated
from src.services.auth_service import AuthService
from src.services.role_service import RoleService
from src.services.user_service import UserService


def get_user_repository(
    db: DbSession,
) -> UserRepository:
    return UserRepository(db)


def get_role_repository(
    db: DbSession,
) -> RoleRepository:
    return RoleRepository(db)


def get_user_service(
    repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> UserService:
    return UserService(repository)


def get_role_service(
    repository: Annotated[
        RoleRepository,
        Depends(get_role_repository),
    ],
) -> RoleService:
    return RoleService(repository)


def get_auth_service(
    repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> AuthService:
    return AuthService(repository)
