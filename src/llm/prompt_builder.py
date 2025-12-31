from src.agents.answer_modes import AnswerMode


def _instruction_for_answer_mode(answer_mode: AnswerMode) -> str:
    return {
        AnswerMode.QA: (
            "Provide a direct, factual answer to the user's question."
        ),
        AnswerMode.LIST: (
            "List the relevant documents or items clearly and explicitly."
        ),
        AnswerMode.EXPAND: (
            "Expand and explain the requested item in detail."
        ),
        AnswerMode.SUMMARY: (
            "Provide a concise, high-level summary."
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
    context = "\n\n".join(
        f"[{i+1}] {c['text']}"
        for i, c in enumerate(retrieved_chunks)
    )

    history = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat_history[-6:]
    )

    mode_instruction = _instruction_for_answer_mode(answer_mode)

    return f"""
You are an enterprise assistant answering strictly from documentation.

Conversation so far:
{history}

Documentation:
{context}

Instruction:
{mode_instruction}
Do NOT invent information. If the answer is missing, say so clearly.

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
