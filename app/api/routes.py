from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response

from app.agent.models import ChatRequest, ChatResponse, ConfirmToolRequest, ToolResult, VoiceTtsRequest
from app.agent.parser import parse_tool_call
from app.agent.prompts import SYSTEM_PROMPT
from app.api.dependencies import get_memory, get_ollama, get_spotify, get_tools, get_voice
from app.core.memory import EncryptedMemory
from app.core.ollama import OllamaClient
from app.core.security import require_auth

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"ok": "true"}


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_auth)])
async def chat(
    request: ChatRequest,
    memory: EncryptedMemory = Depends(get_memory),
    ollama: OllamaClient = Depends(get_ollama),
) -> ChatResponse:
    memory.append_turn("user", request.message)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend({"role": turn["role"], "content": turn["content"]} for turn in memory.load().get("turns", [])[-12:])
    model_reply = await ollama.chat(messages)

    tool_results: list[ToolResult] = []
    tool_call = parse_tool_call(model_reply)
    if tool_call:
        result = await get_tools().run(tool_call)
        tool_results.append(result)
        if result.requires_confirmation:
            reply = f"I need confirmation before running {tool_call.tool}."
        elif result.ok:
            followup_messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": model_reply},
                {"role": "user", "content": f"UNTRUSTED TOOL RESULT for {result.tool}: {result.result}"},
            ]
            reply = await ollama.chat(followup_messages)
        else:
            reply = f"I could not run {tool_call.tool}: {result.error}"
    else:
        reply = model_reply

    memory.append_turn("assistant", reply)
    return ChatResponse(reply=reply, tool_results=tool_results)


@router.post("/tools/confirm", response_model=ToolResult, dependencies=[Depends(require_auth)])
async def confirm_tool(request: ConfirmToolRequest) -> ToolResult:
    return await get_tools().confirm(request.confirmation_id, request.approve)


@router.post("/memory/reset", dependencies=[Depends(require_auth)])
async def reset_memory(memory: EncryptedMemory = Depends(get_memory)) -> dict[str, bool]:
    memory.reset()
    return {"reset": True}


@router.post("/voice/transcribe", dependencies=[Depends(require_auth)])
async def transcribe_audio(file: UploadFile = File(...)) -> dict[str, str]:
    suffix = ".webm"
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[1]
    transcript = await get_voice().transcribe(await file.read(), suffix=suffix)
    return {"transcript": transcript}


@router.post("/voice/tts", dependencies=[Depends(require_auth)])
async def tts_audio(request: VoiceTtsRequest) -> Response:
    audio = await get_voice().speak_to_file(request.text)
    return Response(content=audio, media_type="audio/wav")


@router.get("/spotify/login", dependencies=[Depends(require_auth)])
async def spotify_login() -> dict[str, str]:
    return {"url": get_spotify().auth_url()}


@router.get("/spotify/callback")
async def spotify_callback(code: Optional[str] = None, error: Optional[str] = None) -> HTMLResponse:
    if error:
        raise HTTPException(status_code=400, detail=error)
    if not code:
        raise HTTPException(status_code=400, detail="Missing Spotify authorization code")
    await get_spotify().exchange_code(code)
    return HTMLResponse("<h1>Spotify connected to JARVIS.</h1><p>You can close this tab.</p>")


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token", "")
    from app.core.settings import get_settings

    if token != get_settings().auth_token:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            response = await chat(ChatRequest(message=payload.get("message", "")), memory=get_memory(), ollama=get_ollama())
            await websocket.send_json(response.model_dump())
    except WebSocketDisconnect:
        return
