import re


RETRIEVAL_KEYWORDS = [
    "what is",
    "how does",
    "explain",
    "documentation",
    "policy",
    "timeout",
    "error",
    "config",
    "authentication",
    "authorization"
]


def should_retrieve(message: str) -> bool:
    """
    Decide whether retrieval is needed for this message.
    Deterministic, auditable logic.
    """
    msg = message.lower()

    # Question-like
    if "?" in msg:
        return True

    # Keyword-based
    for kw in RETRIEVAL_KEYWORDS:
        if kw in msg:
            return True

    return False
