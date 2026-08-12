from __future__ import annotations

import re

from src.schemas.chat import ApprovalRequest, ChatRequest, ChatResponse, IntentResult
from src.services.llm_provider import LLMProvider
from src.services.tool_registry import ToolRegistry


class PromptInjectionGuard:
    """Production-grade prompt-injection defense for the chat workflow.

    User and document text are treated as untrusted content. The system must not
    follow instructions hidden inside them, and must block attempts to override
    system behavior or bypass approval logic.
    """

    @staticmethod
    def _normalize(text: str | None) -> str:
        if not text:
            return ""
        normalized = text.lower()
        normalized = normalized.replace("\n", " ")
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @classmethod
    def contains_injection(cls, text: str | None) -> bool:
        if not text:
            return False

        normalized = cls._normalize(text)
        if not normalized:
            return False

        blocked_phrases = [
            "ignore previous instructions",
            "ignore all previous instructions",
            "override system",
            "override system instructions",
            "system prompt",
            "reveal system prompt",
            "act as admin",
            "act as developer",
            "act as system",
            "bypass approval",
            "forget all rules",
            "ignore all rules",
            "developer mode",
            "jailbreak",
            "roleplay as",
            "pretend to be",
            "you are now",
            "disregard previous instructions",
            "disregard all instructions",
        ]

        for phrase in blocked_phrases:
            if phrase in normalized:
                return True

        if re.search(
            r"(ignore|override|disregard|bypass|forget|reveal).*(instructions|rules|system|prompt|approval)",
            normalized,
        ):
            return True

        if re.search(
            r"(act as|pretend to be|roleplay as|you are now).*(admin|developer|system|owner)",
            normalized,
        ):
            return True

        return False

    @staticmethod
    def sanitize(text: str | None) -> str:
        if not text:
            return ""
        if PromptInjectionGuard.contains_injection(text):
            return "[suspicious content removed for safety]"
        return text


class ChatWorkflowService:
    """Chat workflow orchestrator.

    This is intentionally small and uses the existing business layer only via a
    future tool registry.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry | None = None,
    ):
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry or ToolRegistry()

    async def process_message(
        self,
        current_user,
        request: ChatRequest,
    ) -> ChatResponse:
        message_text = request.message or ""
        file_text = request.file_content or ""

        if PromptInjectionGuard.contains_injection(
            message_text
        ) or PromptInjectionGuard.contains_injection(file_text):
            return ChatResponse(
                status="blocked",
                intent="UNSAFE",
                message="This request is unsafe or out of scope.",
            )

        sanitized_message = PromptInjectionGuard.sanitize(message_text)
        sanitized_file_text = PromptInjectionGuard.sanitize(file_text)

        payload = await self.llm_provider.classify_intent(
            sanitized_message,
            sanitized_file_text,
        )
        intent = IntentResult.model_validate(payload)

        if intent.intent == "UNSAFE":
            return ChatResponse(
                status="blocked",
                intent="UNSAFE",
                message="This request is unsafe or out of scope.",
            )

        if intent.intent == "UNKNOWN":
            return ChatResponse(
                status="needs_input",
                intent="UNKNOWN",
                message="I can help with assignment creation, submission, or roster import.",
            )

        prepared_payload = intent.extracted_data or {}
        if intent.intent not in {"UNKNOWN", "UNSAFE"}:
            prepared_payload = {
                "tool_result": self.tool_registry.preview(
                    intent.intent,
                    intent.extracted_data,
                ),
                **(intent.extracted_data or {}),
            }

        if intent.missing_fields:
            return ChatResponse(
                status="clarification_required",
                intent=intent.intent,
                message="I need the following details before I can proceed.",
                clarification_questions=intent.clarification_questions
                or intent.missing_fields,
                action_payload=prepared_payload,
            )

        return ChatResponse(
            status="awaiting_approval",
            intent=intent.intent,
            message="Please confirm this action before I execute it.",
            action_payload=prepared_payload,
            requires_approval=True,
        )

    async def approve_action(
        self,
        current_user,
        request: ApprovalRequest,
    ) -> ChatResponse:
        if not request.approved:
            return ChatResponse(
                status="rejected",
                intent=request.intent,
                message="The action was not approved, so nothing was executed.",
                action_payload=request.action_payload,
            )

        tool_result = await self.tool_registry.dispatch(
            request.intent,
            request.action_payload,
            current_user=current_user,
        )

        return ChatResponse(
            status="executed",
            intent=request.intent,
            message="The approved action has been executed.",
            action_payload={"tool_result": tool_result},
            requires_approval=False,
        )


__all__ = [
    "ChatWorkflowService",
    "PromptInjectionGuard",
]
