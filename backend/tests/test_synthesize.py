import atexit
import os
import shutil
import tempfile
import wave
from collections.abc import Callable
from pathlib import Path

from fastapi.testclient import TestClient

_temp_data_dir = Path(
    tempfile.mkdtemp(prefix="test_synthesize_data_")
)
atexit.register(
    lambda d=_temp_data_dir: shutil.rmtree(str(d), ignore_errors=True)
)

os.environ.setdefault("GEMINI_API_KEY", "test_key")
os.environ["DATA_DIR"] = str(_temp_data_dir)

from app.main import app  # noqa: E402
from app.api.synthesize import get_db, get_tts_client  # noqa: E402
from app.config import settings  # noqa: E402
from app.storage.db import Database  # noqa: E402
from app.tts.client import TtsClientError  # noqa: E402

settings.DATA_DIR = str(_temp_data_dir)

client = TestClient(app)

FRAME_SIZE = 2


def _make_pcm(frame_count: int = 480) -> bytes:
    return bytes(i % 256 for i in range(frame_count * FRAME_SIZE))


def _make_db() -> Database:
    return Database(":memory:")


def _read_wav(path: str) -> tuple[bytes, int, int, int]:
    with wave.open(path, "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        return frames, wf.getnchannels(), wf.getsampwidth(), wf.getframerate()


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


class TestSynthesizeValidation:
    """Pydantic validation — route handler is NOT reached, no DB needed."""

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


class TestSynthesizeSuccess:
    def setup_method(self) -> None:
        self.db = _make_db()
        app.dependency_overrides[get_db] = lambda: self.db

    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def test_returns_json_with_correct_content_type(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world. This is a test.", "voice": "Puck"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_response_has_id_created_at_metadata_audio_url(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "created_at" in data
        assert "metadata" in data
        assert "audio_url" in data
        assert data["audio_url"] == f"/api/audio/{data['id']}"

    def test_metadata_contains_all_fields(self) -> None:
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
        meta = response.json()["metadata"]
        assert meta["text_excerpt"] == "Hello world."
        assert meta["char_count"] == 12
        assert meta["voice"] == "Zephyr"
        assert meta["pacing"] == "slow"
        assert meta["style"] == "dramatic"
        assert meta["accent"] == "British"

    def test_audio_file_saved_to_disk(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 200
        record_id = response.json()["id"]
        audio_path = _temp_data_dir / "audio" / f"{record_id}.wav"
        assert audio_path.exists()

    def test_audio_file_is_valid_wav(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 200
        record_id = response.json()["id"]
        audio_path = _temp_data_dir / "audio" / f"{record_id}.wav"
        frames, nch, sw, rate = _read_wav(str(audio_path))
        assert nch == 1
        assert sw == 2
        assert rate == 24000
        assert len(frames) > 0

    def test_db_record_created_with_status_completed(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 200
        record_id = response.json()["id"]
        record = self.db.get(record_id)
        assert record is not None
        assert record["status"] == "completed"
        assert record["text_excerpt"] == "Hello world."
        assert record["char_count"] == 12
        assert record["voice"] == "Puck"
        assert record["format"] == "wav"

    def test_db_record_audio_path_matches_saved_file(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 200
        record_id = response.json()["id"]
        record = self.db.get(record_id)
        assert record is not None
        audio_path = Path(record["audio_path"])
        assert audio_path == _temp_data_dir / "audio" / f"{record_id}.wav"
        assert audio_path.exists()

    def test_db_record_has_null_for_empty_style_pacing_accent(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Test.", "voice": "Puck"},
        )

        assert response.status_code == 200
        record = self.db.get(response.json()["id"])
        assert record["pacing"] is None
        assert record["style"] is None
        assert record["accent"] is None

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


class TestSynthesizeErrorRecording:
    def setup_method(self) -> None:
        self.db = _make_db()
        app.dependency_overrides[get_db] = lambda: self.db

    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def test_tts_error_502_records_status_error(self) -> None:
        mock_client = MockTtsClient(
            error=TtsClientError("bad gateway", status_code=502)
        )
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 502
        records = self.db.list_items(limit=1)
        assert records["total"] >= 1
        assert records["items"][0]["status"] == "error"
        assert records["items"][0]["text_excerpt"] == "Hello world."
        assert records["items"][0]["voice"] == "Puck"

    def test_tts_error_504_records_status_error(self) -> None:
        mock_client = MockTtsClient(
            error=TtsClientError("timeout", status_code=504)
        )
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 504
        record = self.db.list_items(limit=1)["items"][0]
        assert record["status"] == "error"

    def test_empty_pcm_records_status_error(self) -> None:
        mock_client = MockTtsClient(pcm=b"")
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 502
        record = self.db.list_items(limit=1)["items"][0]
        assert record["status"] == "error"

    def test_unaligned_pcm_records_status_error(self) -> None:
        mock_client = MockTtsClient(pcm=b"\x00\x01\x02")
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 502
        record = self.db.list_items(limit=1)["items"][0]
        assert record["status"] == "error"

    def test_error_record_response_contains_id(self) -> None:
        mock_client = MockTtsClient(
            error=TtsClientError("bad gateway", status_code=502)
        )
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 502
        data = response.json()
        assert "id" in data
        record = self.db.get(data["id"])
        assert record is not None
        assert record["voice"] == "Puck"
        assert record["char_count"] == 12
        assert record["text_excerpt"] == "Hello world."


class ChunkingMockTtsClient:
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
    def setup_method(self) -> None:
        self.db = _make_db()
        app.dependency_overrides[get_db] = lambda: self.db

    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def _get_audio_path(self, record_id: str) -> Path:
        return _temp_data_dir / "audio" / f"{record_id}.wav"

    def test_long_text_returns_200_json(self) -> None:
        long_text = "Hello. " * 800
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "id" in data
        assert "audio_url" in data

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
        record_id = response.json()["id"]
        frames, *_ = _read_wav(str(self._get_audio_path(record_id)))
        expected_total = n_chunks * per_chunk_frames * FRAME_SIZE
        assert len(frames) == expected_total

    def test_long_text_concat_preserves_chunk_order_bytes(self) -> None:
        def make_chunk_pcm(index: int) -> bytes:
            return bytes(
                (index + offset) % 256 for offset in range(96 * FRAME_SIZE)
            )

        mock_client = ChunkingMockTtsClient(pcm_factory=make_chunk_pcm)
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Ordered chunk. " * 700, "voice": "Puck"},
        )

        assert response.status_code == 200
        assert len(mock_client.generated_pcm_blocks) > 1
        record_id = response.json()["id"]
        frames, *_ = _read_wav(str(self._get_audio_path(record_id)))
        assert frames == b"".join(mock_client.generated_pcm_blocks)

    def test_long_text_wav_frame_aligned(self) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "A. " * 2000

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        record_id = response.json()["id"]
        with wave.open(str(self._get_audio_path(record_id)), "rb") as wf:
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
        assert response.headers["content-type"] == "application/json"
        assert len(mock_client.generate_content_calls) > 0
        for call in mock_client.generate_content_calls:
            assert "dramatic" in call["prompt"]
            assert "slow" in call["prompt"]
            assert "British" in call["prompt"]

    def test_single_chunk_creates_record_and_returns_json(self) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hello world.", "voice": "Puck"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "audio_url" in data
        record = self.db.get(data["id"])
        assert record is not None
        assert record["status"] == "completed"

    def test_long_text_db_record_has_correct_fields(self) -> None:
        mock_client = ChunkingMockTtsClient(pcm=_make_pcm(240))
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "Practice. " * 200

        response = client.post(
            "/api/synthesize",
            json={
                "text": long_text,
                "voice": "Zephyr",
                "pacing": "slow",
            },
        )

        assert response.status_code == 200
        data = response.json()
        record = self.db.get(data["id"])
        assert record is not None
        assert record["status"] == "completed"
        assert record["voice"] == "Zephyr"
        assert record["pacing"] == "slow"
        assert record["char_count"] == len(long_text)

    def test_long_text_chunk_error_returned_and_recorded(self) -> None:
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
        record = self.db.list_items(limit=1)["items"][0]
        assert record["status"] == "error"

    def test_long_text_audio_file_exists_on_disk(self) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "Audio file test. " * 300

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        record_id = response.json()["id"]
        assert self._get_audio_path(record_id).exists()

    def test_audio_url_matches_record_id(self) -> None:
        mock_client = ChunkingMockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "Consistency check. " * 300

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["audio_url"] == f"/api/audio/{data['id']}"
        record = self.db.get(data["id"])
        assert record is not None
        assert record["id"] == data["id"]


class TestSynthesizeTextExcerptTruncation:
    def setup_method(self) -> None:
        self.db = _make_db()
        app.dependency_overrides[get_db] = lambda: self.db

    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def test_long_text_is_truncated_in_excerpt(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        long_text = "x" * 300

        response = client.post(
            "/api/synthesize",
            json={"text": long_text, "voice": "Puck"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["metadata"]["text_excerpt"]) == 200
        assert data["metadata"]["char_count"] == 300
        record = self.db.get(data["id"])
        assert record["text_excerpt"] == "x" * 200

    def test_short_text_is_not_truncated(self) -> None:
        mock_client = MockTtsClient()
        app.dependency_overrides[get_tts_client] = lambda: mock_client

        response = client.post(
            "/api/synthesize",
            json={"text": "Hi.", "voice": "Puck"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["text_excerpt"] == "Hi."
        record = self.db.get(data["id"])
        assert record["text_excerpt"] == "Hi."
