import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logger import logger
from src.models.chat_conversation import ChatConversation


class ChatConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, conversation: ChatConversation) -> ChatConversation:
        try:
            self.db.add(conversation)
            await self.db.flush()
            await self.db.refresh(conversation)
            return conversation
        except SQLAlchemyError:
            logger.exception(
                "Failed to create chat conversation",
                user_id=conversation.user_id,
            )
            raise

    async def get_by_id(
        self,
        conversation_id: uuid.UUID,
    ) -> ChatConversation | None:
        try:
            result = await self.db.execute(
                select(ChatConversation).where(ChatConversation.id == conversation_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch chat conversation",
                conversation_id=conversation_id,
            )
            raise

    async def update(
        self,
        conversation: ChatConversation,
    ) -> ChatConversation:
        try:
            await self.db.flush()
            await self.db.refresh(conversation)
            return conversation
        except SQLAlchemyError:
            logger.exception(
                "Failed to update chat conversation",
                conversation_id=conversation.id,
            )
            raise
