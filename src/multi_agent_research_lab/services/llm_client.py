"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

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
    """Provider-agnostic LLM client using OpenAI."""

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self._client = openai.OpenAI(api_key=api_key)
        self._model = settings.openai_model

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

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
