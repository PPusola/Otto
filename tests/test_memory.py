from app.core.memory import EncryptedMemory


def test_encrypted_memory_round_trip(tmp_path) -> None:
    memory = EncryptedMemory(tmp_path, "secret")
    memory.append_turn("user", "hello")

    loaded = memory.load()

    assert loaded["turns"][0]["role"] == "user"
    assert loaded["turns"][0]["content"] == "hello"
    assert b"hello" not in (tmp_path / "memory.enc").read_bytes()

