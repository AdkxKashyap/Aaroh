import asyncio
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.enums.chat import ChatConversationStatus
from src.services.chat_conversation_service import ChatConversationService


class FakeDB:
    def __init__(self):
        self.info = {}
        self.commit_calls = 0
        self.rollback_calls = 0

    def in_transaction(self):
        return self.info.get("service_transaction_depth", 0) > 0

    async def commit(self):
        self.commit_calls += 1
        self.info["service_transaction_depth"] = 0

    async def rollback(self):
        self.rollback_calls += 1
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


def test_get_or_create_creates_new_conversation():
    repository = FakeConversationRepository()
    service = ChatConversationService(repository)
    user = StubUser()

    conversation = asyncio.run(service.get_or_create(user, None))

    assert conversation.user_id == user.id
    assert conversation.school_id == user.school_id
    assert conversation.status == ChatConversationStatus.NEW
    assert repository.db.commit_calls == 1


def test_get_or_create_resumes_existing_owned_conversation():
    repository = FakeConversationRepository()
    service = ChatConversationService(repository)
    user = StubUser()
    conversation = FakeConversation(
        user_id=user.id,
        school_id=user.school_id,
        status=ChatConversationStatus.CLARIFICATION_REQUIRED,
    )
    repository.conversations[conversation.id] = conversation

    resumed = asyncio.run(service.get_or_create(user, conversation.id))

    assert resumed.id == conversation.id
    assert resumed.status == ChatConversationStatus.CLARIFICATION_REQUIRED


def test_get_or_create_rejects_other_user_conversation():
    repository = FakeConversationRepository()
    service = ChatConversationService(repository)
    user = StubUser()
    conversation = FakeConversation(
        user_id=uuid.uuid4(),
        school_id=user.school_id,
        status=ChatConversationStatus.NEW,
    )
    repository.conversations[conversation.id] = conversation

    try:
        asyncio.run(service.get_or_create(user, conversation.id))
        assert False, "Expected access denial for another user's conversation"
    except ValueError as exc:
        assert "Access denied" in str(exc)


def test_get_or_create_rejects_other_school_conversation():
    repository = FakeConversationRepository()
    service = ChatConversationService(repository)
    user = StubUser()
    conversation = FakeConversation(
        user_id=user.id,
        school_id=uuid.uuid4(),
        status=ChatConversationStatus.NEW,
    )
    repository.conversations[conversation.id] = conversation

    try:
        asyncio.run(service.get_or_create(user, conversation.id))
        assert False, "Expected school access denial"
    except ValueError as exc:
        assert "your school" in str(exc)


def test_persist_result_updates_conversation_state():
    repository = FakeConversationRepository()
    service = ChatConversationService(repository)
    user = StubUser()
    conversation = asyncio.run(service.get_or_create(user, None))
    response = SimpleNamespace(
        status="awaiting_approval",
        intent="CREATE_ASSIGNMENT",
        message="Please confirm this action before I execute it.",
        action_payload={"title": "Science Lab"},
        clarification_questions=[],
        requires_approval=True,
    )

    updated = asyncio.run(
        service.persist_result(
            conversation=conversation,
            response=response,
            message="Create assignment",
            file_name="brief.txt",
            file_content="Title: Science Lab",
        )
    )

    assert updated.status == ChatConversationStatus.AWAITING_APPROVAL
    assert updated.current_intent == "CREATE_ASSIGNMENT"
    assert updated.workflow_data["action_payload"]["title"] == "Science Lab"
    assert updated.workflow_data["requires_approval"] is True
