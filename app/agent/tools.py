from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.agent.models import ToolCall, ToolResult, ToolRisk


ToolHandler = Callable[..., Awaitable[Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    handler: ToolHandler
    risk: ToolRisk
    autorun: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._pending: dict[str, ToolCall] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    async def run(self, call: ToolCall) -> ToolResult:
        spec = self._tools.get(call.tool)
        if not spec:
            return ToolResult(ok=False, tool=call.tool, error="Unknown tool")

        if spec.risk is ToolRisk.SENSITIVE and not spec.autorun:
            confirmation_id = str(uuid.uuid4())
            self._pending[confirmation_id] = call
            return ToolResult(
                ok=False,
                tool=call.tool,
                requires_confirmation=True,
                confirmation_id=confirmation_id,
                result={"tool": call.tool, "args": call.args},
            )

        return await self._execute(spec, call)

    async def confirm(self, confirmation_id: str, approve: bool) -> ToolResult:
        call = self._pending.pop(confirmation_id, None)
        if not call:
            return ToolResult(ok=False, tool="unknown", error="Unknown or expired confirmation id")
        if not approve:
            return ToolResult(ok=False, tool=call.tool, error="Tool call denied")
        spec = self._tools.get(call.tool)
        if not spec:
            return ToolResult(ok=False, tool=call.tool, error="Unknown tool")
        return await self._execute(spec, call)

    async def _execute(self, spec: ToolSpec, call: ToolCall) -> ToolResult:
        try:
            result = await spec.handler(**call.args)
            return ToolResult(ok=True, tool=call.tool, result=result)
        except TypeError as exc:
            return ToolResult(ok=False, tool=call.tool, error=f"Invalid tool arguments: {exc}")
        except Exception as exc:
            return ToolResult(ok=False, tool=call.tool, error=str(exc))


async def maybe_await(value: Any) -> Any:
    if asyncio.iscoroutine(value):
        return await value
    return value
