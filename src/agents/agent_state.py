from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class AgentState:
    """
    Minimal agent memory for a session.
    """

    # Optional high-level intent (heuristic or LLM-derived)
    last_intent: Optional[str] = None

    # Cached retrieval results (last successful retrieval only)
    last_retrieved_chunks: Optional[List[dict]] = None

    # LLM-derived intent metadata (non-blocking)
    last_intent_metadata: Optional[Dict] = None

    # 🆕 LLM-derived answer mode (qa / list / expand / summary)
    last_answer_mode: Optional[str] = None
