from src.agents.tools import RetrievalToolInput


def build_retrieval_request(user_message: str) -> RetrievalToolInput:
    """
    Construct retrieval query from user message.
    This is deliberately simple for now.
    """
    return RetrievalToolInput(
        query=user_message,
        top_k=10
    )
