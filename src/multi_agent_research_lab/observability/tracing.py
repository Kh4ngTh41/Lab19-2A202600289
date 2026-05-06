"""Tracing hooks with Langfuse integration.

Best practices:
- Use nested spans for distinct steps (agent:researcher, agent:analyst, etc.)
- Use descriptive names for traces
- Flush at the end of script
- Import Langfuse AFTER loading environment variables
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langfuse import Langfuse, observe

from multi_agent_research_lab.core.config import get_settings


_client: Langfuse | None = None


def _get_client() -> Langfuse:
    """Get or create Langfuse client."""
    global _client
    if _client is None:
        _client = Langfuse()
    return _client


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Create a Langfuse span for tracing.

    Best practices:
    - Use descriptive names like 'agent:researcher', 'llm:openai'
    - Pass relevant attributes for context
    """
    client = _get_client()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}}

    with client.span(name=name, tags=[name.split(":")[0]] if ":" in name else None) as langfuse_span:
        try:
            yield span
        except Exception as e:
            langfuse_span.level = "error"
            langfuse_span.metadata = {"error": str(e)}
            raise


def trace_agent(agent_name: str):
    """Decorator for agent functions to automatic tracing."""
    def decorator(func):
        @observe(observe_fn_name=f"agent:{agent_name}")
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def flush_traces() -> None:
    """Flush all pending traces to Langfuse. Call at script exit."""
    client = _get_client()
    client.flush()


def get_trace_summary() -> dict[str, Any]:
    """Return summary of recent traces."""
    client = _get_client()
    traces = client.api.get_recent_traces(limit=10)
    return {"traces": traces.model_dump() if hasattr(traces, 'model_dump') else str(traces)}
