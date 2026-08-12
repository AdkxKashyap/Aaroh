import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.schemas.chat import IntentResult
from src.services.chat_workflow import ChatWorkflowService
from src.services.submission_chat_workflow import SubmissionChatWorkflow


class FakeProvider:
    async def classify_intent(self, message, file_content=None, conversation_context=None):
        return {
            "intent": "SUBMIT_ASSIGNMENT",
            "confidence": 0.9,
            "extracted_data": {},
            "missing_fields": ["assignment_id"],
            "ambiguities": [],
            "requires_clarification": True,
            "clarification_question": "Which assignment would you like to submit?",
            "clarification_questions": ["Which assignment would you like to submit?"],
            "proposed_action": {},
        }


def test_submission_chat_workflow_builds_payload_from_intent():
    workflow = SubmissionChatWorkflow()
    draft = workflow.build_draft(
        IntentResult(
            intent="SUBMIT_ASSIGNMENT",
            confidence=0.9,
            extracted_data={"assignment_id": "123", "notes": "Done"},
        )
    )

    assert draft.assignment_id == "123"
    assert draft.notes == "Done"


def test_submission_chat_workflow_requires_assignment_id():
    workflow = SubmissionChatWorkflow()
    draft = workflow.build_draft(
        IntentResult(intent="SUBMIT_ASSIGNMENT", confidence=0.9)
    )

    assert draft.missing_fields() == ["assignment_id"]


def test_chat_workflow_requires_clarification_for_missing_submission_assignment():
    service = ChatWorkflowService(FakeProvider())

    response = __import__("asyncio").run(
        service.process_message(
            current_user=SimpleNamespace(
                id="student-1",
                school_id="school-1",
                roles=[SimpleNamespace(role=SimpleNamespace(name="STUDENT"))],
            ),
            request=type(
                "Request",
                (),
                {
                    "message": "I completed my assignment",
                    "file_name": None,
                    "file_content": None,
                    "session_id": "abc",
                },
            )(),
        )
    )

    assert response.status == "clarification_required"
    assert response.intent == "SUBMIT_ASSIGNMENT"
    assert response.message == "Which assignment would you like to submit?"
