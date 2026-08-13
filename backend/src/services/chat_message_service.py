from __future__ import annotations

from src.core.logger import logger
from src.schemas.chat import (
    ChatMessageRequest,
    ChatRequest,
    ChatResponse,
)
from src.services.chat_workflow import ChatWorkflowService
from src.services.extraction_adapter import ExtractionAdapter
from src.services.intent import IntentFactory


class ChatMessageService:
    def __init__(
        self,
        workflow_service: ChatWorkflowService,
        intent_factory: IntentFactory,
    ):
        self.workflow_service = workflow_service
        self.intent_factory = intent_factory

    async def handle_message(
        self,
        current_user,
        request: ChatMessageRequest,
        file=None,
    ) -> ChatResponse:
        extracted_file_text = ""
        file_name = ""

        if file is not None:
            file_bytes = await file.read()
            file_name = file.filename
            extracted_file_text = ExtractionAdapter.extract_text(
                file_bytes, file.filename
            )
        logger.info(
            "Processing chat message",
            user_id=getattr(current_user, "id", None),
            school_id=getattr(current_user, "school_id", None),
            file_name=file_name,
            extracted_file_text=extracted_file_text,
        )
        workflow_response = await self.workflow_service.process_message(
            current_user=current_user,
            request=ChatRequest(
                message=request.message or "",
                file_name=file_name,
                file_content=extracted_file_text,
                session_id="",
            ),
            intent_factory=self.intent_factory,
        )
        return workflow_response
