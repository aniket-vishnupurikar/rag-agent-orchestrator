def build_grounded_prompt(
    user_query: str,
    retrieved_chunks: list,
    chat_history: list
) -> str:
    context = "\n\n".join(
        f"[{i+1}] {c['text']}"
        for i, c in enumerate(retrieved_chunks)
    )

    history = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat_history[-6:]
    )

    return f"""
You are an assistant answering questions based on provided documentation.

Conversation so far:
{history}

Documentation:
{context}

User question:
{user_query}

Answer using the documentation. If the documentation does not contain the answer,
state that clearly.
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
