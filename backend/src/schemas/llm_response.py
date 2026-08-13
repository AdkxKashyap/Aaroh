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

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict) and "assignment_data" not in obj:
            obj = {"assignment_data": obj}
        return super().model_validate(obj, *args, **kwargs)


class RosterExtractionLLMResponse(LLMResponse):
    """
    Represents the response from the LLM provider for roster extraction intents.
    """

    roster_data: list[dict[str, str]] | None = None
