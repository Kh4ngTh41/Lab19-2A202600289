"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        research_notes = state.research_notes or ""
        analysis_notes = state.analysis_notes or ""
        query = state.request.query
        sources = state.sources

        source_refs = "\n".join(
            f"[{i+1}] {s.title}: {s.url or 'N/A'}" for i, s in enumerate(sources)
        )
        system_prompt = (
            "You are a technical writer. Synthesize research notes and analysis into "
            "a clear, well-structured response. Include citations to sources. "
            "Write for the target audience and maintain objectivity."
        )
        user_prompt = (
            f"Query: {query}\n\n"
            f"Research notes:\n{research_notes}\n\n"
            f"Analysis:\n{analysis_notes}\n\n"
            f"Sources:\n{source_refs}\n\n"
            "Write a comprehensive response addressing the query, synthesizing all information."
        )
        response = self._llm.complete(system_prompt, user_prompt)
        state.final_answer = response.content

        return state
