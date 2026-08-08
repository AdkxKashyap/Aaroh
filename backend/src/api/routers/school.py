from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import require_role
from src.dependencies.services import get_school_service
from src.models.user import User
from src.schemas.school import SchoolRegistrationRequest, SchoolResponse
from typing_extensions import Annotated

from src.enums.role import RoleName
from src.schemas.school import SchoolResponse
from src.services.school_service import SchoolService

router = APIRouter(
    prefix="/schools",
    tags=["Schools"],
)


@router.post(
    "/register",
    response_model=SchoolResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_school(
    request: SchoolRegistrationRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN)),
    ],
    service: Annotated[
        SchoolService,
        Depends(get_school_service),
    ],
):
    try:
        return await service.register_school(
            current_user=current_user,
            name=request.name,
            address=request.address,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )
