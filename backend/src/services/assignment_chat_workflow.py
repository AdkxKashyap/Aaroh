from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from src.schemas.chat import IntentResult
from src.services.document_parser import AssignmentBriefParser, ParserError


class AssignmentDraft(BaseModel):
    title: str | None = None
    subject: str | None = None
    instructions: str | None = None
    due_date: str | None = None
    class_id: str | None = None
    class_name: str | None = None
    attachments: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "AssignmentDraft":
        raw = dict(payload or {})
        class_name = raw.get("class_name") or raw.get("target_class")
        instructions = raw.get("instructions") or raw.get("description")
        return cls(
            title=raw.get("title"),
            subject=raw.get("subject"),
            instructions=instructions,
            due_date=raw.get("due_date"),
            class_id=(str(raw.get("class_id")) if raw.get("class_id") else None),
            class_name=class_name,
            attachments=list(raw.get("attachments") or []),
            constraints=list(raw.get("constraints") or []),
            ambiguities=list(raw.get("ambiguities") or []),
        )

    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        if not self.title:
            missing.append("title")
        if not self.subject:
            missing.append("subject")
        if not self.instructions:
            missing.append("instructions")
        if not self.due_date:
            missing.append("due_date")
        if not self.class_id and not self.class_name:
            missing.append("class_name")
        return missing

    def to_payload(self) -> dict[str, Any]:
        payload = self.model_dump(exclude_none=True)
        if self.instructions and "description" not in payload:
            payload["description"] = self.instructions
        return payload


@dataclass
class AssignmentWorkflowResult:
    draft: AssignmentDraft
    missing_fields: list[str]
    clarification_questions: list[str]
    clarification_question: str | None
    proposed_action: dict[str, Any]

    @property
    def requires_clarification(self) -> bool:
        return bool(self.missing_fields)


class AssignmentClarificationService:
    @staticmethod
    def questions_from_intent(intent: IntentResult) -> list[str]:
        questions = list(intent.clarification_questions or [])
        if intent.clarification_question:
            questions.insert(0, intent.clarification_question)
        return list(dict.fromkeys(question for question in questions if question))


class AssignmentApprovalGate:
    @staticmethod
    def build_approval_message(draft: AssignmentDraft) -> str:
        class_label = draft.class_name or draft.class_id or "Unknown class"
        return (
            "I've prepared the following assignment:\n\n"
            f"Title: {draft.title or 'N/A'}\n"
            f"Subject: {draft.subject or 'N/A'}\n"
            f"Class: {class_label}\n"
            f"Due: {draft.due_date or 'N/A'}\n\n"
            "Do you approve this assignment?"
        )


class AssignmentChatWorkflow:
    @staticmethod
    def _merge_payload(target: dict[str, Any], source: dict[str, Any] | None) -> None:
        for key, value in (source or {}).items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            if isinstance(value, list) and not value:
                continue
            target[key] = value

    def _parser_payload(self, file_content: str | None) -> dict[str, Any]:
        if not file_content:
            return {}
        try:
            parsed = AssignmentBriefParser().parse(file_content)
        except ParserError:
            return {}
        return dict(parsed.data or {})

    def build_draft(
        self,
        intent: IntentResult,
        previous_payload: dict[str, Any] | None = None,
        file_content: str | None = None,
    ) -> AssignmentWorkflowResult:
        combined_payload: dict[str, Any] = {}
        self._merge_payload(combined_payload, previous_payload)
        self._merge_payload(combined_payload, self._parser_payload(file_content))
        self._merge_payload(combined_payload, intent.extracted_data)
        self._merge_payload(combined_payload, intent.proposed_action)

        draft = AssignmentDraft.from_payload(combined_payload)
        missing_fields = list(dict.fromkeys((intent.missing_fields or []) + draft.missing_fields()))
        clarification_questions = AssignmentClarificationService.questions_from_intent(intent)
        clarification_question = intent.clarification_question

        return AssignmentWorkflowResult(
            draft=draft,
            missing_fields=missing_fields,
            clarification_questions=clarification_questions,
            clarification_question=clarification_question,
            proposed_action=draft.to_payload(),
        )
