from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from src.schemas.chat import IntentResult


class SubmissionDraft(BaseModel):
    assignment_id: str | None = None
    notes: str | None = None
    submission_type: str = "text"

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def from_payload(cls, payload: dict | None) -> "SubmissionDraft":
        return cls.model_validate(payload or {})

    def missing_fields(self) -> list[str]:
        if not self.assignment_id:
            return ["assignment_id"]
        return []

    def to_payload(self) -> dict:
        return self.model_dump(exclude_none=True)


class SubmissionChatWorkflow:
    def build_draft(
        self,
        intent: IntentResult,
        previous_payload: dict | None = None,
    ) -> SubmissionDraft:
        payload: dict = {}
        payload.update(previous_payload or {})
        payload.update(intent.extracted_data or {})
        payload.update(intent.proposed_action or {})
        return SubmissionDraft.from_payload(payload)
