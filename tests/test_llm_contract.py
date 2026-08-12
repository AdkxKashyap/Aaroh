import asyncio
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from pydantic import BaseModel
from src.services.llm_provider import OllamaProvider
from src.services.prompt_builder import IntentPromptBuilder


class DummyModel(BaseModel):
    name: str


def test_intent_prompt_includes_conversation_context_and_schema():
    prompt = IntentPromptBuilder.build_intent_prompt(
        message="Class 8A",
        file_content="Title: Fractions Project",
        conversation_context={
            "conversation_id": "abc",
            "status": "CLARIFICATION_REQUIRED",
            "intent": "CREATE_ASSIGNMENT",
            "workflow_data": {"missing_fields": ["class_name"]},
        },
    )

    assert "Conversation context:" in prompt
    assert '"status": "CLARIFICATION_REQUIRED"' in prompt
    assert '"clarification_question": null' in prompt
    assert '"proposed_action": {}' in prompt


def test_generate_json_validates_structured_output():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")

    async def fake_post(payload):
        return {"response": json.dumps({"name": "ok"})}

    provider._post = fake_post

    result = asyncio.run(provider.generate_json("prompt", DummyModel))

    assert result.name == "ok"
