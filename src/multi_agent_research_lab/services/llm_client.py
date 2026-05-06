"""LLM client abstraction with Langfuse tracing.

Production note: agents should depend on this interface instead of importing an SDK directly.
Uses Langfuse for LLM tracing with OpenTelemetry-based spans.
"""

import os
from dataclasses import dataclass

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client using OpenAI with Langfuse tracing.

    Uses Langfuse span context for tracing LLM calls.
    """

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self._client = openai.OpenAI(api_key=api_key)
        self._model = settings.openai_model

        # Initialize Langfuse with explicit credentials from settings
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key or "")
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key or "")
        os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)

        self._langfuse = None

    def _get_langfuse(self):
        """Lazy initialization of Langfuse client."""
        if self._langfuse is None:
            from langfuse import Langfuse
            self._langfuse = Langfuse()
        return self._langfuse

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with retry and token logging."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        langfuse = self._get_langfuse()

        with langfuse.start_as_current_observation(
            name="llm:openai",
            model=self._model,
            input={"system": system_prompt, "user": user_prompt},
            model_parameters={"temperature": 0.7, "max_tokens": 2048},
        ) as span:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
            )
            usage = response.usage
            content = response.choices[0].message.content or ""

            input_tokens = usage.prompt_tokens if usage else None
            output_tokens = usage.completion_tokens if usage else None

            cost_usd = None
            if input_tokens and output_tokens:
                input_cost = input_tokens * 0.15 / 1_000_000
                output_cost = output_tokens * 0.60 / 1_000_000
                cost_usd = input_cost + output_cost

            span.update(
                output=content,
                usage_details={
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                },
                cost_details={"total_cost": cost_usd} if cost_usd else None,
            )

            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
            )
