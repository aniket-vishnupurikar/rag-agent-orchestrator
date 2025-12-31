from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(
        default=None,
        description="Client-provided session id. New session if omitted."
    )
    message: str = Field(
        ...,
        description="User input message"
    )
