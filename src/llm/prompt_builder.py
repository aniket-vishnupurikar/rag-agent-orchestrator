# src/llm/prompt_builder.py
from src.agents.answer_modes import AnswerMode


def _instruction_for_answer_mode(answer_mode: AnswerMode) -> str:
    return {
        AnswerMode.QA: (
            "Provide a direct, factual answer to the user's question."
        ),
        AnswerMode.LIST: (
            "List the relevant items clearly. Cite each item using the provided source IDs."
        ),
        AnswerMode.EXPAND: (
            "Expand and explain the requested item in detail, citing sources."
        ),
        AnswerMode.SUMMARY: (
            "Provide a concise, high-level summary with citations where applicable."
        ),
    }.get(
        answer_mode,
        "Provide a helpful answer based on the documentation."
    )


def build_grounded_prompt(
    user_query: str,
    retrieved_chunks: list,
    chat_history: list,
    answer_mode: AnswerMode
) -> str:
    # 🔒 Dataset-agnostic citation: use chunk_id exactly
    context = "\n\n".join(
        f"[{c.get('chunk_id')}] {c.get('text')}"
        for c in retrieved_chunks
        if c.get("chunk_id") and c.get("text")
    )

    history = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat_history[-8:]
    )

    mode_instruction = _instruction_for_answer_mode(answer_mode)

    return f"""
You are an enterprise assistant answering strictly from documentation.

Conversation so far:
{history}

Documentation (cite sources like [C03759]):
{context}

Instruction:
{mode_instruction}
- Use ONLY the documentation above.
- Cite sources using the bracketed IDs.
- If information is missing, say so clearly.

User question:
{user_query}

Answer:
""".strip()


def build_chat_prompt(
    user_query: str,
    chat_history: list
) -> str:
    history = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat_history[-8:]
    )

    return f"""
You are a helpful assistant.

Conversation:
{history}

User:
{user_query}

Assistant:
""".strip()
