import json
from src.agents.planner_types import AgentPlan, AgentAction
from src.llm.llm_client import OpenAICompatibleClient

llm_client = OpenAICompatibleClient()

PLANNER_PROMPT = """
You are an enterprise AI planner.

Your task is to decide what actions an assistant should take.
You must output ONLY valid JSON.

Available actions:
- retrieve: fetch documents
- respond: answer using available documents
- chat: conversational response
- clarify: ask the user for clarification

Rules:
1. If the user asks a factual question → retrieve then respond
2. If the user refers to previously mentioned documents → respond only
3. If no documents are needed → chat
4. Prefer minimal actions

Conversation state:
- Has prior documents: {has_docs}
- Conversation length: {history_len}

User message:
"{user_query}"

Respond ONLY in this JSON format:
{{
  "actions": [
    {{ "type": "<action>", "reason": "<short reason>" }}
  ]
}}
"""


def build_plan_llm(
    user_query: str,
    agent_state,
    chat_history
) -> AgentPlan:
    prompt = PLANNER_PROMPT.format(
        user_query=user_query,
        has_docs=bool(agent_state.last_retrieved_chunks),
        history_len=len(chat_history)
    )

    raw = llm_client.generate(prompt)

    try:
        data = json.loads(raw)
        actions = [
            AgentAction(
                type=a["type"],
                reason=a.get("reason")
            )
            for a in data["actions"]
        ]
        return AgentPlan(actions)
    except Exception:
        # 🔒 Safety fallback
        return AgentPlan([AgentAction(type="chat", reason="Planner fallback")])
