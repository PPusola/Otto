from app.agent.parser import parse_tool_call


def test_parse_tool_call_accepts_valid_json() -> None:
    call = parse_tool_call('{"tool": "spotify_pause", "args": {}}')
    assert call is not None
    assert call.tool == "spotify_pause"
    assert call.args == {}


def test_parse_tool_call_rejects_plain_text() -> None:
    assert parse_tool_call("Sure, I can help.") is None


def test_parse_tool_call_rejects_bad_json() -> None:
    assert parse_tool_call("{tool: nope}") is None

