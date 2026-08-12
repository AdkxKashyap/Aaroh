import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.services.tool_registry import ToolRegistry


def test_tool_registry_routes_create_assignment_action():
    registry = ToolRegistry()

    result = registry.dispatch(
        "CREATE_ASSIGNMENT",
        {
            "title": "Science Lab",
            "class_id": "123e4567-e89b-12d3-a456-426614174000",
        },
    )

    assert result["tool_name"] == "AssignmentTool"
    assert result["status"] == "ready"
    assert result["payload"]["title"] == "Science Lab"


def test_tool_registry_rejects_unknown_intent():
    registry = ToolRegistry()

    try:
        registry.dispatch("NOT_REAL", {})
        assert False, "Expected ValueError for unsupported tool intent"
    except ValueError as exc:
        assert "Unsupported intent" in str(exc)
