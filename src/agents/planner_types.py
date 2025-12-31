from dataclasses import dataclass
from typing import Literal, List, Optional

ActionType = Literal[
    "retrieve",
    "respond",
    "chat"
]

@dataclass
class AgentAction:
    type: ActionType
    reason: Optional[str] = None

@dataclass
class AgentPlan:
    actions: List[AgentAction]
