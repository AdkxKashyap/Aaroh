from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from src.core.auth import get_current_user
from src.dependencies.services import (
    get_chat_message_service,
    get_chat_workflow_service,
)
from src.models.user import User
from src.schemas.chat import (
    ApprovalRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
)
from src.services.chat_message_service import ChatMessageService
from src.services.chat_workflow import ChatWorkflowService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def chat_message(
    request: ChatMessageRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    message_service: Annotated[
        ChatMessageService,
        Depends(get_chat_message_service),
    ],
    file: UploadFile | None = File(default=None),
):
    if not request.message and file is None and not request.file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either message or file is required.",
        )

    try:
        return await message_service.handle_message(current_user, request, file=file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def chat(
    request: ChatRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    workflow_service: Annotated[
        ChatWorkflowService,
        Depends(get_chat_workflow_service),
    ],
):
    try:
        return await workflow_service.process_message(current_user, request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/approve",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_action(
    request: ApprovalRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    workflow_service: Annotated[
        ChatWorkflowService,
        Depends(get_chat_workflow_service),
    ],
):
    try:
        return await workflow_service.approve_action(current_user, request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
