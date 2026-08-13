import uuid
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.enums.chat import ChatConversationStatus
from src.models.base import BaseModel


class ChatConversation(BaseModel):
    __tablename__ = "chat_conversations"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey("schools.id"),
        nullable=False,
    )

    status: Mapped[ChatConversationStatus] = mapped_column(
        Enum(ChatConversationStatus),
        nullable=False,
        default=ChatConversationStatus.NEW,
    )

    current_intent: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    last_user_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_assistant_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    workflow_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
