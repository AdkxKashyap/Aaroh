"""
Document APIs

Responsibility:
    Document lifecycle endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from src.core.auth import require_role
from src.dependencies.services import get_document_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.document import DocumentResponse, DocumentVersionResponse
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
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.ADMIN, RoleName.TEACHER)),
    ],
    document_service: Annotated[
        DocumentService,
        Depends(get_document_service),
    ],
    document_type: str = Form(default="upload"),
    file: UploadFile | None = File(default=None),
    class_id: uuid.UUID | None = Form(default=None),
):

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file upload is required.",
        )

    try:
        return await document_service.create_document(
            school_id=current_user.school_id,
            uploaded_by=current_user.id,
            document_type=document_type,
            file=file,
            current_user=current_user,
            class_id=class_id,
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
    document = await document_service.get_document(document_id, current_user)
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
        return await document_service.get_versions(document_id, current_user)
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ex),
        )


@router.post(
    "/{document_id}/parse",
    response_model=DocumentResponse,
)
async def begin_document_parsing(
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
        return await document_service.begin_parsing(document_id, current_user)
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )
