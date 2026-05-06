"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any


_trace_dir = Path.home() / ".claude" / "projects" / "multi-agent-traces"
_trace_dir.mkdir(parents=True, exist_ok=True)


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton.

    Writes spans to a JSON file for later analysis. Can be augmented with
    LangSmith/Langfuse provider spans when API keys are available.
    """
    started = datetime.now()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
        "started": started.isoformat(),
    }
    try:
        yield span
    finally:
        span["duration_seconds"] = (datetime.now() - started).total_seconds()
        span["ended"] = datetime.now().isoformat()
        _write_span(span)


def _write_span(span: dict[str, Any]) -> None:
    """Write a span to the trace file."""
    trace_file = _trace_dir / f"trace_{datetime.now():%Y%m%d}.jsonl"
    with open(trace_file, "a") as f:
        f.write(json.dumps(span) + "\n")


def get_trace_summary() -> dict[str, Any]:
    """Return summary of all traces for the current day."""
    trace_file = _trace_dir / f"trace_{datetime.now():%Y%m%d}.jsonl"
    if not trace_file.exists():
        return {"total_spans": 0, "spans": []}

    spans = []
    with open(trace_file) as f:
        for line in f:
            if line.strip():
                spans.append(json.loads(line))

    total_duration = sum(s.get("duration_seconds", 0) for s in spans)
    return {
        "total_spans": len(spans),
        "total_duration": total_duration,
        "spans": [s["name"] for s in spans],
    }
