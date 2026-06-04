from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptedMemory:
    def __init__(self, data_dir: Path, password: str) -> None:
        self.data_dir = data_dir
        self.memory_path = data_dir / "memory.enc"
        self.salt_path = data_dir / "memory.salt"
        self.fernet = Fernet(self._derive_key(password))

    def append_turn(self, role: str, content: str) -> None:
        state = self.load()
        state.setdefault("turns", []).append(
            {
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        state["turns"] = state["turns"][-40:]
        self.save(state)

    def load(self) -> dict[str, Any]:
        if not self.memory_path.exists():
            return {"turns": []}
        try:
            raw = self.fernet.decrypt(self.memory_path.read_bytes())
        except InvalidToken as exc:
            raise RuntimeError("Could not decrypt memory. Check JARVIS_MEMORY_PASSWORD.") from exc
        return json.loads(raw.decode("utf-8"))

    def save(self, state: dict[str, Any]) -> None:
        payload = json.dumps(state, ensure_ascii=True, indent=2).encode("utf-8")
        self.memory_path.write_bytes(self.fernet.encrypt(payload))

    def reset(self) -> None:
        if self.memory_path.exists():
            self.memory_path.unlink()

    def _derive_key(self, password: str) -> bytes:
        if self.salt_path.exists():
            salt = self.salt_path.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_path.write_bytes(salt)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
