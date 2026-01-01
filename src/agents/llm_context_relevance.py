# src/agents/llm_context_relevance.py

from typing import Literal
from src.llm.llm_client import OpenAICompatibleClient

_llm = OpenAICompatibleClient()

ContextDecision = Literal["reuse", "retrieve"]


def judge_context_relevance_llm(
    user_query: str,
    retrieved_chunks: list,
    chat_history: list,
) -> ContextDecision:
    """
    LangGraph-style epistemic sufficiency check.

    Core question:
        "Can the assistant answer the user's question
         correctly and completely using ONLY its
         current knowledge and retrieved context?"

    Returns:
        "reuse"    → existing knowledge is sufficient
        "retrieve" → additional retrieval required

    Design principles:
    - Conservative by default
    - No heuristics
    - No topic matching
    - No intent inference
    - Pure epistemic judgment
    """

    # Guardrail: no context means insufficient by definition
    if not retrieved_chunks:
        return "retrieve"

    # Keep context minimal and focused (LangGraph-style)
    context_preview = "\n".join(
        f"- {c.get('text', '')[:250]}"
        for c in retrieved_chunks[:5]
    )

    conversation = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat_history[-6:]
    )

    prompt = f"""
You are an expert AI agent performing an epistemic check.

Your task is to decide whether the assistant already has
ENOUGH INFORMATION to answer the user's question correctly.

Conversation history:
{conversation}

Previously retrieved documentation:
{context_preview}

User's current question:
"{user_query}"

Decision criteria:
- Answer "reuse" ONLY if the available information is sufficient
  to answer the question fully and accurately.
- If any required detail is missing, unclear, or uncertain,
  answer "retrieve".
- If the question introduces a new topic or new information need,
  answer "retrieve".
- Be conservative. If unsure, answer "retrieve".

Respond with ONLY ONE WORD:
reuse
retrieve
""".strip()

    raw = _llm.generate(prompt).strip().lower()

    if raw == "reuse":
        return "reuse"

    # Default safety behavior
    return "retrieve"
