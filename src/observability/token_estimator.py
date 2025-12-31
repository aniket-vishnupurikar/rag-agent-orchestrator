def estimate_tokens(text: str) -> int:
    """
    Rough token estimation.
    ~4 chars per token for English.
    """
    return max(1, len(text) // 4)
