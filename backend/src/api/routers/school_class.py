import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import get_current_user, require_role
from src.core.logger import logger
from src.dependencies.services import get_school_class_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.school_class import CreateSchoolClassRequest, SchoolClassResponse
from src.services.school_class_service import SchoolClassService
from typing_extensions import Annotated

router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)


@router.post(
    "",
    response_model=SchoolClassResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_class(
    request: CreateSchoolClassRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    service: Annotated[
        SchoolClassService,
        Depends(get_school_class_service),
    ],
):
    try:
        return await service.create_class(
            current_user=current_user,
            name=request.name,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.get(
    "",
    response_model=list[SchoolClassResponse],
)
async def get_classes(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    service: Annotated[
        SchoolClassService,
        Depends(get_school_class_service),
    ],
):
    logger.info(
        "Fetching classes for school",
        school_id=current_user.school_id,
    )
    return await service.get_classes(
        current_user.school_id,
    )


@router.get(
    "/{teacher_id}",
    dependencies=[Depends(require_role(RoleName.ADMIN, RoleName.TEACHER))],
    response_model=list[SchoolClassResponse],
)
async def get_classes_by_teacher(
    teacher_id: uuid.UUID,
    service: Annotated[
        SchoolClassService,
        Depends(get_school_class_service),
    ],
):
    """
    Fetch all classes assigned to the current teacher.
    """

    return await service.get_class_by_teacher(
        teacher_id=teacher_id,
    )
