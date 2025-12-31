from src.agents.agent_state import AgentState
from src.agents.planner_types import AgentPlan, AgentAction

# LLM-based planner (primary)
from src.agents.llm_planner import build_plan_llm


# Feature flag: keep for safety & testing
USE_LLM_PLANNER = True


def build_plan(
    user_query: str,
    agent_state: AgentState,
    chat_history: list
) -> AgentPlan:
    """
    Core planner entry point.

    Design goals:
    - Dataset agnostic
    - Enterprise-chat generic
    - LLM-driven
    - Safe against hallucination
    """

    # ------------------------------------------------------------------
    # 🔒 HARD RAG SAFETY INVARIANT (FOUNDATIONAL)
    # ------------------------------------------------------------------
    # If NO retrieval has ever happened in this session,
    # we MUST retrieve before answering — regardless of what
    # the LLM planner thinks.
    # ------------------------------------------------------------------
    if not agent_state.last_retrieved_chunks:
        return AgentPlan([
            AgentAction(
                type="retrieve",
                reason="Initial grounding required"
            ),
            AgentAction(type="respond")
        ])

    # ------------------------------------------------------------------
    # 🧠 LLM PLANNER (PRIMARY AFTER FIRST GROUNDING)
    # ------------------------------------------------------------------
    if USE_LLM_PLANNER:
        plan = build_plan_llm(
            user_query=user_query,
            agent_state=agent_state,
            chat_history=chat_history
        )

        # Safety net: never allow empty or malformed plans
        if plan and plan.actions:
            return plan

    # ------------------------------------------------------------------
    # 🛟 FINAL DETERMINISTIC FALLBACK
    # ------------------------------------------------------------------
    return AgentPlan([
        AgentAction(
            type="respond",
            reason="Fallback respond with existing context"
        )
    ])
