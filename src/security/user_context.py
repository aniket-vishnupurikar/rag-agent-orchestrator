from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class UserContext:
    """
    Represents authenticated user attributes used for authorization
    and downstream ABAC enforcement.
    """
    user_id: str
    department: str
    clearance: int
    projects: List[str]
    raw_token: str = ""  # Non-persistent, for internal use only
