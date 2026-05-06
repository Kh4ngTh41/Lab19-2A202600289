"""Tracing hooks with Langfuse integration."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langfuse import Langfuse


_client: Langfuse | None = None


def _get_client() -> Langfuse:
    """Get or create Langfuse client."""
    global _client
    if _client is None:
        _client = Langfuse()
    return _client


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None):
    """Create a Langfuse span for tracing."""
    client = _get_client()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}}

    with client.start_as_current_observation(
        name=name,
        as_type="span",
        metadata=attributes,
    ) as langfuse_span:
        try:
            yield span
        except Exception as e:
            langfuse_span.level = "ERROR"
            langfuse_span.status_message = str(e)
            raise


def flush_traces() -> None:
    """Flush all pending traces to Langfuse."""
    client = _get_client()
    client.flush()
