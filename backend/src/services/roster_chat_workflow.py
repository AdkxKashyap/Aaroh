from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from src.services.document_parser import ParserError, RosterParser


class RosterRowDraft(BaseModel):
    name: str = ""
    username: str = ""
    email: str = ""
    password: str = ""
    grade_class: str = ""
    parent_contact: str = ""
    notes: str = ""

    model_config = ConfigDict(extra="ignore")


class RosterImportDraft(BaseModel):
    rows: list[RosterRowDraft] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    def to_payload(self) -> dict:
        return {
            "rows": [row.model_dump() for row in self.rows],
            "students": [row.model_dump() for row in self.rows],
        }


class RosterChatWorkflow:
    def build_draft(self, file_content: str | None) -> RosterImportDraft:
        if not file_content:
            return RosterImportDraft(
                rows=[],
                missing_fields=["file_content"],
                ambiguities=["Roster upload is required."],
            )

        parsed = RosterParser().parse(file_content)
        rows = [
            RosterRowDraft.model_validate(row) for row in parsed.data.get("rows", [])
        ]
        return RosterImportDraft(
            rows=rows,
            missing_fields=list(parsed.missing_fields or []),
            ambiguities=list(parsed.ambiguities or []),
        )

    @staticmethod
    def build_approval_message(draft: RosterImportDraft) -> str:
        class_names = sorted({row.grade_class for row in draft.rows if row.grade_class})
        class_summary = ", ".join(class_names) if class_names else "Unknown classes"
        return (
            f"I've prepared a roster import for {len(draft.rows)} students across {class_summary}. "
            "Do you approve this roster import?"
        )
