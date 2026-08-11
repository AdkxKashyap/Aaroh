"""
Document APIs

Responsibility:
    Document lifecycle endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import get_current_user, require_role
from src.dependencies.services import get_document_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.document import (
    CreateDocumentRequest,
    DocumentResponse,
    DocumentVersionResponse,
)
from src.services.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    request: CreateDocumentRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN, RoleName.TEACHER)),
    ],
    document_service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    try:
        return await document_service.create_document(
            school_id=current_user.school_id,
            uploaded_by=current_user.id,
            document_type=request.document_type,
            content_hash=request.content_hash,
            storage_key=request.storage_key,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(
            require_role(
                RoleName.ADMIN,
                RoleName.TEACHER,
            )
        ),
    ],
    document_service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    document = await document_service.get_document(current_user, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return document


@router.get(
    "/{document_id}/versions",
    response_model=list[DocumentVersionResponse],
)
async def get_document_versions(
    document_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN, RoleName.TEACHER)),
    ],
    document_service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
):
    try:
        return await document_service.get_versions(current_user, document_id)
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ex),
        )
