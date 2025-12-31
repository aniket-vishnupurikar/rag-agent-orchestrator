from dataclasses import dataclass


@dataclass
class RetrievalToolInput:
    """
    Explicit representation of a retrieval tool invocation.
    """
    query: str
    top_k: int = 5
    