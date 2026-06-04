from __future__ import annotations

from secrets import compare_digest
from typing import Optional

from fastapi import Header, HTTPException, Query, status

from app.core.settings import get_settings


def require_auth(authorization: Optional[str] = Header(default=None)) -> None:
    settings = get_settings()
    expected = f"Bearer {settings.auth_token}"
    if not authorization or not compare_digest(authorization, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JARVIS auth token")


def require_ws_auth(token: str = Query(default="")) -> None:
    settings = get_settings()
    if not token or not compare_digest(token, settings.auth_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JARVIS auth token")
