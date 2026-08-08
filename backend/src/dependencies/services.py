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
from src.services.assignment_service import AssignmentService
from src.repositories.assignment_repository import AssignmentRepository
from src.dependencies.database import DbSession
from src.repositories.role_repository import RoleRepository
from src.repositories.school_class_repository import SchoolClassRepository
from src.repositories.school_repository import SchoolRepository
from src.repositories.teacher_class_repository import TeacherClassRepository
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.role_service import RoleService
from src.services.school_class_service import SchoolClassService
from src.services.school_service import SchoolService
from src.services.teacher_service import TeacherService
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


def get_school_service(
    school_repository: Annotated[
        SchoolRepository,
        Depends(get_school_repository),
    ],
    user_repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> SchoolService:
    """
    Creates SchoolService.
    """

    return SchoolService(school_repository, user_repository)


def get_school_class_service(
    class_repository: Annotated[
        SchoolClassRepository,
        Depends(get_school_class_repository),
    ],
    school_repository: Annotated[
        SchoolRepository,
        Depends(get_school_repository),
    ],
) -> SchoolClassService:
    """
    Creates SchoolClassService.
    """

    return SchoolClassService(
        class_repository=class_repository,
        school_repository=school_repository,
    )


def get_teacher_class_repository(
    db: DbSession,
) -> TeacherClassRepository:
    """
    Creates TeacherClassRepository.
    """

    return TeacherClassRepository(db)


def get_teacher_service(
    teacher_class_repository: Annotated[
        TeacherClassRepository,
        Depends(get_teacher_class_repository),
    ],
    class_repository: Annotated[
        SchoolClassRepository,
        Depends(get_school_class_repository),
    ],
    user_repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
    role_repository: Annotated[
        RoleRepository,
        Depends(get_role_repository),
    ],
) -> TeacherService:
    """
    Creates TeacherService.
    """

    return TeacherService(
        user_service=user_service,
        user_repository=user_repository,
        role_repository=role_repository,
        class_repository=class_repository,
        teacher_class_repository=teacher_class_repository,
    )

def get_assignment_repository(
    db: DbSession,
) -> AssignmentRepository:
    """
    Creates AssignmentRepository.
    """

    return AssignmentRepository(db)
def get_assignment_service(
    assignment_repository: Annotated[
        AssignmentRepository,
        Depends(get_assignment_repository),
    ],
    class_repository: Annotated[
        SchoolClassRepository,
        Depends(get_school_class_repository),
    ],
    teacher_class_repository: Annotated[
        TeacherClassRepository,
        Depends(get_teacher_class_repository),
    ],
) -> AssignmentService:

    return AssignmentService(
        assignment_repository=assignment_repository,
        class_repository=class_repository,
        teacher_class_repository=teacher_class_repository,
    )