import json
from typing import Optional

from src.agents.planner_types import AgentPlan, AgentAction
from src.llm.llm_client import OpenAICompatibleClient

llm_client = OpenAICompatibleClient()

PLANNER_PROMPT = """
You are an enterprise AI planner.

Your task is to decide what actions an assistant should take next.
You must output ONLY valid JSON.
Do NOT include explanations outside the JSON.

Available actions:
- retrieve: fetch documents
- respond: answer using available documents
- chat: conversational response
- clarify: ask the user for clarification

General planning principles:
- Prefer minimal actions
- Reuse existing documents if suitable
- Retrieve only if additional grounding is needed
- Ask for clarification only if the user intent is ambiguous

Conversation state:
- Has prior documents: {has_docs}
- Conversation length: {history_len}

Intent metadata (advisory, may be incomplete):
{intent_block}

User message:
"{user_query}"

Respond ONLY in this JSON format:
{{
  "actions": [
    {{ "type": "<action>", "reason": "<short reason>" }}
  ]
}}
""".strip()


def _format_intent_block(intent_metadata: Optional[dict]) -> str:
    """
    Formats intent metadata safely for the planner prompt.
    Planner must treat this as advisory context only.
    """
    if not intent_metadata:
        return "- No intent metadata available"

    lines = []
    for key, value in intent_metadata.items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)


def build_plan_llm(
    user_query: str,
    agent_state,
    chat_history,
    intent_metadata: Optional[dict] = None
) -> AgentPlan:
    """
    LLM-based planning.

    Responsibilities:
    - Decide *what* to do (not how)
    - Remain dataset-agnostic
    - Never override RAG safety rules (handled upstream)
    """

    prompt = PLANNER_PROMPT.format(
        user_query=user_query,
        has_docs=bool(agent_state.last_retrieved_chunks),
        history_len=len(chat_history),
        intent_block=_format_intent_block(intent_metadata),
    )

    raw = llm_client.generate(prompt)

    try:
        data = json.loads(raw)

        actions = []
        for action in data.get("actions", []):
            if "type" not in action:
                continue

            actions.append(
                AgentAction(
                    type=action["type"],
                    reason=action.get("reason", "LLM planned")
                )
            )

        if actions:
            return AgentPlan(actions)

    except Exception:
        pass

    # 🔒 Absolute safety fallback
    return AgentPlan([
        AgentAction(
            type="chat",
            reason="LLM planner fallback"
        )
    ])
