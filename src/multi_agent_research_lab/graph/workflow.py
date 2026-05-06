"""LangGraph workflow skeleton."""

from typing import Any

from langgraph.graph import END, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {
            "supervisor": SupervisorAgent(),
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
        }
        self._graph: StateGraph | None = None

    def build(self) -> StateGraph:
        """Create a LangGraph graph."""
        workflow = StateGraph(ResearchState)

        workflow.add_node("supervisor", self._wrap_agent("supervisor"))
        workflow.add_node("researcher", self._wrap_agent("researcher"))
        workflow.add_node("analyst", self._wrap_agent("analyst"))
        workflow.add_node("writer", self._wrap_agent("writer"))

        workflow.set_entry_point("supervisor")

        workflow.add_conditional_edges(
            "supervisor",
            self._route_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
            },
        )

        workflow.add_edge("researcher", "supervisor")
        workflow.add_edge("analyst", "supervisor")
        workflow.add_edge("writer", END)

        self._graph = workflow
        return workflow

    def _wrap_agent(self, name: str):
        """Wrap agent to use trace_span."""
        agent = self._agents[name]

        def wrapped(state: ResearchState) -> ResearchState:
            with trace_span(f"agent:{name}") as span:
                result = agent.run(state)
                state.add_trace_event(f"agent:{name}", span)
                return result

        return wrapped

    def _route_decision(self, state: ResearchState) -> str:
        """Route based on supervisor's decision stored in route_history."""
        if not state.route_history:
            return "researcher"
        last_route = state.route_history[-1]
        if last_route in ("researcher", "analyst", "writer", "done"):
            return last_route
        return "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        if self._graph is None:
            self.build()
        app = self._graph.compile()
        result_dict = app.invoke(state)
        if isinstance(result_dict, dict):
            return ResearchState(**result_dict)
        return result_dict
