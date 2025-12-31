from dataclasses import dataclass
from typing import Literal, List, Optional

ActionType = Literal[
    "retrieve",
    "respond",
    "chat",
    "clarify"
]

@dataclass
class AgentAction:
    type: ActionType
    reason: Optional[str] = None

@dataclass
class AgentPlan:
    actions: List[AgentAction]
