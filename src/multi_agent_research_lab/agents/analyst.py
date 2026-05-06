"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        research_notes = state.research_notes or "No research notes available."
        sources = state.sources

        source_refs = "\n".join(
            f"- {s.title}: {s.url or 'N/A'}" for s in sources
        )
        system_prompt = (
            "You are an analyst. Given research notes, extract key claims, "
            "compare different viewpoints, and flag weak evidence or gaps. "
            "Structure your analysis with clear sections. Be critical and rigorous."
        )
        user_prompt = (
            f"Research notes:\n{research_notes}\n\n"
            f"Sources:\n{source_refs}\n\n"
            "Provide a structured analysis with: Key Claims, Viewpoint Comparison, Weak Evidence Flags."
        )
        response = self._llm.complete(system_prompt, user_prompt)
        state.analysis_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent="analyst",
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )

        return state
