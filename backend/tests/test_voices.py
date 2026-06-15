import os

from fastapi.testclient import TestClient

os.environ.setdefault("GEMINI_API_KEY", "test_key")

from app.api.voices import VOICES
from app.main import app

client = TestClient(app)


class TestVoicesStaticData:
    def test_voices_count(self) -> None:
        assert len(VOICES) == 30

    def test_voices_all_have_name_and_description(self) -> None:
        for voice in VOICES:
            assert isinstance(voice["name"], str) and len(voice["name"]) > 0
            assert isinstance(voice["description"], str) and len(voice["description"]) > 0

    def test_voices_names_unique(self) -> None:
        names = [voice["name"] for voice in VOICES]
        assert len(names) == len(set(names))


class TestVoicesEndpoint:
    def test_get_voices_returns_200(self) -> None:
        response = client.get("/api/voices")
        assert response.status_code == 200

    def test_get_voices_returns_30_voices(self) -> None:
        response = client.get("/api/voices")
        data = response.json()
        assert "voices" in data
        assert len(data["voices"]) == 30

    def test_get_voices_entries_have_name_and_description(self) -> None:
        response = client.get("/api/voices")
        data = response.json()
        for voice in data["voices"]:
            assert "name" in voice
            assert "description" in voice
            assert isinstance(voice["name"], str)
            assert isinstance(voice["description"], str)

    def test_get_voices_returns_json_content_type(self) -> None:
        response = client.get("/api/voices")
        assert "application/json" in response.headers["content-type"]
