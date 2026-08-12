from __future__ import annotations

import re
from typing import Any

from src.schemas.chat import (
    ApprovalRequest,
    ChatRequest,
    ChatResponse,
    ClarificationQuestionResult,
    IntentResult,
)
from src.services.assignment_chat_workflow import (
    AssignmentApprovalGate,
    AssignmentChatWorkflow,
)
from src.services.llm_provider import LLMProvider
from src.services.prompt_builder import ClarificationPromptBuilder
from src.services.roster_chat_workflow import RosterChatWorkflow
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
        self.assignment_workflow = AssignmentChatWorkflow()
        self.roster_workflow = RosterChatWorkflow()

    async def _build_clarification_question(
        self,
        intent: str,
        missing_fields: list[str],
        ambiguities: list[str],
        structured_data: dict[str, Any],
    ) -> str:
        prompt = ClarificationPromptBuilder.build_clarification_prompt(
            intent=intent,
            missing_fields=missing_fields,
            ambiguities=ambiguities,
            structured_data=structured_data,
        )
        result = await self.llm_provider.generate_json(
            prompt,
            ClarificationQuestionResult,
        )
        return result.question

    async def process_message(
        self,
        current_user,
        request: ChatRequest,
        conversation_context: dict[str, Any] | None = None,
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
            conversation_context=conversation_context,
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

        prepared_payload = intent.proposed_action or intent.extracted_data or {}
        approval_message = "Please confirm this action before I execute it."

        if intent.intent == "CREATE_ASSIGNMENT":
            previous_payload = {}
            if conversation_context:
                previous_payload = (
                    (conversation_context.get("workflow_data") or {}).get(
                        "action_payload"
                    )
                    or {}
                )

            assignment_result = self.assignment_workflow.build_draft(
                intent=intent,
                previous_payload=previous_payload,
                file_content=sanitized_file_text,
            )
            prepared_payload = assignment_result.proposed_action
            clarification_questions = assignment_result.clarification_questions
            if assignment_result.clarification_question:
                clarification_questions = [
                    assignment_result.clarification_question,
                    *clarification_questions,
                ]
            clarification_questions = list(dict.fromkeys(clarification_questions))

            if assignment_result.requires_clarification:
                return ChatResponse(
                    status="clarification_required",
                    intent=intent.intent,
                    message=assignment_result.clarification_question
                    or "I need a few more details before I can proceed.",
                    missing_fields=assignment_result.missing_fields,
                    clarification_questions=clarification_questions
                    or assignment_result.missing_fields,
                    action_payload={
                        "tool_result": self.tool_registry.preview(
                            intent.intent,
                            prepared_payload,
                        ),
                        **prepared_payload,
                    },
                )

            approval_message = AssignmentApprovalGate.build_approval_message(
                assignment_result.draft
            )

        if intent.intent == "ROSTER_IMPORT":
            roster_result = self.roster_workflow.build_draft(sanitized_file_text)
            prepared_payload = roster_result.to_payload()
            if roster_result.missing_fields or roster_result.ambiguities:
                question = await self._build_clarification_question(
                    intent=intent.intent,
                    missing_fields=roster_result.missing_fields,
                    ambiguities=roster_result.ambiguities,
                    structured_data=prepared_payload,
                )
                return ChatResponse(
                    status="clarification_required",
                    intent=intent.intent,
                    message=question,
                    missing_fields=roster_result.missing_fields,
                    clarification_questions=[question],
                    action_payload={
                        "tool_result": self.tool_registry.preview(
                            intent.intent,
                            prepared_payload,
                        ),
                        **prepared_payload,
                    },
                )

            approval_message = self.roster_workflow.build_approval_message(
                roster_result
            )

        if intent.intent not in {"UNKNOWN", "UNSAFE"}:
            prepared_payload = {
                "tool_result": self.tool_registry.preview(
                    intent.intent,
                    prepared_payload,
                ),
                **prepared_payload,
            }

        clarification_questions = list(intent.clarification_questions or [])
        if intent.clarification_question:
            clarification_questions.insert(0, intent.clarification_question)

        if intent.requires_clarification or intent.missing_fields or clarification_questions:
            return ChatResponse(
                status="clarification_required",
                intent=intent.intent,
                message=intent.clarification_question
                or "I need a few more details before I can proceed.",
                missing_fields=list(intent.missing_fields or []),
                clarification_questions=clarification_questions
                or intent.missing_fields,
                action_payload=prepared_payload,
            )

        return ChatResponse(
            status="awaiting_approval",
            intent=intent.intent,
            message=approval_message,
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
