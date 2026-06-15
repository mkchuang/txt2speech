import atexit
import os
import shutil
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

_temp_data_dir = Path(
    tempfile.mkdtemp(prefix="test_history_data_")
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


def _seed_record(
    db: Database,
    *,
    record_id: str | None = None,
    text_excerpt: str = "Hello world.",
    char_count: int = 12,
    voice: str = "Puck",
    status: str = "completed",
    pacing: str | None = None,
    style: str | None = None,
    accent: str | None = None,
    audio_path: str | None = None,
) -> dict:
    if audio_path is None:
        rid = record_id or "test-id"
        audio_path = str(resolve_audio_path(rid))
    return db.create(
        record_id=record_id,
        text_excerpt=text_excerpt,
        char_count=char_count,
        voice=voice,
        format="wav",
        audio_path=audio_path,
        status=status,
        pacing=pacing,
        style=style,
        accent=accent,
    )


class TestListHistory:
    def test_empty_history(self) -> None:
        db = _make_db()
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/history")
            assert response.status_code == 200
            data = response.json()
            assert data == {
                "items": [],
                "total": 0,
                "limit": 50,
                "offset": 0,
                "has_more": False,
            }
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_list_returns_items_in_desc_order(self) -> None:
        db = _make_db()
        record1 = _seed_record(db, text_excerpt="First")
        record2 = _seed_record(db, text_excerpt="Second")
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/history")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["has_more"] is False
            assert len(data["items"]) == 2
            assert data["items"][0]["id"] == record2["id"]
            assert data["items"][1]["id"] == record1["id"]
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_items_have_audio_url(self) -> None:
        db = _make_db()
        record = _seed_record(db, record_id="url-test-id")
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/history")
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1
            item = data["items"][0]
            assert item["id"] == record["id"]
            assert item["audio_url"] == f"/api/audio/{record['id']}"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_items_have_all_fields(self) -> None:
        db = _make_db()
        record = _seed_record(
            db,
            record_id="fields-test",
            text_excerpt="Test excerpt",
            char_count=42,
            voice="Zephyr",
            status="completed",
            pacing="slow",
            style="dramatic",
            accent="British",
        )
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/history")
            assert response.status_code == 200
            item = response.json()["items"][0]
            assert item["id"] == record["id"]
            assert item["created_at"] == record["created_at"]
            assert item["text_excerpt"] == "Test excerpt"
            assert item["char_count"] == 42
            assert item["source"] == "text"
            assert item["voice"] == "Zephyr"
            assert item["pacing"] == "slow"
            assert item["style"] == "dramatic"
            assert item["accent"] == "British"
            assert item["format"] == "wav"
            assert item["duration_ms"] is None
            assert item["status"] == "completed"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_custom_limit_offset(self) -> None:
        db = _make_db()
        for i in range(5):
            _seed_record(db, text_excerpt=f"Record {i}")
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/history?limit=2&offset=1")
            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 2
            assert data["offset"] == 1
            assert data["total"] == 5
            assert data["has_more"] is True
            assert len(data["items"]) == 2
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_has_more_false_on_last_page(self) -> None:
        db = _make_db()
        for i in range(3):
            _seed_record(db, text_excerpt=f"Record {i}")
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/history?limit=3&offset=0")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            assert data["has_more"] is False
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_default_params(self) -> None:
        db = _make_db()
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.get("/api/history")
            data = response.json()
            assert data["limit"] == 50
            assert data["offset"] == 0
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()


class TestDeleteHistory:
    def test_delete_removes_db_row_and_file(self) -> None:
        record_id = "delete-test-1"
        db = _make_db()
        _seed_record(db, record_id=record_id)
        audio_path = save_audio(record_id, b"dummy wav data")
        assert audio_path.exists()

        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.delete(f"/api/history/{record_id}")
            assert response.status_code == 200
            data = response.json()
            assert data == {"id": record_id, "deleted": True}

            assert db.get(record_id) is None
            assert not audio_path.exists()
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_delete_nonexistent_returns_404(self) -> None:
        db = _make_db()
        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.delete("/api/history/nonexistent-id")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "history item not found"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_delete_still_works_when_file_already_gone(self) -> None:
        record_id = "orphan-file"
        db = _make_db()
        _seed_record(db, record_id=record_id)
        path = resolve_audio_path(record_id)
        assert not path.exists()

        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.delete(f"/api/history/{record_id}")
            assert response.status_code == 200
            data = response.json()
            assert data == {"id": record_id, "deleted": True}
            assert db.get(record_id) is None
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_delete_only_targets_specified_id(self) -> None:
        id_a = "target-a"
        id_b = "target-b"
        db = _make_db()
        _seed_record(db, record_id=id_a, text_excerpt="A")
        _seed_record(db, record_id=id_b, text_excerpt="B")
        save_audio(id_a, b"audio a")
        save_audio(id_b, b"audio b")

        app.dependency_overrides[get_database] = lambda: db
        try:
            response = client.delete(f"/api/history/{id_a}")
            assert response.status_code == 200
            assert db.get(id_a) is None
            assert db.get(id_b) is not None
            assert not resolve_audio_path(id_a).exists()
            assert resolve_audio_path(id_b).exists()
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()

    def test_delete_then_get_history_excludes_deleted(self) -> None:
        record_id = "to-delete"
        db = _make_db()
        _seed_record(db, record_id=record_id, text_excerpt="Will be deleted")
        _seed_record(db, text_excerpt="Kept")
        save_audio(record_id, b"audio")

        app.dependency_overrides[get_database] = lambda: db
        try:
            client.delete(f"/api/history/{record_id}")
            response = client.get("/api/history")
            data = response.json()
            assert data["total"] == 1
            assert data["items"][0]["text_excerpt"] == "Kept"
        finally:
            app.dependency_overrides.pop(get_database, None)
            db.close()
