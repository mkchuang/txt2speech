import io
import os
import wave
from collections.abc import Callable

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
        assert "Hello world." in call["prompt"]

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


class ChunkingMockTtsClient:
    """Mock client with count_tokens support for multi-chunk tests."""

    def __init__(
        self,
        pcm: bytes | None = None,
        error: Exception | None = None,
        pcm_factory: Callable[[int], bytes] | None = None,
        count_tokens_error_after: int | None = None,
    ) -> None:
        self.pcm = pcm if pcm is not None else _make_pcm()
        self.error = error
        self.pcm_factory = pcm_factory
        self.count_tokens_error_after = count_tokens_error_after
        self.generate_content_calls: list[dict[str, str]] = []
        self.generated_pcm_blocks: list[bytes] = []
        self.count_tokens_calls: list[str] = []

    def generate_content(self, prompt: str, voice_name: str) -> bytes:
        self.generate_content_calls.append(
            {"prompt": prompt, "voice_name": voice_name}
        )
        if self.error:
            raise self.error
        if self.pcm_factory is not None:
            pcm = self.pcm_factory(len(self.generate_content_calls) - 1)
        else:
            pcm = self.pcm
        self.generated_pcm_blocks.append(pcm)
        return pcm

    def count_tokens(self, prompt: str) -> int:
        self.count_tokens_calls.append(prompt)
        if (
            self.count_tokens_error_after is not None
            and len(self.count_tokens_calls) > self.count_tokens_error_after
        ):
            raise RuntimeError("count_tokens unavailable")
        return max(1, len(prompt) // 4)


class TestSynthesizeLongChunking:
    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def test_long_text_returns_200_audio_wav(self) -> None:
        long_text = "Hello. " * 800
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_long_text_splits_into_multiple_chunks(self) -> None:
        long_text = "Practice. " * 1000
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        assert len(mock_client.generate_content_calls) > 1

    def test_long_text_total_frames_equal_sum_of_block_frames(self) -> None:
        per_chunk_frames = 480
        mock_client = ChunkingMockTtsClient(pcm=_make_pcm(per_chunk_frames))
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "Sentence. " * 500

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        n_chunks = len(mock_client.generate_content_calls)
        assert n_chunks > 1
        with wave.open(io.BytesIO(response.content), "rb") as wf:
            assert wf.getnframes() == n_chunks * per_chunk_frames

    def test_long_text_concat_preserves_chunk_order_bytes(self) -> None:
        def make_chunk_pcm(index: int) -> bytes:
            return bytes((index + offset) % 256 for offset in range(96 * FRAME_SIZE))

        mock_client = ChunkingMockTtsClient(pcm_factory=make_chunk_pcm)
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Ordered chunk. " * 700, "voice": "Puck"},
        )

        assert response.status_code == 200
        assert len(mock_client.generated_pcm_blocks) > 1
        with wave.open(io.BytesIO(response.content), "rb") as wf:
            assert wf.readframes(wf.getnframes()) == b"".join(
                mock_client.generated_pcm_blocks
            )

    def test_long_text_wav_frame_aligned(self) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "A. " * 2000

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        with wave.open(io.BytesIO(response.content), "rb") as wf:
            total_bytes = wf.getnframes() * wf.getsampwidth() * wf.getnchannels()
            assert total_bytes % FRAME_SIZE == 0

    def test_count_tokens_is_used_for_prompt_overhead(self) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={
                "text": "Short text. " * 100,
                "voice": "Puck",
                "style": "dramatic",
            },
        )

        assert response.status_code == 200
        assert len(mock_client.count_tokens_calls) >= 1
        assert mock_client.count_tokens_calls[0] != ""

    def test_count_tokens_is_not_called_per_candidate_for_long_no_space_text(
        self,
    ) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "a" * 5000, "voice": "Puck"},
        )

        assert response.status_code == 200
        assert len(mock_client.count_tokens_calls) == 1
        assert len(mock_client.generate_content_calls) > 1

    def test_count_tokens_overhead_failure_falls_back_to_heuristic(self) -> None:
        mock_client = ChunkingMockTtsClient(count_tokens_error_after=0)
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Fallback chunking. " * 300, "voice": "Puck"},
        )

        assert response.status_code == 200
        assert len(mock_client.count_tokens_calls) == 1
        assert len(mock_client.generate_content_calls) > 0

    def test_long_text_with_style_pacing_accent_each_chunk_has_params(self) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "Practice makes progress. " * 400

        response = client.post(
            "/api/synthesize",
            json={
                "text": long_text,
                "voice": "Zephyr",
                "style": "dramatic",
                "pacing": "slow",
                "accent": "British",
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert len(mock_client.generate_content_calls) > 0
        for call in mock_client.generate_content_calls:
            assert "dramatic" in call["prompt"]
            assert "slow" in call["prompt"]
            assert "British" in call["prompt"]

    def test_single_chunk_preserves_m2_behavior(self) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert len(mock_client.generate_content_calls) == 1
        assert "Hello world." in mock_client.generate_content_calls[0]["prompt"]

    def test_long_text_chunk_error_returned(self) -> None:
        mock_client = ChunkingMockTtsClient(
            error=TtsClientError("chunk failed", status_code=502)
        )
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "Sentence. " * 500
        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 502
