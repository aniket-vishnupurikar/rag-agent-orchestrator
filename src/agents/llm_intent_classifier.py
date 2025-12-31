import json
from typing import Dict, Any

from src.llm.llm_client import OpenAICompatibleClient
from src.agents.agent_state import AgentState


llm_client = OpenAICompatibleClient()


INTENT_SYSTEM_PROMPT = """
You are an intent classification module for an enterprise chatbot.

Your job is to infer the user's intent at a HIGH LEVEL.
This intent is metadata only and does NOT control execution.

Use ONLY the following intent labels:

- INFORMATION_SEEKING
- EXPLANATION
- COMPARISON
- PROCEDURAL_GUIDANCE
- SUMMARIZATION
- FOLLOW_UP
- CLARIFICATION
- CASUAL_CONVERSATION
- OTHER

Return STRICT JSON with the following fields:
{
  "primary_intent": string,
  "confidence": number between 0 and 1,
  "is_follow_up": boolean,
  "needs_documents": boolean,
  "notes": string
}
"""


def classify_intent_llm(
    user_query: str,
    chat_history: list,
    agent_state: AgentState
) -> Dict[str, Any]:
    """
    Metadata-only LLM intent classification.
    Safe to ignore. No side effects.
    """

    history_text = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat_history[-4:]
    )

    prompt = f"""
{INTENT_SYSTEM_PROMPT}

Conversation history:
{history_text}

User message:
{user_query}

Return JSON only.
"""

    try:
        raw = llm_client.generate(prompt)
        return json.loads(raw)

    except Exception:
        # Silent failure by design
        return {
            "primary_intent": "OTHER",
            "confidence": 0.0,
            "is_follow_up": False,
            "needs_documents": False,
            "notes": "LLM intent classification failed"
        }
