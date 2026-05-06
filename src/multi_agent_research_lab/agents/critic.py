"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        final_answer = state.final_answer or ""
        research_notes = state.research_notes or ""
        sources = state.sources

        source_refs = "\n".join(
            f"- {s.title}: {s.url or 'N/A'}" for s in sources
        )
        system_prompt = (
            "You are a critical reviewer. Fact-check claims against sources, "
            "identify hallucination or unsupported assertions, and check citation coverage. "
            "Be strict and precise. Return your critique as a structured list of issues."
        )
        user_prompt = (
            f"Final answer to review:\n{final_answer}\n\n"
            f"Research notes:\n{research_notes}\n\n"
            f"Sources:\n{source_refs}\n\n"
            "Provide a structured critique with: Factual Issues, Unsupported Claims, Citation Gaps, Overall Assessment."
        )
        response = self._llm.complete(system_prompt, user_prompt)

        state.agent_results.append(
            AgentResult(
                agent="critic",
                content=response.content,
                metadata={"checked": True},
            )
        )
        state.errors.extend(self._extract_errors(response.content))

        return state

    def _extract_errors(self, critique: str) -> list[str]:
        """Simple heuristic to extract error lines from critique."""
        errors = []
        for line in critique.split("\n"):
            if any(
                keyword in line.lower()
                for keyword in ["error", "false", "unsupported", "missing", "gap", "issue"]
            ):
                errors.append(line.strip())
        return errors[:5]
