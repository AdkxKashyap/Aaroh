"""
Role APIs

Responsibility:
    Role management.
"""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies.services import get_role_service
from src.schemas.role import (
    AssignRoleRequest,
    CreateRoleRequest,
    RoleResponse,
)
from src.services.role_service import RoleService

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    request: CreateRoleRequest,
    service: Annotated[
        RoleService,
        Depends(get_role_service),
    ],
):
    try:
        return await service.create_role(
            request.name,
            request.description,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=400,
            detail=str(ex),
        )


@router.get(
    "",
    response_model=list[RoleResponse],
)
async def get_roles(
    service: Annotated[
        RoleService,
        Depends(get_role_service),
    ],
):
    return await service.get_roles()


@router.post(
    "/users/{user_id}",
)
async def assign_role(
    user_id: uuid.UUID,
    request: AssignRoleRequest,
    service: Annotated[
        RoleService,
        Depends(get_role_service),
    ],
):
    try:
        await service.assign_role(
            user_id,
            request.role_id,
        )

        return {"message": "Role assigned successfully."}

    except ValueError as ex:
        raise HTTPException(
            status_code=400,
            detail=str(ex),
        )
