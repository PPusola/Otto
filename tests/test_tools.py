from app.agent.models import ToolCall, ToolRisk
from app.agent.tools import ToolRegistry, ToolSpec


async def test_safe_tool_runs_immediately() -> None:
    async def handler(name: str) -> dict[str, str]:
        return {"hello": name}

    registry = ToolRegistry()
    registry.register(ToolSpec("hello", handler, ToolRisk.SAFE, autorun=True))

    result = await registry.run(ToolCall(tool="hello", args={"name": "Jarvis"}))

    assert result.ok is True
    assert result.result == {"hello": "Jarvis"}


async def test_sensitive_tool_requires_confirmation_when_autorun_disabled() -> None:
    async def handler() -> dict[str, bool]:
        return {"done": True}

    registry = ToolRegistry()
    registry.register(ToolSpec("danger", handler, ToolRisk.SENSITIVE, autorun=False))

    result = await registry.run(ToolCall(tool="danger"))

    assert result.ok is False
    assert result.requires_confirmation is True
    assert result.confirmation_id


async def test_sensitive_tool_runs_after_confirmation() -> None:
    async def handler() -> dict[str, bool]:
        return {"done": True}

    registry = ToolRegistry()
    registry.register(ToolSpec("danger", handler, ToolRisk.SENSITIVE, autorun=False))
    pending = await registry.run(ToolCall(tool="danger"))

    result = await registry.confirm(pending.confirmation_id or "", approve=True)

    assert result.ok is True
    assert result.result == {"done": True}

