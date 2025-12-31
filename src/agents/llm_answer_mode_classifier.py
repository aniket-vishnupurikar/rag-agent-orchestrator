from src.llm.llm_client import OpenAICompatibleClient
from src.agents.answer_modes import AnswerMode


_llm = OpenAICompatibleClient()


def classify_answer_mode_llm(
    user_query: str,
    chat_history: list
) -> AnswerMode:
    """
    LLM-based answer mode detection.
    Returns a single AnswerMode.
    Metadata-only; no side effects.
    """

    history = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat_history[-6:]
    )

    prompt = f"""
You are classifying how an assistant should respond.

Conversation so far:
{history}

User message:
{user_query}

Decide the best answer mode from the following options:
- qa       → answer a direct question
- list     → enumerate documents or items
- expand   → explain one item in detail
- summary  → provide a high-level overview

Return ONLY the mode name.
"""

    raw = _llm.generate(prompt).strip().lower()

    if raw in AnswerMode.__members__.values():
        return AnswerMode(raw)

    # Safe fallback
    return AnswerMode.QA
