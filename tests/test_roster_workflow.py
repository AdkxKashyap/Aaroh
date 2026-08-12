import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.schemas.chat import IntentResult
from src.services.chat_workflow import ChatWorkflowService
from src.services.roster_chat_workflow import RosterChatWorkflow
from src.services.roster_import_service import RosterImportService
from src.services.tool_registry import ToolRegistry


class FakeProvider:
    async def classify_intent(
        self, message, file_content=None, conversation_context=None
    ):
        return {
            "intent": "ROSTER_IMPORT",
            "confidence": 0.95,
            "extracted_data": {},
            "missing_fields": [],
            "ambiguities": [],
            "requires_clarification": False,
            "clarification_question": None,
            "clarification_questions": [],
            "proposed_action": {},
        }

    async def generate_json(self, prompt, response_model):
        return response_model(
            question="Please re-upload the roster with username, email, and password columns for each student."
        )


class FakeRosterService:
    def __init__(self):
        self.calls = []

    async def import_roster(self, current_user, rows, class_name=None, school_id=None):
        self.calls.append(rows)
        return {
            "rows_processed": len(rows),
            "students_created": len(rows),
            "classes_created": 1,
        }


def test_roster_parser_requires_credentials_columns():
    workflow = RosterChatWorkflow()
    result = workflow.build_draft("Name,Class,Parent Contact\nAva,7A,555-0101")

    assert "username" in result.missing_fields
    assert "email" in result.missing_fields
    assert "password" in result.missing_fields


def test_chat_workflow_uses_llm_question_for_missing_roster_credentials():
    service = ChatWorkflowService(
        FakeProvider(),
        tool_registry=ToolRegistry(roster_service=FakeRosterService()),
    )

    response = asyncio.run(
        service.process_message(
            current_user=SimpleNamespace(
                id="admin-1",
                school_id="school-1",
                roles=[SimpleNamespace(role=SimpleNamespace(name="ADMIN"))],
            ),
            request=SimpleNamespace(
                message="Import this roster",
                file_name="students.csv",
                file_content="Name,Class,Parent Contact\nAva,7A,555-0101",
                session_id="abc",
            ),
        )
    )

    assert response.status == "clarification_required"
    assert response.intent == "ROSTER_IMPORT"
    assert "username, email, and password" in response.message


def test_roster_import_service_uses_existing_class_and_student_services():
    class_repository = SimpleNamespace()
    created_classes = []
    created_students = []

    async def get_by_name(school_id, name):
        return None

    async def create_class(current_user, name):
        created_classes.append(name)
        return SimpleNamespace(id="class-1", name=name)

    async def create_student(current_user, username, email, password, class_id):
        created_students.append(
            {
                "username": username,
                "email": email,
                "password": password,
                "class_id": class_id,
            }
        )

    class_repository.get_by_name = get_by_name
    class_service = SimpleNamespace(create_class=create_class)
    student_service = SimpleNamespace(create_student=create_student)

    service = RosterImportService(
        class_repository=class_repository,
        class_service=class_service,
        student_service=student_service,
    )

    current_user = SimpleNamespace(
        school_id="school-1",
        roles=[SimpleNamespace(role=SimpleNamespace(name="ADMIN"))],
    )

    result = asyncio.run(
        service.import_roster(
            current_user=current_user,
            rows=[
                {
                    "name": "Ava",
                    "username": "ava",
                    "email": "ava@example.com",
                    "password": "secret",
                    "grade_class": "7A",
                }
            ],
        )
    )

    assert result["rows_processed"] == 1
    assert result["students_created"] == 1
    assert result["classes_created"] == 1
    assert created_classes == ["7A"]
    assert created_students[0]["username"] == "ava"
