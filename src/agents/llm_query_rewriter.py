# src/agents/llm_query_rewriter.py

from src.llm.llm_client import OpenAICompatibleClient

_llm = OpenAICompatibleClient()


def rewrite_query_llm(
    user_query: str,
    chat_history: list
) -> str:
    """
    LangGraph-style query rewriting.

    Purpose:
    - Rewrite the query ONLY when retrieval is required
    - Produce a self-contained, retrieval-optimized query
    - No answering, no hallucination

    This mirrors LangGraph's rewrite node behavior.
    """

    history = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat_history[-6:]
    )

    prompt = f"""
You are an expert query rewriter for retrieval.

Your task:
Rewrite the user's latest question into a single, self-contained
search query that will retrieve the most relevant documents.

Rules:
- Use ONLY information implied by the conversation
- Do NOT answer the question
- Do NOT add new facts
- Resolve pronouns and references
- Remove conversational phrasing
- Maximize retrievability, not readability

Conversation history:
{history}

User question:
"{user_query}"

Return ONLY the rewritten query.
No explanations. No quotes.
""".strip()

    rewritten = _llm.generate(prompt).strip()

    # Absolute safety fallback
    return rewritten or user_query
