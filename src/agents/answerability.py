from typing import List, Dict
import re


def is_answerable(
    user_query: str,
    retrieved_chunks: List[Dict],
    min_chunks: int = 2
) -> bool:
    """
    Soft heuristic: determines whether retrieved context
    is likely sufficient to answer the question.
    """

    if not retrieved_chunks or len(retrieved_chunks) < min_chunks:
        return False

    query_tokens = set(
        re.findall(r"\w+", user_query.lower())
    )

    overlap_count = 0

    for chunk in retrieved_chunks:
        chunk_tokens = set(
            re.findall(r"\w+", chunk.get("text", "").lower())
        )
        if len(query_tokens & chunk_tokens) >= 2:
            overlap_count += 1

    return overlap_count >= min_chunks
