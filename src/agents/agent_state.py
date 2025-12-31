from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AgentState:
    """
    Minimal agent memory for a session.
    """

    # Optional high-level intent (temporary, heuristic-based)
    last_intent: Optional[str] = None

    # Cached retrieval results (last successful retrieval only)
    last_retrieved_chunks: Optional[List[dict]] = None

    # LLM-derived intent metadata (non-blocking)
    last_intent_metadata: Optional[dict] = None

