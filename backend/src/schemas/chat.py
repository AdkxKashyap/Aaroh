"""Schemas for the chat-based AI workflow.

This keeps the chat layer intentionally thin and decoupled from the business
services. The LLM only returns structured intent and extraction data; the actual
service calls still happen in the existing business layer.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    file_name: str | None = None
    file_content: str | None = None
    session_id: str | None = None


class ChatMessageRequest(BaseModel):
    conversation_id: uuid.UUID | None = None
    message: str | None = None
    file_name: str | None = None
    file_content: str | None = None


class ChatMessageResponse(BaseModel):
    conversation_id: uuid.UUID
    status: str
    message: str
    intent: str | None = None
    proposed_action: dict[str, Any] = Field(default_factory=dict)
    clarification_question: str | None = None
    requires_approval: bool = False
    approval_data: dict[str, Any] = Field(default_factory=dict)


class IntentResult(BaseModel):
    intent: Literal[
        "CREATE_ASSIGNMENT",
        "UPDATE_ASSIGNMENT",
        "SUBMIT_ASSIGNMENT",
        "ROSTER_IMPORT",
        "UNKNOWN",
        "UNSAFE",
    ]
    confidence: float = 0.0
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_question: str | None = None
    clarification_questions: list[str] = Field(default_factory=list)
    proposed_action: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    intent: str
    approved: bool = False
    action_payload: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None


class ChatResponse(BaseModel):
    status: str
    intent: str | None = None
    message: str
    clarification_questions: list[str] = Field(default_factory=list)
    action_payload: dict[str, Any] | None = None
    requires_approval: bool = False
