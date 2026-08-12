from __future__ import annotations

import uuid

from src.schemas.chat import (
    ApprovalRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatRequest,
)
from src.enums.chat import ChatConversationStatus
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

    @staticmethod
    def _is_approval_message(message: str | None) -> bool:
        normalized = (message or "").strip().lower()
        return normalized in {"approve", "yes", "create it", "looks good"}

    @staticmethod
    def _response_from_workflow(conversation, workflow_response) -> ChatMessageResponse:
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

        if self._is_approval_message(request.message):
            if conversation.status == ChatConversationStatus.AWAITING_APPROVAL:
                workflow_response = await self.workflow_service.approve_action(
                    current_user=current_user,
                    request=ApprovalRequest(
                        intent=conversation.current_intent or "UNKNOWN",
                        approved=True,
                        action_payload=(
                            (conversation.workflow_data or {}).get("action_payload")
                            or {}
                        ),
                    ),
                )
                conversation = await self.conversation_service.persist_result(
                    conversation=conversation,
                    response=workflow_response,
                    message=request.message,
                    file_name=(conversation.workflow_data or {}).get("file_name"),
                    file_content=(conversation.workflow_data or {}).get(
                        "file_content"
                    ),
                )
                return self._response_from_workflow(conversation, workflow_response)

            if conversation.status == ChatConversationStatus.COMPLETED:
                return ChatMessageResponse(
                    conversation_id=conversation.id,
                    status=conversation.status.value,
                    message="This action has already been completed.",
                    intent=conversation.current_intent,
                    proposed_action=(
                        (conversation.workflow_data or {}).get("action_payload") or {}
                    ),
                    missing_fields=(
                        (conversation.workflow_data or {}).get("missing_fields") or []
                    ),
                    requires_approval=False,
                    approval_data=(
                        (conversation.workflow_data or {}).get("action_payload") or {}
                    ),
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

        return self._response_from_workflow(conversation, workflow_response)
