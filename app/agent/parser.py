from __future__ import annotations

import json
from typing import Optional

from pydantic import ValidationError

from app.agent.models import ToolCall


def parse_tool_call(text: str) -> Optional[ToolCall]:
    stripped = text.strip()
    if not stripped.startswith("{") or not stripped.endswith("}"):
        return None
    try:
        data = json.loads(stripped)
        return ToolCall.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        return None
