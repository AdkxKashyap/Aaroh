from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from src.core.logger import logger
from src.enums.actions import Actions
from src.enums.intent import IntentName
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.assignment import (
    AssignmentResponse,
    CreateAssignmentRequestWithClassName,
)
from src.schemas.chat import ChatResponse
from src.schemas.llm_response import AssignmentLLMResponse
from src.services.assignment_service import AssignmentService

from src.services.prompt_builder import AssignmentPromptBuilder


class Intent(ABC):
    """
    Base class for all intents.

    Only execute() is mandatory.
    """

    @abstractmethod
    def get_intent_name(self) -> IntentName:
        """
        Returns the name of the intent.
        """
        pass

    @abstractmethod
    def get_prompt(self, *args, **kwargs) -> str:
        pass

    @abstractmethod
    async def execute(
        self,
        user: User,
        payload: BaseModel,
    ) -> ChatResponse:
        """
        Execute the action represented by this intent.
        """
        pass


class UnknownIntent(Intent):
    def get_intent_name(self) -> IntentName:
        return IntentName.UNKNOWN

    def get_prompt(self, *args, **kwargs) -> str:
        return ""

    async def execute(
        self,
        user: User,
        payload: BaseModel,
    ) -> ChatResponse:
        return ChatResponse(
            status="unknown_intent",
            message="The intent is unknown or not supported.",
            intent=IntentName.UNKNOWN,
            proposed_action={},
            missing_fields=[],
            clarification_question=None,
            requires_approval=False,
            approval_data={},
        )


class UnsafeIntent(Intent):
    def get_intent_name(self) -> IntentName:
        return IntentName.UNSAFE

    def get_prompt(self, *args, **kwargs) -> str:
        return ""

    async def execute(
        self,
        user: User,
        payload: BaseModel,
    ) -> ChatResponse:
        return ChatResponse(
            status="blocked",
            message="The intent is unsafe and has been blocked.",
            intent=IntentName.UNSAFE,
            proposed_action={},
            missing_fields=[],
            clarification_question=None,
            requires_approval=False,
            approval_data={},
        )


class CreateAssignmentIntent(Intent):
    def __init__(
        self,
        assignment_service: AssignmentService,
    ):
        self.assignment_service = assignment_service

    def get_intent_name(self) -> IntentName:
        return IntentName.CREATE_ASSIGNMENT

    def get_prompt(self, **kwargs) -> str:
        message = kwargs.get("message", "")
        file_content = kwargs.get("file_content", "")
        return AssignmentPromptBuilder.build_prompt(
            message=message, file_content=file_content
        )

    async def execute(
        self,
        user: User,
        payload: BaseModel,
    ) -> ChatResponse:
        try:
            # Validate the LLM response.
            llm_response_data = AssignmentLLMResponse.model_validate(payload)

            # Missing information means we cannot execute yet.
            if llm_response_data.missing_information:
                return ChatResponse(
                    status=Actions.MISSING_INFORMATION,
                    message=(
                        llm_response_data.llm_message
                        or "Missing information for assignment creation."
                    ),
                    intent=IntentName.CREATE_ASSIGNMENT,
                    proposed_action={},
                    missing_fields=llm_response_data.missing_information,
                    clarification_question=None,
                    requires_approval=False,
                    approval_data={},
                )

            # Validate the actual assignment payload.
            assignment_data = CreateAssignmentRequestWithClassName.model_validate(
                llm_response_data.assignment_data
            )

            assignment_response = await self.assignment_service.create_assignment(
                current_user=user,
                title=assignment_data.title,
                description=assignment_data.description,
                due_date=assignment_data.due_date,
                class_name=assignment_data.class_name,
            )

            return self._to_chat_response(assignment_response)

        except Exception as exc:
            logger.exception(
                "Failed to execute CreateAssignmentIntent",
                user_id=getattr(user, "id", None),
                school_id=getattr(user, "school_id", None),
            )

            raise ValueError("AI model response was invalid.") from exc

    @staticmethod
    def _to_chat_response(
        assignment_response: AssignmentResponse,
    ) -> ChatResponse:
        return ChatResponse(
            status=Actions.SUCCESS,
            message="Assignment created successfully.",
            intent=IntentName.CREATE_ASSIGNMENT,
            proposed_action={},
            missing_fields=[],
            clarification_question=None,
            requires_approval=False,
            approval_data={},
        )


class IntentFactory:
    """
    Creates the appropriate Intent implementation.

    The factory receives already constructed domain services.
    It does NOT use FastAPI Depends().
    """

    def __init__(
        self,
        assignment_service: AssignmentService,
    ):
        self.assignment_service = assignment_service

    def get_intent(
        self,
        intent_name: IntentName,
    ) -> Intent:

        if intent_name == IntentName.CREATE_ASSIGNMENT:
            return CreateAssignmentIntent(
                assignment_service=self.assignment_service,
            )

        if intent_name == IntentName.UNSAFE:
            return UnsafeIntent()

        if intent_name == IntentName.UNKNOWN:
            return UnknownIntent()

        return UnknownIntent()
