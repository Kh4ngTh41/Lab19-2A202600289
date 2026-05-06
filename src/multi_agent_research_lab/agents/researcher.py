"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self._llm = LLMClient()
        self._search = SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        query = state.request.query
        max_sources = state.request.max_sources

        sources = self._search.search(query, max_results=max_sources)
        state.sources = sources

        context = "\n\n".join(
            f"[{i+1}] {s.title}: {s.snippet}"
            for i, s in enumerate(sources)
        )
        system_prompt = (
            "You are a research assistant. Given source documents, write clear and concise "
            "research notes summarizing the key findings. Focus on facts, claims, and any "
            "uncertainties. Keep it to 3-5 sentences per source when possible."
        )
        user_prompt = f"Sources:\n{context}\n\nWrite concise research notes for: {query}"
        response = self._llm.complete(system_prompt, user_prompt)
        state.research_notes = response.content

        return state
