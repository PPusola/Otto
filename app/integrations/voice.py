from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import pyttsx3


class VoiceService:
    def __init__(self, whisper_binary: Optional[str], whisper_model: Optional[str]) -> None:
        self.whisper_binary = whisper_binary
        self.whisper_model = whisper_model

    async def transcribe(self, audio_bytes: bytes, suffix: str = ".wav") -> str:
        if not self.whisper_binary or not self.whisper_model:
            raise RuntimeError("whisper.cpp is not configured. Set JARVIS_WHISPER_CPP_BINARY and JARVIS_WHISPER_CPP_MODEL.")
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / f"input{suffix}"
            audio_path.write_bytes(audio_bytes)
            cmd = [self.whisper_binary, "-m", self.whisper_model, "-f", str(audio_path), "-otxt", "-of", str(Path(tmp) / "out")]
            process = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=False)
            if process.returncode != 0:
                raise RuntimeError(process.stderr.strip() or "whisper.cpp transcription failed")
            transcript_path = Path(tmp) / "out.txt"
            if transcript_path.exists():
                return transcript_path.read_text(encoding="utf-8").strip()
            return process.stdout.strip()

    async def speak_to_file(self, text: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "speech.wav"
            await asyncio.to_thread(self._save_speech, text, path)
            return path.read_bytes()

    def _save_speech(self, text: str, path: Path) -> None:
        engine = pyttsx3.init()
        engine.save_to_file(text, str(path))
        engine.runAndWait()
