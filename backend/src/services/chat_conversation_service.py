import uuid
from typing import Any

from src.db.transaction import transactional
from src.enums.chat import ChatConversationStatus
from src.models.chat_conversation import ChatConversation
from src.repositories.chat_conversation_repository import ChatConversationRepository


class ChatConversationService:
    def __init__(
        self,
        repository: ChatConversationRepository,
    ):
        self.repository = repository

    async def get_or_create(
        self,
        current_user,
        conversation_id: uuid.UUID | None,
    ) -> ChatConversation:
        if conversation_id is not None:
            conversation = await self.repository.get_by_id(conversation_id)
            if conversation is None:
                raise ValueError("Conversation not found.")
            if conversation.user_id != current_user.id:
                raise ValueError("Access denied to this conversation.")
            if conversation.school_id != current_user.school_id:
                raise ValueError("Conversation does not belong to your school.")
            return conversation

        conversation = ChatConversation(
            user_id=current_user.id,
            school_id=current_user.school_id,
            status=ChatConversationStatus.NEW,
            workflow_data={},
        )
        async with transactional(self.repository.db):
            return await self.repository.create(conversation)

    async def mark_processing(
        self,
        conversation: ChatConversation,
        message: str | None,
    ) -> ChatConversation:
        conversation.status = ChatConversationStatus.PROCESSING
        conversation.last_user_message = message
        async with transactional(self.repository.db):
            return await self.repository.update(conversation)

    async def persist_result(
        self,
        conversation: ChatConversation,
        response,
        message: str | None,
        file_name: str | None,
        file_content: str | None,
    ) -> ChatConversation:
        conversation.current_intent = response.intent
        conversation.last_user_message = message
        conversation.last_assistant_message = response.message
        conversation.status = self._map_response_status(response.status)
        conversation.workflow_data = {
            "action_payload": response.action_payload,
            "clarification_questions": list(response.clarification_questions or []),
            "requires_approval": response.requires_approval,
            "file_name": file_name,
            "file_content": file_content,
        }
        async with transactional(self.repository.db):
            return await self.repository.update(conversation)

    def _map_response_status(self, status: str) -> ChatConversationStatus:
        mapping = {
            "clarification_required": ChatConversationStatus.CLARIFICATION_REQUIRED,
            "awaiting_approval": ChatConversationStatus.AWAITING_APPROVAL,
            "executed": ChatConversationStatus.COMPLETED,
            "rejected": ChatConversationStatus.REJECTED,
            "blocked": ChatConversationStatus.REJECTED,
            "needs_input": ChatConversationStatus.FAILED,
        }
        return mapping.get(status, ChatConversationStatus.FAILED)

    def build_context(self, conversation: ChatConversation) -> dict[str, Any]:
        return {
            "conversation_id": conversation.id,
            "status": conversation.status.value,
            "intent": conversation.current_intent,
            "workflow_data": conversation.workflow_data or {},
            "last_user_message": conversation.last_user_message,
            "last_assistant_message": conversation.last_assistant_message,
        }
