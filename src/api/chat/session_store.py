from typing import Dict, List, Tuple
from src.api.models.response import ChatMessage
from src.agents.agent_state import AgentState
from src.agents.intent import AgentIntent


class SessionStore:
    """
    In-memory session store scoped by:
    user_id -> session_id -> list of ChatMessage

    Also maintains AgentState per (user_id, session_id).
    Redis-ready abstraction.
    """

    def __init__(self, max_messages: int = 20):
        self.sessions: Dict[str, Dict[str, List[ChatMessage]]] = {}
        self.agent_states: Dict[Tuple[str, str], AgentState] = {}
        self.max_messages = max_messages

    # ==========================
    # Chat history
    # ==========================

    def get_session(
        self,
        user_id: str,
        session_id: str
    ) -> List[ChatMessage]:
        return self.sessions.get(user_id, {}).get(session_id, [])

    def append_message(
        self,
        user_id: str,
        session_id: str,
        message: ChatMessage
    ) -> None:
        user_sessions = self.sessions.setdefault(user_id, {})
        messages = user_sessions.setdefault(session_id, [])

        messages.append(message)

        # rolling window
        if len(messages) > self.max_messages:
            user_sessions[session_id] = messages[-self.max_messages:]

    def session_exists(
        self,
        user_id: str,
        session_id: str
    ) -> bool:
        return session_id in self.sessions.get(user_id, {})

    # ==========================
    # Agent state
    # ==========================

    def get_agent_state(
        self,
        user_id: str,
        session_id: str
    ) -> AgentState:
        key = (user_id, session_id)
        if key not in self.agent_states:
            self.agent_states[key] = AgentState()
        return self.agent_states[key]

    def update_agent_state(
        self,
        user_id: str,
        session_id: str,
        **updates
    ) -> None:
        state = self.get_agent_state(user_id, session_id)
        for field, value in updates.items():
            setattr(state, field, value)

    # ==========================
    # Intent helpers(Part of Agent State)
    # ==========================

    def get_intent(
        self,
        user_id: str,
        session_id: str
    ) -> AgentIntent | None:
        state = self.get_agent_state(user_id, session_id)
        return state.intent

    def set_intent(
        self,
        user_id: str,
        session_id: str,
        intent: AgentIntent,
        confidence: float = 1.0
    ) -> None:
        state = self.get_agent_state(user_id, session_id)
        state.intent = intent
        state.intent_confidence = confidence

    def update_intent_confidence(
        self,
        user_id: str,
        session_id: str,
        delta: float
    ) -> None:
        state = self.get_agent_state(user_id, session_id)

        if state.intent_confidence is None:
            state.intent_confidence = 0.0

        state.intent_confidence = max(
            0.0,
            min(1.0, state.intent_confidence + delta)
        )
