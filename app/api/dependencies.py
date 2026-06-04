from __future__ import annotations

from functools import lru_cache

from app.agent.models import ToolRisk
from app.agent.tools import ToolRegistry, ToolSpec
from app.core.memory import EncryptedMemory
from app.core.ollama import OllamaClient
from app.core.settings import get_settings
from app.integrations.spotify import SpotifyClient
from app.integrations.voice import VoiceService
from app.integrations.wiz import WizController


@lru_cache
def get_memory() -> EncryptedMemory:
    settings = get_settings()
    return EncryptedMemory(settings.data_dir, settings.memory_password)


@lru_cache
def get_ollama() -> OllamaClient:
    settings = get_settings()
    return OllamaClient(settings.ollama_base_url, settings.ollama_model)


@lru_cache
def get_spotify() -> SpotifyClient:
    settings = get_settings()
    return SpotifyClient(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        default_device_id=settings.spotify_default_device_id,
        memory=get_memory(),
    )


@lru_cache
def get_wiz() -> WizController:
    settings = get_settings()
    controller = WizController(settings.wiz_broadcast)
    controller.configure(settings.wiz_lights)
    return controller


@lru_cache
def get_voice() -> VoiceService:
    settings = get_settings()
    return VoiceService(settings.whisper_cpp_binary, settings.whisper_cpp_model)


@lru_cache
def get_tools() -> ToolRegistry:
    settings = get_settings()
    spotify = get_spotify()
    wiz = get_wiz()
    registry = ToolRegistry()

    registry.register(ToolSpec("spotify_search", spotify.search, ToolRisk.SAFE, autorun=True))
    registry.register(ToolSpec("spotify_play", spotify.play, ToolRisk.SENSITIVE, autorun=settings.allow_spotify_autorun))
    registry.register(ToolSpec("spotify_pause", spotify.pause, ToolRisk.SENSITIVE, autorun=settings.allow_spotify_autorun))
    registry.register(ToolSpec("spotify_next", spotify.next, ToolRisk.SENSITIVE, autorun=settings.allow_spotify_autorun))
    registry.register(ToolSpec("spotify_previous", spotify.previous, ToolRisk.SENSITIVE, autorun=settings.allow_spotify_autorun))
    registry.register(ToolSpec("spotify_set_volume", spotify.set_volume, ToolRisk.SENSITIVE, autorun=settings.allow_spotify_autorun))
    registry.register(ToolSpec("spotify_currently_playing", spotify.currently_playing, ToolRisk.SAFE, autorun=True))

    registry.register(ToolSpec("wiz_discover_lights", wiz.discover, ToolRisk.SENSITIVE, autorun=settings.allow_wiz_autorun))
    registry.register(ToolSpec("wiz_light_on", wiz.turn_on, ToolRisk.SENSITIVE, autorun=settings.allow_wiz_autorun))
    registry.register(ToolSpec("wiz_light_off", wiz.turn_off, ToolRisk.SENSITIVE, autorun=settings.allow_wiz_autorun))
    registry.register(ToolSpec("wiz_set_brightness", wiz.set_brightness, ToolRisk.SENSITIVE, autorun=settings.allow_wiz_autorun))
    registry.register(ToolSpec("wiz_set_color", wiz.set_color, ToolRisk.SENSITIVE, autorun=settings.allow_wiz_autorun))
    return registry
