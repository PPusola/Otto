from __future__ import annotations

import base64
import time
import urllib.parse
from pathlib import Path
from typing import Any, Optional

import httpx

from app.agent.models import SpotifyTokenState
from app.core.memory import EncryptedMemory


SPOTIFY_SCOPES = "user-read-playback-state user-modify-playback-state streaming"


class SpotifyClient:
    def __init__(
        self,
        client_id: Optional[str],
        client_secret: Optional[str],
        redirect_uri: str,
        default_device_id: Optional[str],
        memory: EncryptedMemory,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.default_device_id = default_device_id
        self.memory = memory

    def auth_url(self, state: str = "jarvis") -> str:
        self._require_config()
        query = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": SPOTIFY_SCOPES,
                "state": state,
            }
        )
        return f"https://accounts.spotify.com/authorize?{query}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        self._require_config()
        token = await self._token_request({"grant_type": "authorization_code", "code": code, "redirect_uri": self.redirect_uri})
        self._save_token(token)
        return {"ok": True, "scope": token.get("scope", "")}

    async def search(self, query: str) -> dict[str, Any]:
        data = await self._api("GET", "/v1/search", params={"q": query, "type": "track,album,playlist", "limit": 5})
        tracks = [
            {
                "name": item["name"],
                "uri": item["uri"],
                "artist": ", ".join(artist["name"] for artist in item.get("artists", [])),
            }
            for item in data.get("tracks", {}).get("items", [])
        ]
        return {"tracks": tracks}

    async def play(self, query_or_uri: str) -> dict[str, Any]:
        uri = query_or_uri
        if not uri.startswith("spotify:"):
            results = await self.search(query_or_uri)
            tracks = results.get("tracks", [])
            if not tracks:
                raise RuntimeError(f"No Spotify result found for {query_or_uri!r}")
            uri = tracks[0]["uri"]

        body: dict[str, Any] = {"uris": [uri]} if uri.startswith("spotify:track:") else {"context_uri": uri}
        params = {"device_id": self.default_device_id} if self.default_device_id else None
        await self._api("PUT", "/v1/me/player/play", params=params, json=body, expect_json=False)
        return {"playing": uri}

    async def pause(self) -> dict[str, Any]:
        await self._api("PUT", "/v1/me/player/pause", expect_json=False)
        return {"paused": True}

    async def next(self) -> dict[str, Any]:
        await self._api("POST", "/v1/me/player/next", expect_json=False)
        return {"skipped": "next"}

    async def previous(self) -> dict[str, Any]:
        await self._api("POST", "/v1/me/player/previous", expect_json=False)
        return {"skipped": "previous"}

    async def set_volume(self, percent: int) -> dict[str, Any]:
        if percent < 0 or percent > 100:
            raise ValueError("Spotify volume percent must be between 0 and 100")
        await self._api("PUT", "/v1/me/player/volume", params={"volume_percent": percent}, expect_json=False)
        return {"volume_percent": percent}

    async def currently_playing(self) -> dict[str, Any]:
        data = await self._api("GET", "/v1/me/player/currently-playing")
        item = data.get("item") or {}
        return {
            "is_playing": data.get("is_playing", False),
            "name": item.get("name"),
            "uri": item.get("uri"),
            "artist": ", ".join(artist["name"] for artist in item.get("artists", [])),
        }

    async def _api(self, method: str, path: str, expect_json: bool = True, **kwargs: Any) -> Any:
        token = await self._valid_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token.access_token}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, f"https://api.spotify.com{path}", headers=headers, **kwargs)
        if response.status_code == 204:
            return {}
        if response.status_code == 404:
            raise RuntimeError("Spotify has no active playback device. Open Spotify on one device and try again.")
        response.raise_for_status()
        return response.json() if expect_json else {}

    async def _valid_token(self) -> SpotifyTokenState:
        state = self.memory.load()
        token_data = state.get("spotify_token")
        if not token_data:
            raise RuntimeError("Spotify is not connected. Visit /api/spotify/login first.")
        token = SpotifyTokenState.model_validate(token_data)
        if token.expires_at - 60 > time.time():
            return token
        if not token.refresh_token:
            raise RuntimeError("Spotify token expired and no refresh token is available.")
        refreshed = await self._token_request({"grant_type": "refresh_token", "refresh_token": token.refresh_token})
        if not refreshed.get("refresh_token"):
            refreshed["refresh_token"] = token.refresh_token
        self._save_token(refreshed)
        return SpotifyTokenState.model_validate(self.memory.load()["spotify_token"])

    async def _token_request(self, data: dict[str, str]) -> dict[str, Any]:
        self._require_config()
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("ascii")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://accounts.spotify.com/api/token",
                data=data,
                headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
            )
        response.raise_for_status()
        return response.json()

    def _save_token(self, token: dict[str, Any]) -> None:
        state = self.memory.load()
        state["spotify_token"] = {
            "access_token": token["access_token"],
            "refresh_token": token.get("refresh_token"),
            "expires_at": time.time() + int(token.get("expires_in", 3600)),
            "scope": token.get("scope", ""),
        }
        self.memory.save(state)

    def _require_config(self) -> None:
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Spotify client id/secret are not configured.")


def spotify_cache_path(data_dir: Path) -> Path:
    return data_dir / "spotify.json"
