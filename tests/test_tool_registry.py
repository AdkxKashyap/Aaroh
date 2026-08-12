import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.schemas.chat import ApprovalRequest, ChatRequest
from src.services.chat_workflow import ChatWorkflowService
from src.services.tool_registry import ToolRegistry


class StubUser:
    def __init__(self):
        self.id = "teacher-1"
        self.school_id = "school-1"


class FakeAssignmentService:
    def __init__(self):
        self.calls = []

    async def create_assignment(
        self,
        current_user,
        title,
        description,
        due_date,
        class_id,
    ):
        self.calls.append(
            {
                "current_user": current_user,
                "title": title,
                "description": description,
                "due_date": due_date,
                "class_id": class_id,
            }
        )

        return SimpleNamespace(
            id="assignment-1",
            title=title,
            description=description,
            due_date=due_date,
            class_id=class_id,
            teacher_id="teacher-1",
            status="DRAFT",
        )


class FakeProvider:
    async def classify_intent(
        self,
        message: str,
        file_content: str | None = None,
        conversation_context=None,
    ):
        return {
            "intent": "CREATE_ASSIGNMENT",
            "confidence": 0.9,
            "extracted_data": {
                "title": "Science Lab",
                "description": "Lab report due next week",
                "due_date": (
                    datetime.now(timezone.utc) + timedelta(days=7)
                ).isoformat(),
                "class_name": "8A",
            },
            "missing_fields": [],
            "ambiguities": [],
            "requires_clarification": False,
            "clarification_question": None,
            "clarification_questions": [],
            "proposed_action": {
                "title": "Science Lab",
                "description": "Lab report due next week",
                "due_date": (
                    datetime.now(timezone.utc) + timedelta(days=7)
                ).isoformat(),
                "class_name": "8A",
            },
        }


def test_tool_registry_routes_create_assignment_action():
    registry = ToolRegistry()

    result = asyncio.run(
        registry.dispatch(
            "CREATE_ASSIGNMENT",
            {
                "title": "Science Lab",
                "class_id": "123e4567-e89b-12d3-a456-426614174000",
            },
        )
    )

    assert result["tool_name"] == "AssignmentTool"
    assert result["status"] == "ready"
    assert result["payload"]["title"] == "Science Lab"


def test_tool_registry_rejects_unknown_intent():
    registry = ToolRegistry()

    try:
        asyncio.run(registry.dispatch("NOT_REAL", {}))
        assert False, "Expected ValueError for unsupported tool intent"
    except ValueError as exc:
        assert "Unsupported intent" in str(exc)


def test_chat_workflow_requires_approval_before_execution():
    assignment_service = FakeAssignmentService()
    service = ChatWorkflowService(
        FakeProvider(),
        tool_registry=ToolRegistry(assignment_service=assignment_service),
    )

    response = asyncio.run(
        service.process_message(
            current_user=StubUser(),
            request=ChatRequest(
                message="Create an assignment",
                file_name="assignment.txt",
                file_content="Title: Science Lab",
                session_id="abc",
            ),
        )
    )

    assert response.intent == "CREATE_ASSIGNMENT"
    assert response.requires_approval is True
    assert response.action_payload is not None
    assert response.action_payload["tool_result"]["status"] == "ready"
    assert response.action_payload["class_name"] == "8A"
    assert assignment_service.calls == []


def test_chat_workflow_executes_only_after_approval():
    assignment_service = FakeAssignmentService()
    service = ChatWorkflowService(
        FakeProvider(),
        tool_registry=ToolRegistry(assignment_service=assignment_service),
    )

    response = asyncio.run(
        service.approve_action(
            current_user=StubUser(),
            request=ApprovalRequest(
                intent="CREATE_ASSIGNMENT",
                approved=True,
                action_payload={
                    "title": "Science Lab",
                    "description": "Lab report due next week",
                    "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                    "class_id": "123e4567-e89b-12d3-a456-426614174000",
                },
            ),
        )
    )

    assert response.status == "executed"
    assert response.intent == "CREATE_ASSIGNMENT"
    assert assignment_service.calls[0]["title"] == "Science Lab"
