from src.agents.agent_state import AgentState
from src.agents.planner_types import AgentPlan, AgentAction


def build_plan(
    user_query: str,
    agent_state: AgentState,
    chat_history: list
) -> AgentPlan:
    """
    Phase-0 deterministic planner.
    No dataset-specific heuristics.
    """

    # If we already retrieved context in this session, reuse it
    if agent_state.last_retrieved_chunks:
        return AgentPlan([
            AgentAction(type="respond", reason="Reuse prior retrieval")
        ])

    # Otherwise, retrieve first
    return AgentPlan([
        AgentAction(type="retrieve", reason="Need context"),
        AgentAction(type="respond")
    ])
