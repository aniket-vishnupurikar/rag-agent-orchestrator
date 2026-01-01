from src.agents.agent_state import AgentState
from src.agents.planner_types import AgentPlan, AgentAction
from src.agents.llm_planner import build_plan_llm

# 🆕 Context relevance judge
from src.agents.llm_context_relevance import judge_context_relevance_llm

USE_LLM_PLANNER = True


def _is_explicitly_casual(user_query: str) -> bool:
    """
    Minimal, dataset-agnostic check for conversational intent.
    This is intentionally conservative.
    """
    casual_markers = [
        "let's start over",
        "start a new conversation",
        "new topic",
        "change the topic",
        "forget previous context",
        "ignore previous messages",
        "let's talk about something else",
        "just chatting",
        "random question",
    ]

    q = user_query.lower().strip()
    return any(q.startswith(m) or q == m for m in casual_markers)


def build_plan(
    user_query: str,
    agent_state: AgentState,
    chat_history: list
) -> AgentPlan:
    """
    Core planner entry point.

    Principles:
    - Retrieval-first grounding
    - LLM advisory planning
    - Explicit safety constraints
    - Dataset-agnostic behavior
    """

    # ------------------------------------------------------------------
    # 🔒 HARD RAG SAFETY INVARIANT (FOUNDATIONAL)
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
    # 🧠 CONTEXT RELEVANCE RESET (FOUNDATIONAL)
    # ------------------------------------------------------------------
    relevance_decision = judge_context_relevance_llm(
        user_query=user_query,
        retrieved_chunks=agent_state.last_retrieved_chunks,
        chat_history=chat_history,
    )

    if relevance_decision == "retrieve":
        return AgentPlan([
            AgentAction(
                type="retrieve",
                reason="Existing context not relevant to new question"
            ),
            AgentAction(type="respond")
        ])

    # ------------------------------------------------------------------
    # 🧠 LLM PLANNER (ADVISORY)
    # ------------------------------------------------------------------
    if USE_LLM_PLANNER:
        plan = build_plan_llm(
            user_query=user_query,
            agent_state=agent_state,
            chat_history=chat_history,
            intent_metadata=getattr(
                agent_state, "last_intent_metadata", None
            )
        )

        if plan and plan.actions:
            # ----------------------------------------------------------
            # 🔒 PHASE 2.4 CONSTRAINT:
            # No ungrounded chat once documents exist
            # ----------------------------------------------------------
            contains_chat = any(
                a.type == "chat" for a in plan.actions
            )

            if contains_chat and not _is_explicitly_casual(user_query):
                return AgentPlan([
                    AgentAction(
                        type="respond",
                        reason="Grounded response enforced (post-retrieval)"
                    )
                ])

            return plan

    # ------------------------------------------------------------------
    # 🛟 FINAL SAFETY FALLBACK
    # ------------------------------------------------------------------
    return AgentPlan([
        AgentAction(
            type="respond",
            reason="Fallback respond with existing context"
        )
    ])
