from __future__ import annotations

import re

from pydantic import ValidationError
from src.core.logger import logger
from src.enums.intent import IntentName
from src.enums.role import RoleName
from src.schemas.chat import (
    ChatRequest,
    ChatResponse,
    IntentResult,
)
from src.services.intent import IntentFactory
from src.services.llm_provider import LLMProvider
from src.services.prompt_builder import IntentPromptBuilder
from src.services.roster_chat_workflow import RosterChatWorkflow
from src.services.submission_chat_workflow import SubmissionChatWorkflow

"""TODO: Simplified Workflow for POC
    Upload->LLM->Intent Classification->GET PROMPTS for Intent->Generate Structured Response Based on Intent->Check for Missing Fields->If Missing Fields->Ask to reupload with missing fields->If No Missing Fields->Ask for Approval->Execute Action
"""


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
        # TODO: Improve Prompt.Add these as system prompts
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
    ):
        self.llm_provider = llm_provider
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

    def _ensure_intent_authorized(self, current_user, intent: IntentName) -> None:
        required_roles = {
            # TODO: Simplify intent handling
            IntentName.CREATE_ASSIGNMENT: {RoleName.TEACHER},
            IntentName.ROSTER_IMPORT: {RoleName.ADMIN},
            IntentName.SUBMIT_ASSIGNMENT: {RoleName.STUDENT},
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

    async def process_message(
        self,
        current_user,
        request: ChatRequest,
        intent_factory: IntentFactory,
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
                intent=IntentName.UNSAFE,
                message="This request is unsafe or out of scope.",
            )

        sanitized_message = PromptInjectionGuard.sanitize(message_text)
        sanitized_file_text = PromptInjectionGuard.sanitize(file_text)

        prompt = IntentPromptBuilder.build_intent_prompt(
            sanitized_message,
            sanitized_file_text,
        )
        payload = await self.llm_provider.generate_response(
            prompt,
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
        )

        intent = intent_factory.get_intent(intent.intent)

        if (
            intent.get_intent_name() == IntentName.UNSAFE
            or intent.get_intent_name() == IntentName.UNKNOWN
        ):
            return await intent.execute(current_user, payload)

        self._ensure_intent_authorized(current_user, intent.get_intent_name())
        prompt = intent.get_prompt(message=sanitized_message, file_content=sanitized_file_text) or ""
        llm_response = await self.llm_provider.generate_response(
            prompt,
        )
        return await intent.execute(current_user, llm_response)
