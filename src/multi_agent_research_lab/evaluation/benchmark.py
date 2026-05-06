"""Benchmark skeleton for single-agent vs multi-agent."""

import re
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, quality, cost, citation coverage, and error rate."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    quality_score = _estimate_quality(state)
    estimated_cost = _estimate_cost(state)
    citation_coverage = _calc_citation_coverage(state)
    error_rate = _calc_error_rate(state)

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=estimated_cost,
        quality_score=quality_score,
        notes=(
            f"Citation coverage: {citation_coverage:.0%}, "
            f"Errors detected: {error_rate}"
        ),
    )
    return state, metrics


def _estimate_quality(state: ResearchState) -> float | None:
    """Estimate quality based on content completeness."""
    score = 0.0
    if state.final_answer:
        score += 4.0
    if state.analysis_notes:
        score += 2.0
    if state.research_notes:
        score += 2.0
    if len(state.sources) >= 3:
        score += 2.0
    return min(score, 10.0)


def _estimate_cost(state: ResearchState) -> float | None:
    """Estimate cost based on agent results token counts."""
    total_tokens = 0
    for result in state.agent_results:
        metadata = result.metadata
        input_tok = metadata.get("input_tokens", 0) or 0
        output_tok = metadata.get("output_tokens", 0) or 0
        total_tokens += input_tok + output_tok

    if total_tokens == 0:
        return None

    input_cost = total_tokens * 0.15 / 1_000_000
    output_cost = total_tokens * 0.60 / 1_000_000
    return input_cost + output_cost


def _calc_citation_coverage(state: ResearchState) -> float:
    """Calculate what fraction of claims have source citations."""
    answer = state.final_answer or ""
    if not answer:
        return 0.0

    citation_pattern = re.compile(r"\[\d+\]|\[\d+,\s*\d+\]|\[source \d+\]", re.IGNORECASE)
    citations_found = len(citation_pattern.findall(answer))
    num_sources = len(state.sources)

    if num_sources == 0:
        return 0.0

    return min(citations_found / num_sources, 1.0)


def _calc_error_rate(state: ResearchState) -> float:
    """Calculate error rate as fraction of trace events with errors."""
    if not state.trace:
        return 0.0
    error_count = sum(
        1 for t in state.trace if t.get("payload", {}).get("error")
    )
    return error_count / len(state.trace)
