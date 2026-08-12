from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import get_current_user
from src.models.user import User
from src.schemas.chat import ChatRequest, ChatResponse
from src.services.chat_workflow import ChatWorkflowService
from src.services.llm_provider import LLMClientFactory

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_chat_workflow_service() -> ChatWorkflowService:
    llm_provider = LLMClientFactory.create("ollama")
    return ChatWorkflowService(llm_provider)


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
