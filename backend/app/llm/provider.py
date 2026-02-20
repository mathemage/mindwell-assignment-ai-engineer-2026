"""LLM provider interface and implementations."""
from abc import ABC, abstractmethod
from typing import Any

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.errors import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, Any],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate a structured response from the LLM."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.default_temperature = settings.llm_temperature
        self.default_max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a response from OpenAI."""
        try:
            logger.info(
                "Generating LLM response",
                model=self.model,
                num_messages=len(messages),
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                timeout=self.timeout,
            )

            content = response.choices[0].message.content or ""
            logger.info(
                "LLM response generated",
                response_length=len(content),
                tokens_used=response.usage.total_tokens if response.usage else 0,
            )

            return content

        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            raise LLMError(f"Failed to generate LLM response: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, Any],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate a structured JSON response from OpenAI."""
        import json

        try:
            logger.info(
                "Generating structured LLM response",
                model=self.model,
                num_messages=len(messages),
            )

            # Prepend JSON format instruction as system message if not already present
            # or incorporate into user message to avoid appending after user messages
            messages_with_format = messages.copy()
            
            # Check if there's already a system message
            has_system = any(msg.get("role") == "system" for msg in messages_with_format)
            
            if has_system:
                # Add instruction to the existing system message
                for msg in messages_with_format:
                    if msg.get("role") == "system":
                        msg["content"] += f"\n\nRespond with valid JSON matching this schema: {json.dumps(response_format)}"
                        break
            else:
                # Prepend as first system message
                messages_with_format.insert(0, {
                    "role": "system",
                    "content": f"Respond with valid JSON matching this schema: {json.dumps(response_format)}",
                })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages_with_format,  # type: ignore
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                response_format={"type": "json_object"},
                timeout=self.timeout,
            )

            content = response.choices[0].message.content or "{}"
            logger.info(
                "Structured LLM response generated",
                tokens_used=response.usage.total_tokens if response.usage else 0,
            )

            return json.loads(content)

        except Exception as e:
            logger.error("Structured LLM generation failed", error=str(e))
            raise LLMError(f"Failed to generate structured LLM response: {str(e)}") from e


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider."""
    return OpenAIProvider()
