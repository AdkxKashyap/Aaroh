from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel
from src.config.settings import get_settings
from src.core.logger import logger
from src.services.prompt_builder import IntentPromptBuilder

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Transport abstraction for model providers.

    Providers implement only the actual LLM request/response behavior. Prompt
    construction is intentionally handled elsewhere so that the prompt layer can
    be changed without modifying the provider logic.
    """

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Ollama-backed provider used by default in the POC."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.OLLAMA_TIMEOUT_SECONDS
        )

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Ollama request failed")
            raise ValueError(
                "AI service is currently unavailable. Please try again."
            ) from exc

    @staticmethod
    def _extract_json(text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return cleaned

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        return cleaned

    async def generate_response(
        self,
        prompt: str,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "stream": False,
            "prompt": prompt,
            "options": {"temperature": 0.1},
        }
        logger.info(f"LLM request payload: {payload}")
        raw = await self._post(payload)
        text = raw.get("response", "").strip()
        logger.info(f"LLM raw response: {text}")
        if not text:
            raise ValueError(
                "LLM returned an empty response for intent classification."
            )

        cleaned = self._extract_json(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM intent response was not valid JSON.") from exc

    async def generate_json(self, prompt: str, response_model: type[T]) -> T:
        payload = {
            "model": self.model,
            "stream": False,
            "prompt": prompt,
            "options": {"temperature": 0.1},
        }
        raw = await self._post(payload)
        text = raw.get("response", "").strip()
        if not text:
            raise ValueError("LLM returned an empty response.")

        parsed = json.loads(text)
        return response_model.model_validate(parsed)


class LLMClientFactory:
    """Creates the default LLM provider for the POC.

    Later, this can return AzureOpenAIProvider or another concrete provider
    without adjusting the workflow code.
    """

    @staticmethod
    def create(provider: str = "ollama") -> LLMProvider:
        provider_name = (provider or "ollama").lower()
        if provider_name == "ollama":
            return OllamaProvider()
        raise ValueError(f"Unsupported LLM provider: {provider}")


__all__ = [
    "LLMClientFactory",
    "LLMProvider",
    "OllamaProvider",
]
