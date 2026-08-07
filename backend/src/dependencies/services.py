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

from typing import Annotated

from fastapi import Depends
from src.dependencies.database import DbSession
from src.repositories.role_repository import RoleRepository
from src.repositories.school_class_repository import SchoolClassRepository
from src.repositories.school_repository import SchoolRepository
from src.repositories.user_repository import UserRepository
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
    role_repository: Annotated[
        RoleRepository,
        Depends(get_role_repository),
    ],
    user_repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> RoleService:
    return RoleService(role_repository, user_repository)


def get_auth_service(
    repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> AuthService:
    return AuthService(repository)


def get_school_repository(
    db: DbSession,
) -> SchoolRepository:
    """
    Creates SchoolRepository.
    """

    return SchoolRepository(db)


def get_school_class_repository(
    db: DbSession,
) -> SchoolClassRepository:
    """
    Creates SchoolClassRepository.
    """

    return SchoolClassRepository(db)
