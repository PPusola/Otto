from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ToolRisk(str, Enum):
    SAFE = "safe"
    SENSITIVE = "sensitive"


class ToolCall(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    ok: bool
    tool: str
    result: Any = None
    error: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    tool_results: list[ToolResult] = Field(default_factory=list)


class ConfirmToolRequest(BaseModel):
    confirmation_id: str
    approve: bool


class VoiceTtsRequest(BaseModel):
    text: str


class SpotifyTokenState(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: float
    scope: str = ""

    @property
    def token_type(self) -> Literal["Bearer"]:
        return "Bearer"
