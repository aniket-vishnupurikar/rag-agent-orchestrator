from typing import List
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]
