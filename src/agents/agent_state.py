# src/agents/agent_state.py
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class AgentState:
    """
    Minimal agent memory for a session.
    """

    last_intent: Optional[str] = None

    # Cached retrieval results (last successful retrieval only)
    last_retrieved_chunks: Optional[List[dict]] = None

    # LLM-derived intent metadata (non-blocking)
    last_intent_metadata: Optional[Dict] = None

    # LLM-derived answer mode
    last_answer_mode: Optional[str] = None

    # 🆕 Source map for citation integrity & follow-ups
    # {chunk_id: {"doc_id": ..., "domain": ...}}
    last_source_map: Optional[Dict[str, Dict]] = None
