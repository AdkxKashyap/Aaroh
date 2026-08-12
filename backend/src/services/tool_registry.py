from __future__ import annotations

from typing import Any


class ToolRegistry:
    """Minimal action dispatcher for the AI chat POC.

    The LLM does not call business services directly. It emits a structured intent
    plus a validated payload. The registry maps the intent to a tool that is
    allowed to invoke the real application logic.
    """

    _TOOLS: dict[str, str] = {
        "CREATE_ASSIGNMENT": "AssignmentTool",
        "UPDATE_ASSIGNMENT": "AssignmentTool",
        "SUBMIT_ASSIGNMENT": "SubmitAssignmentTool",
        "ROSTER_IMPORT": "RosterImportTool",
    }

    def dispatch(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        tool_name = self._TOOLS.get((intent or "").upper())
        if tool_name is None:
            raise ValueError(f"Unsupported intent for tool dispatch: {intent}")

        return {
            "tool_name": tool_name,
            "status": "ready",
            "payload": payload,
        }


__all__ = ["ToolRegistry"]
