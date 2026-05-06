"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self) -> None:
        self._llm = LLMClient()
        self._settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        iteration = state.iteration
        max_iterations = self._settings.max_iterations

        if iteration >= max_iterations:
            state.record_route("done")
            return state

        next_route = self._decide_route(state)
        state.record_route(next_route)
        return state

    def _decide_route(self, state: ResearchState) -> str:
        """Decide next route based on current state."""
        has_research = state.research_notes is not None
        has_analysis = state.analysis_notes is not None
        has_final = state.final_answer is not None

        if not has_research:
            return "researcher"
        if not has_analysis:
            return "analyst"
        if not has_final:
            return "writer"

        return "done"
