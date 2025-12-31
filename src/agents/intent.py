from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentIntent:
    """
    Represents the user's evolving intent within a session.
    """
    name: str
    confidence: float = 0.0
    last_updated_turn: int = 0
    resolved: bool = False

    def reinforce(self, delta: float = 0.1):
        self.confidence = min(1.0, self.confidence + delta)

    def weaken(self, delta: float = 0.1):
        self.confidence = max(0.0, self.confidence - delta)
