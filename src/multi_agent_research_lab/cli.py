"""Command-line entrypoint for the lab starter."""

from time import perf_counter
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import flush_traces

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline using simple researcher-writer pipeline."""

    _init()
    started = perf_counter()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)

    from multi_agent_research_lab.agents.researcher import ResearcherAgent
    from multi_agent_research_lab.agents.writer import WriterAgent

    researcher = ResearcherAgent()
    writer = WriterAgent()

    researcher.run(state)
    writer.run(state)

    latency = perf_counter() - started

    console.print(Panel.fit(
        f"[bold]Query:[/bold] {query}\n\n"
        f"[bold]Latency:[/bold] {latency:.2f}s\n\n"
        f"[bold]Answer:[/bold]\n{state.final_answer}",
        title="Single-Agent Baseline",
    ))

    flush_traces()


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)

    console.print(Panel.fit(
        f"[bold]Query:[/bold] {result.request.query}\n\n"
        f"[bold]Route history:[/bold] {' → '.join(result.route_history)}\n\n"
        f"[bold]Final answer:[/bold]\n{result.final_answer}",
        title="Multi-Agent Workflow",
    ))

    flush_traces()


@app.command("benchmark")
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run benchmark comparing baseline vs multi-agent."""

    _init()

    def baseline_runner(q: str) -> ResearchState:
        from multi_agent_research_lab.agents.researcher import ResearcherAgent
        from multi_agent_research_lab.agents.writer import WriterAgent
        s = ResearchState(request=ResearchQuery(query=q))
        ResearcherAgent().run(s)
        WriterAgent().run(s)
        return s

    def multi_runner(q: str) -> ResearchState:
        return MultiAgentWorkflow().run(ResearchState(request=ResearchQuery(query=q)))

    console.print("[bold]Running baseline...[/bold]")
    _, baseline_metrics = run_benchmark("baseline", query, baseline_runner)

    console.print("[bold]Running multi-agent...[/bold]")
    _, multi_metrics = run_benchmark("multi-agent", query, multi_runner)

    console.print(Panel.fit(
        f"[bold]Baseline:[/bold]\n"
        f"  Latency: {baseline_metrics.latency_seconds:.2f}s\n"
        f"  Cost: ${baseline_metrics.estimated_cost_usd or 0:.4f}\n"
        f"  Quality: {baseline_metrics.quality_score or 0:.1f}/10\n\n"
        f"[bold]Multi-Agent:[/bold]\n"
        f"  Latency: {multi_metrics.latency_seconds:.2f}s\n"
        f"  Cost: ${multi_metrics.estimated_cost_usd or 0:.4f}\n"
        f"  Quality: {multi_metrics.quality_score or 0:.1f}/10",
        title="Benchmark Results",
    ))

    flush_traces()


if __name__ == "__main__":
    app()
