# utils/models/chat_payload.py
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
import os

class OpenAIMessage(BaseModel):
    role: Literal["system", "user", "assistant", "function", "tool"]
    content: str
    name: Optional[str] = None  # for function calls

class ChatPayload(BaseModel):
    model: str = Field(default_factory=lambda: os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"))
    messages: List[OpenAIMessage]
    stream: bool = False
    temperature: float = 0.0
    top_p: float = 1.0
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Any] = None

    class Config:
        # drop any fields that are None when you call .dict()
        exclude_none = True
