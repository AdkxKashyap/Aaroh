from pydantic import BaseModel
from src.schemas.assignment import CreateAssignmentRequestWithClassName


class LLMResponse(BaseModel):
    """
    Represents the response from the LLM provider.
    """

    llm_message: str | None = None
    missing_information: list[str] | None = None


class AssignmentLLMResponse(LLMResponse):
    """
    Represents the response from the LLM provider for assignment-related intents.
    """

    assignment_data: CreateAssignmentRequestWithClassName | None = None


class RosterExtractionLLMResponse(LLMResponse):
    """
    Represents the response from the LLM provider for roster extraction intents.
    """

    roster_data: list[dict[str, str]] | None = None
