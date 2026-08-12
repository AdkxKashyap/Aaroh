import asyncio
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.schemas.chat import ChatMessageRequest, ChatResponse
from src.services.chat_conversation_service import ChatConversationService
from src.services.chat_message_service import ChatMessageService


class FakeDB:
    def __init__(self):
        self.info = {}

    def in_transaction(self):
        return self.info.get("service_transaction_depth", 0) > 0

    async def commit(self):
        self.info["service_transaction_depth"] = 0

    async def rollback(self):
        self.info["service_transaction_depth"] = 0


class FakeConversation:
    def __init__(self, user_id, school_id, status, workflow_data=None):
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.school_id = school_id
        self.status = status
        self.current_intent = None
        self.last_user_message = None
        self.last_assistant_message = None
        self.workflow_data = workflow_data or {}


class FakeConversationRepository:
    def __init__(self):
        self.db = FakeDB()
        self.conversations = {}

    async def create(self, conversation):
        if conversation.id is None:
            conversation.id = uuid.uuid4()
        self.conversations[conversation.id] = conversation
        return conversation

    async def get_by_id(self, conversation_id):
        return self.conversations.get(conversation_id)

    async def update(self, conversation):
        self.conversations[conversation.id] = conversation
        return conversation


class StubUser:
    def __init__(self):
        self.id = uuid.uuid4()
        self.school_id = uuid.uuid4()


class FakeWorkflowService:
    def __init__(self):
        self.calls = []
        self.approval_calls = 0

    async def process_message(self, current_user, request, conversation_context=None):
        self.calls.append(conversation_context)
        if len(self.calls) == 1:
            return ChatResponse(
                status="clarification_required",
                intent="CREATE_ASSIGNMENT",
                message="Which class should receive this assignment?",
                missing_fields=["class_name"],
                clarification_questions=["Which class should receive this assignment?"],
                action_payload={"title": "Fractions Project"},
                requires_approval=False,
            )

        return ChatResponse(
            status="awaiting_approval",
            intent="CREATE_ASSIGNMENT",
            message="Do you approve this assignment?",
            action_payload={
                "title": "Fractions Project",
                "class_name": "8A",
                "subject": "Mathematics",
                "instructions": "Solve the worksheet.",
                "due_date": "2026-08-20",
            },
            requires_approval=True,
        )

    async def approve_action(self, current_user, request):
        self.approval_calls += 1
        return ChatResponse(
            status="executed",
            intent=request.intent,
            message="Assignment created successfully.",
            action_payload={"tool_result": {"status": "executed"}},
            requires_approval=False,
        )


def test_chat_message_service_resumes_clarification_conversation():
    repository = FakeConversationRepository()
    conversation_service = ChatConversationService(repository)
    workflow_service = FakeWorkflowService()
    message_service = ChatMessageService(workflow_service, conversation_service)
    user = StubUser()

    first_response = asyncio.run(
        message_service.handle_message(
            user,
            ChatMessageRequest(message="Create an assignment"),
        )
    )

    second_response = asyncio.run(
        message_service.handle_message(
            user,
            ChatMessageRequest(
                conversation_id=first_response.conversation_id,
                message="Class 8A",
            ),
        )
    )

    assert first_response.status == "CLARIFICATION_REQUIRED"
    assert first_response.missing_fields == ["class_name"]
    assert second_response.conversation_id == first_response.conversation_id
    assert second_response.status == "AWAITING_APPROVAL"
    assert workflow_service.calls[1]["status"] == "CLARIFICATION_REQUIRED"
    assert (
        workflow_service.calls[1]["workflow_data"]["missing_fields"] == ["class_name"]
    )
    assert (
        workflow_service.calls[1]["workflow_data"]["action_payload"]["title"]
        == "Fractions Project"
    )


def test_chat_message_service_executes_only_on_approval_message_once():
    repository = FakeConversationRepository()
    conversation_service = ChatConversationService(repository)
    workflow_service = FakeWorkflowService()
    message_service = ChatMessageService(workflow_service, conversation_service)
    user = StubUser()

    first_response = asyncio.run(
        message_service.handle_message(
            user,
            ChatMessageRequest(message="Create an assignment"),
        )
    )

    second_response = asyncio.run(
        message_service.handle_message(
            user,
            ChatMessageRequest(
                conversation_id=first_response.conversation_id,
                message="Class 8A",
            ),
        )
    )

    approval_response = asyncio.run(
        message_service.handle_message(
            user,
            ChatMessageRequest(
                conversation_id=first_response.conversation_id,
                message="Approve",
            ),
        )
    )

    repeated_approval_response = asyncio.run(
        message_service.handle_message(
            user,
            ChatMessageRequest(
                conversation_id=first_response.conversation_id,
                message="Approve",
            ),
        )
    )

    assert second_response.status == "AWAITING_APPROVAL"
    assert approval_response.status == "COMPLETED"
    assert approval_response.message == "Assignment created successfully."
    assert workflow_service.approval_calls == 1
    assert repeated_approval_response.status == "COMPLETED"
    assert repeated_approval_response.message == "This action has already been completed."
    assert workflow_service.approval_calls == 1
