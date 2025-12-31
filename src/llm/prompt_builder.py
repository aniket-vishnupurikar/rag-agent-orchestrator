from src.agents.answer_modes import AnswerMode


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

    if answer_mode == AnswerMode.QA:
        instruction = (
            "Answer the user's question concisely using the documentation."
        )

    elif answer_mode == AnswerMode.LIST:
        instruction = (
            "List the relevant documents or items found in the documentation."
        )

    elif answer_mode == AnswerMode.EXPAND:
        instruction = (
            "Explain the relevant document or section in detail. "
            "Structure the explanation clearly."
        )

    elif answer_mode == AnswerMode.SUMMARY:
        instruction = (
            "Provide a high-level summary of the documentation."
        )

    else:
        instruction = "Answer using the documentation."

    return f"""
You are an assistant answering based on provided documentation.

Conversation so far:
{history}

Documentation:
{context}

Instruction:
{instruction}

User question:
{user_query}

Answer:
"""


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
"""
