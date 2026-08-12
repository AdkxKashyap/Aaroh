import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.schemas.chat import IntentResult
from src.services.assignment_chat_workflow import AssignmentChatWorkflow


def test_assignment_chat_workflow_merges_parser_and_llm_payloads():
    workflow = AssignmentChatWorkflow()
    intent = IntentResult(
        intent="CREATE_ASSIGNMENT",
        confidence=0.9,
        extracted_data={"class_name": "8A"},
        proposed_action={"subject": "Mathematics"},
    )

    result = workflow.build_draft(
        intent=intent,
        previous_payload={"title": "Fractions Project"},
        file_content="Instructions: Solve fractions\nDue Date: 2026-08-20",
    )

    assert result.draft.title == "Fractions Project"
    assert result.draft.subject == "Mathematics"
    assert result.draft.instructions == "Solve fractions"
    assert result.draft.due_date == "2026-08-20"
    assert result.draft.class_name == "8A"


def test_assignment_chat_workflow_preserves_llm_clarification_question():
    workflow = AssignmentChatWorkflow()
    intent = IntentResult(
        intent="CREATE_ASSIGNMENT",
        confidence=0.9,
        extracted_data={"title": "Fractions Project"},
        missing_fields=["class_name"],
        requires_clarification=True,
        clarification_question="Which class should receive this assignment?",
        clarification_questions=["Which class should receive this assignment?"],
    )

    result = workflow.build_draft(intent=intent)

    assert result.requires_clarification is True
    assert result.clarification_question == "Which class should receive this assignment?"
    assert result.clarification_questions[0] == "Which class should receive this assignment?"
