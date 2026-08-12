from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseTool(ABC):
    """Base interface for all AI-driven action tools.

    Tools are intentionally thin: they validate/shape the intended action but do
    not write directly to the database. The real business service remains the
    write boundary.
    """

    name: str = "BaseTool"

    @abstractmethod
    async def execute(
        self,
        payload: dict[str, Any],
        current_user: Any = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


class AssignmentTool(BaseTool):
    name = "AssignmentTool"

    def __init__(self, assignment_service=None, **_: Any):
        self.assignment_service = assignment_service

    async def execute(
        self,
        payload: dict[str, Any],
        current_user: Any = None,
    ) -> dict[str, Any]:
        safe_payload = dict(payload or {})

        if self.assignment_service is None:
            return {
                "title": safe_payload.get("title"),
                "description": safe_payload.get("description"),
                "due_date": safe_payload.get("due_date"),
                "class_id": safe_payload.get("class_id"),
                "subject": safe_payload.get("subject"),
                "instructions": safe_payload.get("instructions"),
            }

        title = safe_payload.get("title")
        description = safe_payload.get("description") or safe_payload.get(
            "instructions"
        )
        due_date_value = safe_payload.get("due_date")
        class_id_value = safe_payload.get("class_id")

        if not title:
            raise ValueError("Assignment title is required.")
        if not class_id_value:
            raise ValueError("Class ID is required for assignment creation.")
        if not due_date_value:
            raise ValueError("Due date is required for assignment creation.")

        due_date = due_date_value
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

        created_assignment = await self.assignment_service.create_assignment(
            current_user=current_user,
            title=title,
            description=description or "",
            due_date=due_date,
            class_id=uuid.UUID(str(class_id_value)),
        )

        if isinstance(created_assignment, dict):
            assignment_result = created_assignment
        else:
            assignment_result = {
                "id": getattr(created_assignment, "id", None),
                "title": getattr(created_assignment, "title", None),
                "description": getattr(created_assignment, "description", None),
                "due_date": getattr(created_assignment, "due_date", None),
                "class_id": getattr(created_assignment, "class_id", None),
                "teacher_id": getattr(created_assignment, "teacher_id", None),
                "status": getattr(created_assignment, "status", None),
            }

        due_date_value = assignment_result.get("due_date")
        if getattr(due_date_value, "isoformat", None) is not None:
            due_date_value = due_date_value.isoformat()

        return {
            "id": str(assignment_result.get("id")),
            "title": assignment_result.get("title"),
            "description": assignment_result.get("description"),
            "due_date": due_date_value,
            "class_id": str(assignment_result.get("class_id")),
            "teacher_id": str(assignment_result.get("teacher_id")),
            "status": assignment_result.get("status"),
        }


class SubmitAssignmentTool(BaseTool):
    name = "SubmitAssignmentTool"

    def __init__(self, submission_service=None, **_: Any):
        self.submission_service = submission_service

    async def execute(
        self,
        payload: dict[str, Any],
        current_user: Any = None,
    ) -> dict[str, Any]:
        safe_payload = dict(payload or {})
        if self.submission_service is None:
            return {
                "assignment_id": safe_payload.get("assignment_id"),
                "student_id": safe_payload.get("student_id"),
                "submission_type": safe_payload.get("submission_type", "text"),
                "notes": safe_payload.get("notes"),
            }

        assignment_id = safe_payload.get("assignment_id")
        if not assignment_id:
            raise ValueError("Assignment ID is required for submission.")

        submission = await self.submission_service.submit_assignment(
            current_user=current_user,
            assignment_id=uuid.UUID(str(assignment_id)),
        )

        return {
            "id": str(submission.id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "status": submission.status,
        }


class RosterImportTool(BaseTool):
    name = "RosterImportTool"

    def __init__(self, roster_service=None, **_: Any):
        self.roster_service = roster_service

    async def execute(
        self,
        payload: dict[str, Any],
        current_user: Any = None,
    ) -> dict[str, Any]:
        safe_payload = dict(payload or {})
        rows = safe_payload.get("rows") or safe_payload.get("students") or []

        if self.roster_service is None:
            return {
                "rows": rows,
                "class_name": safe_payload.get("class_name"),
                "school_id": safe_payload.get("school_id"),
            }

        result = await self.roster_service.import_roster(
            current_user=current_user,
            rows=rows,
            class_name=safe_payload.get("class_name"),
            school_id=safe_payload.get("school_id"),
        )
        return {
            "rows_processed": (
                result.get("rows_processed") if isinstance(result, dict) else None
            ),
            "class_name": safe_payload.get("class_name"),
            "school_id": safe_payload.get("school_id"),
        }


class ToolRegistry:
    """Minimal action dispatcher for the AI chat POC.

    The LLM does not call business services directly. It emits a structured intent
    plus a validated payload. The registry maps the intent to a tool that is
    allowed to invoke the real application logic.
    """

    _TOOLS: dict[str, type[BaseTool]] = {
        "CREATE_ASSIGNMENT": AssignmentTool,
        "UPDATE_ASSIGNMENT": AssignmentTool,
        "SUBMIT_ASSIGNMENT": SubmitAssignmentTool,
        "ROSTER_IMPORT": RosterImportTool,
    }

    def __init__(
        self,
        assignment_service=None,
        submission_service=None,
        roster_service=None,
    ):
        self.assignment_service = assignment_service
        self.submission_service = submission_service
        self.roster_service = roster_service

    def preview(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        normalized_intent = (intent or "").upper()
        tool_cls = self._TOOLS.get(normalized_intent)
        if tool_cls is None:
            raise ValueError(f"Unsupported intent for tool dispatch: {intent}")

        return {
            "tool_name": tool_cls.__name__,
            "status": "ready",
            "payload": payload or {},
        }

    async def dispatch(
        self,
        intent: str,
        payload: dict[str, Any],
        current_user: Any = None,
    ) -> dict[str, Any]:
        normalized_intent = (intent or "").upper()
        tool_cls = self._TOOLS.get(normalized_intent)
        if tool_cls is None:
            raise ValueError(f"Unsupported intent for tool dispatch: {intent}")

        tool = tool_cls(
            assignment_service=self.assignment_service,
            submission_service=self.submission_service,
            roster_service=self.roster_service,
        )
        result = await tool.execute(payload or {}, current_user=current_user)

        return {
            "tool_name": tool.name,
            "status": (
                "executed"
                if any(
                    [
                        self.assignment_service,
                        self.submission_service,
                        self.roster_service,
                    ]
                )
                else "ready"
            ),
            "payload": result,
        }


__all__ = [
    "AssignmentTool",
    "BaseTool",
    "RosterImportTool",
    "SubmitAssignmentTool",
    "ToolRegistry",
]
