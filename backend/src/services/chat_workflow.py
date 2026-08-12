from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError
from src.core.logger import logger
from src.enums.role import RoleName
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
from src.services.submission_chat_workflow import SubmissionChatWorkflow
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
    #TODO: Improve Prompt.Add these as system prompts
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
        self.submission_workflow = SubmissionChatWorkflow()

    @staticmethod
    def _role_names(current_user) -> set[str]:
        names: set[str] = set()
        for user_role in getattr(current_user, "roles", []) or []:
            role_name = getattr(getattr(user_role, "role", None), "name", None)
            if role_name:
                names.add(role_name)
        return names

    def _ensure_intent_authorized(self, current_user, intent: str) -> None:
        required_roles = {
            # TODO: Simplify intent handling
            "CREATE_ASSIGNMENT": {RoleName.TEACHER},
            "ROSTER_IMPORT": {RoleName.ADMIN},
            "SUBMIT_ASSIGNMENT": {RoleName.STUDENT},
        }
        expected = required_roles.get(intent)
        if not expected:
            return

        role_names = self._role_names(current_user)
        if role_names.intersection(expected):
            return

        logger.warning(
            "Chat intent authorization failed",
            user_id=getattr(current_user, "id", None),
            school_id=getattr(current_user, "school_id", None),
            intent=intent,
            required_roles=list(expected),
        )
        raise PermissionError("Access denied.")

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
            logger.warning(
                "Blocked unsafe chat request",
                user_id=getattr(current_user, "id", None),
                school_id=getattr(current_user, "school_id", None),
            )
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
        try:
            intent = IntentResult.model_validate(payload)
        except ValidationError as exc:
            logger.exception(
                "Invalid LLM output",
                user_id=getattr(current_user, "id", None),
                school_id=getattr(current_user, "school_id", None),
            )
            raise ValueError("AI model response was invalid.") from exc

        logger.info(
            "Chat intent classified",
            user_id=getattr(current_user, "id", None),
            school_id=getattr(current_user, "school_id", None),
            intent=intent.intent,
            conversation_id=(conversation_context or {}).get("conversation_id"),
            workflow_state=(conversation_context or {}).get("status"),
        )

        self._ensure_intent_authorized(current_user, intent.intent)
        # TODO: Simplify intent handling. Use onlt 2 Intent for POC
        # TODO: Improve Prompt.Clarification Questions should be generated by llm provider, Improve Initial prompt
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
        # TODO: Improve Prompt. Clarification Questions should be generated by llm provider, Improve Initial prompt
        approval_message = "Please confirm this action before I execute it."

        if intent.intent == "CREATE_ASSIGNMENT":
            previous_payload = {}
            if conversation_context:
                previous_payload = (
                    conversation_context.get("workflow_data") or {}
                ).get("action_payload") or {}

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
            logger.info(
                "Assignment proposal awaiting approval",
                user_id=getattr(current_user, "id", None),
                school_id=getattr(current_user, "school_id", None),
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
            logger.info(
                "Roster proposal awaiting approval",
                user_id=getattr(current_user, "id", None),
                school_id=getattr(current_user, "school_id", None),
            )

        if intent.intent == "SUBMIT_ASSIGNMENT":
            previous_payload = {}
            if conversation_context:
                previous_payload = (
                    conversation_context.get("workflow_data") or {}
                ).get("action_payload") or {}

            submission_draft = self.submission_workflow.build_draft(
                intent=intent,
                previous_payload=previous_payload,
            )
            prepared_payload = submission_draft.to_payload()
            clarification_questions = list(intent.clarification_questions or [])
            if intent.clarification_question:
                clarification_questions.insert(0, intent.clarification_question)

            if submission_draft.missing_fields():
                return ChatResponse(
                    status="clarification_required",
                    intent=intent.intent,
                    message=intent.clarification_question
                    or "Which assignment would you like to submit?",
                    missing_fields=submission_draft.missing_fields(),
                    clarification_questions=clarification_questions
                    or submission_draft.missing_fields(),
                    action_payload={
                        "tool_result": self.tool_registry.preview(
                            intent.intent,
                            prepared_payload,
                        ),
                        **prepared_payload,
                    },
                )

            return ChatResponse(
                status="ready_to_execute",
                intent=intent.intent,
                message="I have enough information to submit this assignment.",
                action_payload={
                    "tool_result": self.tool_registry.preview(
                        intent.intent,
                        prepared_payload,
                    ),
                    **prepared_payload,
                },
                requires_approval=False,
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

        if (
            intent.requires_clarification
            or intent.missing_fields
            or clarification_questions
        ):
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

        return await self.execute_action(
            current_user=current_user,
            intent=request.intent,
            action_payload=request.action_payload,
            message="The approved action has been executed.",
        )

    async def execute_action(
        self,
        current_user,
        intent: str,
        action_payload: dict[str, Any],
        message: str,
    ) -> ChatResponse:
        logger.info(
            "Executing chat action",
            user_id=getattr(current_user, "id", None),
            school_id=getattr(current_user, "school_id", None),
            intent=intent,
        )
        tool_result = await self.tool_registry.dispatch(
            intent,
            action_payload,
            current_user=current_user,
        )

        return ChatResponse(
            status="executed",
            intent=intent,
            message=message,
            action_payload={"tool_result": tool_result},
            requires_approval=False,
        )


__all__ = [
    "ChatWorkflowService",
    "PromptInjectionGuard",
]
