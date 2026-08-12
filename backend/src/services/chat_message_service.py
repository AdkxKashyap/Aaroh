from __future__ import annotations

import uuid

from src.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatRequest
from src.services.chat_conversation_service import ChatConversationService
from src.services.chat_workflow import ChatWorkflowService
from src.services.extraction_adapter import ExtractionAdapter


class ChatMessageService:
    def __init__(
        self,
        workflow_service: ChatWorkflowService,
        conversation_service: ChatConversationService,
    ):
        self.workflow_service = workflow_service
        self.conversation_service = conversation_service

    async def handle_message(
        self,
        current_user,
        request: ChatMessageRequest,
        file=None,
    ) -> ChatMessageResponse:
        conversation = await self.conversation_service.get_or_create(
            current_user=current_user,
            conversation_id=request.conversation_id,
        )

        extracted_file_text = request.file_content
        file_name = request.file_name

        if file is not None:
            file_bytes = await file.read()
            file_name = file.filename
            extracted_file_text = ExtractionAdapter.extract_text(
                file_bytes, file.filename
            )

        conversation_context = self.conversation_service.build_context(conversation)

        await self.conversation_service.mark_processing(conversation, request.message)

        workflow_response = await self.workflow_service.process_message(
            current_user=current_user,
            request=ChatRequest(
                message=request.message or "",
                file_name=file_name,
                file_content=extracted_file_text,
                session_id=str(conversation.id),
            ),
            conversation_context=conversation_context,
        )

        conversation = await self.conversation_service.persist_result(
            conversation=conversation,
            response=workflow_response,
            message=request.message,
            file_name=file_name,
            file_content=extracted_file_text,
        )

        return ChatMessageResponse(
            conversation_id=conversation.id,
            status=conversation.status.value,
            message=workflow_response.message,
            intent=workflow_response.intent,
            proposed_action=(workflow_response.action_payload or {}),
            missing_fields=list(workflow_response.missing_fields or []),
            clarification_question=(
                workflow_response.clarification_questions[0]
                if workflow_response.clarification_questions
                else None
            ),
            requires_approval=workflow_response.requires_approval,
            approval_data=(workflow_response.action_payload or {}),
        )
