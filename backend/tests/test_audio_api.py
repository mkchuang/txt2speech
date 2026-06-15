import atexit
import os
import shutil
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

_temp_data_dir = Path(
    tempfile.mkdtemp(prefix="test_audio_api_data_")
)
atexit.register(
    lambda d=_temp_data_dir: shutil.rmtree(str(d), ignore_errors=True)
)

os.environ.setdefault("GEMINI_API_KEY", "test_key")
os.environ["DATA_DIR"] = str(_temp_data_dir)

from app.main import app  # noqa: E402
from app.config import settings  # noqa: E402
from app.storage.db import Database, get_database  # noqa: E402
from app.storage.files import resolve_audio_path, save_audio  # noqa: E402

settings.DATA_DIR = str(_temp_data_dir)

client = TestClient(app)


def _make_db() -> Database:
    return Database(":memory:")


def _seed_audio(
    db: Database,
    *,
    record_id: str,
    audio_bytes: bytes = b"fake wav data",
) -> None:
    db.create(
        record_id=record_id,
        text_excerpt="Test.",
        char_count=5,
        voice="Puck",
        format="wav",
        audio_path=str(resolve_audio_path(record_id)),
        status="completed",
    )
    save_audio(record_id, audio_bytes)


class TestGetAudio:
    def test_unknown_id_returns_404(self) -> None:
        db = _make_db()
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/audio/nonexistent")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "audio not found"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_returns_audio_file(self) -> None:
        db = _make_db()
        _seed_audio(db, record_id="audio-test-1", audio_bytes=b"fake pcm")
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/audio/audio-test-1")
            assert response.status_code == 200
            assert response.content == b"fake pcm"
            assert response.headers["content-type"] == "audio/wav"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_accept_ranges_header_present(self) -> None:
        db = _make_db()
        _seed_audio(db, record_id="accept-range", audio_bytes=b"data")
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/audio/accept-range")
            assert response.status_code == 200
            assert response.headers.get("accept-ranges") == "bytes"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_record_exists_but_file_missing_returns_404(self) -> None:
        db = _make_db()
        db.create(
            record_id="orphan-record",
            text_excerpt="Missing file.",
            char_count=12,
            voice="Puck",
            format="wav",
            audio_path=str(resolve_audio_path("orphan-record")),
            status="completed",
        )
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/audio/orphan-record")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "audio file not found"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_range_request_returns_206(self) -> None:
        db = _make_db()
        audio_data = bytes(range(256))
        _seed_audio(db, record_id="range-test", audio_bytes=audio_data)
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get(
                "/api/audio/range-test",
                headers={"Range": "bytes=0-127"},
            )
            assert response.status_code == 206
            assert response.content == audio_data[0:128]
            assert "content-range" in response.headers
            assert response.headers["content-range"].startswith(
                "bytes 0-127/256"
            )
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_range_request_open_end(self) -> None:
        db = _make_db()
        audio_data = bytes(range(200))
        _seed_audio(db, record_id="range-open", audio_bytes=audio_data)
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get(
                "/api/audio/range-open",
                headers={"Range": "bytes=100-"},
            )
            assert response.status_code == 206
            assert response.content == audio_data[100:]
            assert response.headers["content-range"].startswith(
                "bytes 100-199/200"
            )
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_download_sets_content_disposition(self) -> None:
        db = _make_db()
        _seed_audio(db, record_id="download-test", audio_bytes=b"download me")
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/audio/download-test?download=1")
            assert response.status_code == 200
            cd = response.headers["content-disposition"]
            assert "attachment" in cd
            assert "download-test.wav" in cd
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_download_with_range_combines_both(self) -> None:
        db = _make_db()
        audio_data = b"\x00\x01\x02\x03" * 125
        _seed_audio(db, record_id="dl-range", audio_bytes=audio_data)
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get(
                "/api/audio/dl-range?download=1",
                headers={"Range": "bytes=100-299"},
            )
            assert response.status_code == 206
            assert response.content == audio_data[100:300]
            cd = response.headers["content-disposition"]
            assert "attachment" in cd
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_non_wav_media_type(self) -> None:
        db = _make_db()
        _seed_audio(db, record_id="wav-type", audio_bytes=b"wav data")
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/audio/wav-type")
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/wav"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()
