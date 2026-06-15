import io
import os
import wave

from fastapi.testclient import TestClient

os.environ.setdefault("GEMINI_API_KEY", "test_key")

from app.main import app
from app.api.synthesize import get_tts_client
from app.tts.client import TtsClientError

client = TestClient(app)

FRAME_SIZE = 2


def _make_pcm(frame_count: int = 480) -> bytes:
    return bytes(i % 256 for i in range(frame_count * FRAME_SIZE))


class MockTtsClient:
    def __init__(
        self,
        pcm: bytes | None = None,
        error: Exception | None = None,
    ) -> None:
        self.pcm = pcm if pcm is not None else _make_pcm()
        self.error = error
        self.generate_content_calls: list[dict[str, str]] = []

    def generate_content(self, prompt: str, voice_name: str) -> bytes:
        self.generate_content_calls.append(
            {"prompt": prompt, "voice_name": voice_name}
        )
        if self.error:
            raise self.error
        return self.pcm


class TestSynthesizeValid:
    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def test_short_english_returns_200_audio_wav(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world. This is a test.", "voice": "Puck"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_wav_stdlib_readable(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        wav_bytes = response.content
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 24000
            assert wf.getnframes() > 0

    def test_passes_prompt_and_voice_to_client(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={
                "text": "Hello world.",
                "voice": "Zephyr",
                "style": "dramatic",
                "pacing": "slow",
                "accent": "British",
            },
        )

        assert response.status_code == 200
        call = mock_client.generate_content_calls[0]
        assert "Zephyr" in call["prompt"]
        assert "dramatic" in call["prompt"]
        assert "slow" in call["prompt"]
        assert "British" in call["prompt"]
        assert "Hello world." in call["prompt"]
        assert call["voice_name"] == "Zephyr"

    def test_strips_voice_before_client_call(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": " Hello world. ", "voice": " Puck "},
        )

        assert response.status_code == 200
        call = mock_client.generate_content_calls[0]
        assert call["voice_name"] == "Puck"
        assert " Hello world. " in call["prompt"]

    def test_default_style_pacing_accent_omitted(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Test.", "voice": "Puck"},
        )

        assert response.status_code == 200
        call = mock_client.generate_content_calls[0]
        assert "### DIRECTOR'S NOTES" in call["prompt"]
        assert "### TRANSCRIPT" in call["prompt"]
        assert "Test." in call["prompt"]


class TestSynthesizeValidation:
    def test_missing_text_returns_422(self) -> None:
        response = client.post("/api/synthesize", json={"voice": "Puck"})
        assert response.status_code == 422

    def test_empty_text_returns_422(self) -> None:
        response = client.post(
            "/api/synthesize", json={"text": "", "voice": "Puck"}
        )
        assert response.status_code == 422

    def test_whitespace_only_text_returns_422(self) -> None:
        response = client.post(
            "/api/synthesize", json={"text": "   ", "voice": "Puck"}
        )
        assert response.status_code == 422

    def test_missing_voice_returns_422(self) -> None:
        response = client.post(
            "/api/synthesize", json={"text": "Hello world."}
        )
        assert response.status_code == 422

    def test_empty_voice_returns_422(self) -> None:
        response = client.post(
            "/api/synthesize", json={"text": "Hello world.", "voice": ""}
        )
        assert response.status_code == 422

    def test_whitespace_only_voice_returns_422(self) -> None:
        response = client.post(
            "/api/synthesize", json={"text": "Hello world.", "voice": "   "}
        )
        assert response.status_code == 422

    def test_empty_body_returns_422(self) -> None:
        response = client.post("/api/synthesize", json={})
        assert response.status_code == 422


class TestSynthesizeErrorMapping:
    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def test_tts_error_502_maps_to_502(self) -> None:
        mock_client = MockTtsClient(
            error=TtsClientError("bad gateway", status_code=502)
        )
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 502

    def test_tts_error_504_maps_to_504(self) -> None:
        mock_client = MockTtsClient(
            error=TtsClientError("timeout", status_code=504)
        )
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 504

    def test_empty_pcm_maps_to_502(self) -> None:
        mock_client = MockTtsClient(pcm=b"")
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 502

    def test_unaligned_pcm_maps_to_502(self) -> None:
        mock_client = MockTtsClient(pcm=b"\x00\x01\x02")
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 502
