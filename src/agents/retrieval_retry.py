from typing import List, Dict
from src.agents.tools import RetrievalToolInput


MAX_RETRIES = 2
MIN_ACCEPTABLE_SCORE = -6.0  # domain-tuned


def should_retry(chunks: List[Dict]) -> bool:
    """
    Decide whether retrieval results are weak enough to retry.
    """
    if not chunks:
        return True

    best_score = max(c.get("score", float("-inf")) for c in chunks)
    return best_score < MIN_ACCEPTABLE_SCORE


def refine_retrieval_input(
    original: RetrievalToolInput,
    attempt: int
) -> RetrievalToolInput:
    """
    Simple deterministic refinement strategy.
    """
    if attempt == 1:
        return RetrievalToolInput(
            query=f"{original.query} documentation",
            top_k=original.top_k
        )

    if attempt == 2:
        return RetrievalToolInput(
            query=f"internal policy {original.query}",
            top_k=original.top_k
        )

    return original
