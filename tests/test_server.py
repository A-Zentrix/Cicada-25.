from fastapi.testclient import TestClient

from backend.server import app


client = TestClient(app)


def test_chat_validation():
    # Empty message should 422 due to min_length=1
    resp = client.post("/api/chat", json={"message": "", "language": "en-US"})
    assert resp.status_code == 422


def test_chat_ok_structure(monkeypatch):
    # Monkeypatch bot() to avoid calling external API
    from backend import server

    def fake_bot(msg: str, language: str = "en-US") -> str:
        return f"echo: {msg} [{language}]"

    monkeypatch.setattr(server, "bot", fake_bot)

    resp = client.post("/api/chat", json={"message": "hello", "language": "en-US"})
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data and data["reply"].startswith("echo:")


