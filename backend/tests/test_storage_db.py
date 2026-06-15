import os
import uuid
from pathlib import Path

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test_key")

from app.storage import db as storage_db
from app.storage.db import CREATE_TABLE_SQL, Database, get_database


def _make_db() -> Database:
    return Database(":memory:")


def _create_one(
    db: Database,
    text_excerpt: str = "Hello world.",
    char_count: int = 12,
    voice: str = "Puck",
    status: str = "completed",
    **kwargs: object,
) -> dict:
    return db.create(
        text_excerpt=text_excerpt,
        char_count=char_count,
        voice=voice,
        format=kwargs.pop("format", "wav"),
        audio_path=kwargs.pop("audio_path", "data/audio/test.wav"),
        status=status,
        **kwargs,
    )


class TestSchema:
    def test_create_table_sql_contains_all_columns(self) -> None:
        expected = {
            "id",
            "created_at",
            "text_excerpt",
            "char_count",
            "source",
            "voice",
            "pacing",
            "style",
            "accent",
            "format",
            "audio_path",
            "duration_ms",
            "status",
        }
        for col in expected:
            assert col in CREATE_TABLE_SQL


class TestCreate:
    def test_create_returns_dict_with_all_fields(self) -> None:
        db = _make_db()
        record = _create_one(db, text_excerpt="Hello", char_count=5)

        assert record["id"]
        assert record["created_at"]
        assert record["text_excerpt"] == "Hello"
        assert record["char_count"] == 5
        assert record["source"] == "text"
        assert record["voice"] == "Puck"
        assert record["format"] == "wav"
        assert record["audio_path"] == "data/audio/test.wav"
        assert record["status"] == "completed"
        assert record["pacing"] is None
        assert record["style"] is None
        assert record["accent"] is None
        assert record["duration_ms"] is None

    def test_create_with_all_optional_fields(self) -> None:
        db = _make_db()
        record = _create_one(
            db,
            text_excerpt="Test",
            char_count=4,
            voice="Zephyr",
            source="md",
            pacing="slow",
            style="narrative",
            accent="british",
            duration_ms=1234,
            status="error",
        )

        assert record["source"] == "md"
        assert record["pacing"] == "slow"
        assert record["style"] == "narrative"
        assert record["accent"] == "british"
        assert record["duration_ms"] == 1234
        assert record["status"] == "error"

    def test_source_defaults_to_text(self) -> None:
        db = _make_db()
        record = _create_one(db)
        assert record["source"] == "text"

    def test_each_create_generates_unique_id(self) -> None:
        db = _make_db()
        r1 = _create_one(db)
        r2 = _create_one(db)
        assert r1["id"] != r2["id"]

    def test_created_at_is_iso_format(self) -> None:
        db = _make_db()
        record = _create_one(db)
        created_at = record["created_at"]
        assert "T" in created_at
        assert created_at.endswith("+00:00") or "Z" in created_at

    def test_custom_record_id_is_preserved(self) -> None:
        db = _make_db()
        custom_id = "my-custom-id-123"
        record = _create_one(db, record_id=custom_id)
        assert record["id"] == custom_id

    def test_custom_record_id_respects_default_uuid_when_omitted(self) -> None:
        db = _make_db()
        record = _create_one(db)
        uuid.UUID(record["id"])

    def test_duplicate_record_id_raises(self) -> None:
        db = _make_db()
        _create_one(db, record_id="dup-id")
        with pytest.raises(Exception):
            _create_one(db, record_id="dup-id")


class TestListItems:
    def test_empty_list_returns_zero_total(self) -> None:
        db = _make_db()
        result = db.list_items()
        assert result == {
            "items": [],
            "total": 0,
            "limit": 50,
            "offset": 0,
            "has_more": False,
        }

    def test_list_returns_all_items_when_within_limit(self) -> None:
        db = _make_db()
        _create_one(db, text_excerpt="A")
        _create_one(db, text_excerpt="B")
        _create_one(db, text_excerpt="C")

        result = db.list_items(limit=10, offset=0)
        assert result["total"] == 3
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert result["has_more"] is False
        assert len(result["items"]) == 3

    def test_list_respects_limit(self) -> None:
        db = _make_db()
        for i in range(5):
            _create_one(db, text_excerpt=f"Entry {i}")

        result = db.list_items(limit=2, offset=0)
        assert result["total"] == 5
        assert result["limit"] == 2
        assert result["offset"] == 0
        assert result["has_more"] is True
        assert len(result["items"]) == 2

    def test_list_respects_offset(self) -> None:
        db = _make_db()
        for i in range(5):
            _create_one(db, text_excerpt=f"Entry {i}")

        result = db.list_items(limit=2, offset=2)
        assert result["total"] == 5
        assert result["limit"] == 2
        assert result["offset"] == 2
        assert result["has_more"] is True
        assert len(result["items"]) == 2

    def test_list_last_page_has_no_more(self) -> None:
        db = _make_db()
        for i in range(5):
            _create_one(db, text_excerpt=f"Entry {i}")

        result = db.list_items(limit=2, offset=4)
        assert result["total"] == 5
        assert result["offset"] == 4
        assert result["has_more"] is False
        assert len(result["items"]) == 1

    def test_list_offset_beyond_total_returns_empty(self) -> None:
        db = _make_db()
        _create_one(db, text_excerpt="Only one")

        result = db.list_items(limit=10, offset=10)
        assert result["total"] == 1
        assert result["has_more"] is False
        assert result["items"] == []

    def test_list_order_is_created_at_descending(self) -> None:
        db = _make_db()
        r1 = _create_one(db, text_excerpt="First")
        r2 = _create_one(db, text_excerpt="Second")
        r3 = _create_one(db, text_excerpt="Third")

        result = db.list_items(limit=10, offset=0)
        items = result["items"]
        assert len(items) == 3
        assert items[0]["id"] == r3["id"]
        assert items[1]["id"] == r2["id"]
        assert items[2]["id"] == r1["id"]

    def test_list_order_uses_newer_row_when_created_at_ties(self) -> None:
        db = _make_db()
        r1 = _create_one(db, text_excerpt="First")
        r2 = _create_one(db, text_excerpt="Second")
        same_time = "2026-06-15T00:00:00+00:00"
        db.conn.execute("UPDATE syntheses SET created_at = ?", (same_time,))
        db.conn.commit()

        result = db.list_items(limit=10, offset=0)
        items = result["items"]
        assert items[0]["id"] == r2["id"]
        assert items[1]["id"] == r1["id"]

    def test_limit_clamped_to_minimum_1(self) -> None:
        db = _make_db()
        _create_one(db)
        result = db.list_items(limit=0, offset=0)
        assert result["limit"] == 1
        assert len(result["items"]) == 1

    def test_limit_clamped_to_maximum_200(self) -> None:
        db = _make_db()
        result = db.list_items(limit=500, offset=0)
        assert result["limit"] == 200

    def test_negative_offset_treated_as_zero(self) -> None:
        db = _make_db()
        _create_one(db)
        result = db.list_items(limit=10, offset=-5)
        assert result["offset"] == 0
        assert len(result["items"]) == 1


class TestGet:
    def test_get_returns_record_when_exists(self) -> None:
        db = _make_db()
        created = _create_one(db, text_excerpt="Find me")
        found = db.get(created["id"])
        assert found is not None
        assert found["id"] == created["id"]
        assert found["text_excerpt"] == "Find me"

    def test_get_returns_none_for_missing_id(self) -> None:
        db = _make_db()
        result = db.get("non-existent-id")
        assert result is None


class TestDelete:
    def test_delete_removes_record(self) -> None:
        db = _make_db()
        created = _create_one(db, text_excerpt="Delete me")
        assert db.get(created["id"]) is not None

        deleted = db.delete(created["id"])
        assert deleted is True
        assert db.get(created["id"]) is None

    def test_delete_returns_false_for_missing_id(self) -> None:
        db = _make_db()
        result = db.delete("non-existent-id")
        assert result is False

    def test_delete_only_removes_target_record(self) -> None:
        db = _make_db()
        r1 = _create_one(db, text_excerpt="Keep me")
        r2 = _create_one(db, text_excerpt="Delete me")

        db.delete(r2["id"])
        assert db.get(r1["id"]) is not None
        assert db.get(r2["id"]) is None


class TestIntegration:
    def test_full_crud_flow(self) -> None:
        db = _make_db()

        r1 = _create_one(db, text_excerpt="A")
        r2 = _create_one(db, text_excerpt="B")
        r3 = _create_one(db, text_excerpt="C")

        result = db.list_items(limit=10, offset=0)
        assert result["total"] == 3

        assert db.get(r2["id"]) is not None
        assert db.delete(r2["id"]) is True

        result = db.list_items(limit=10, offset=0)
        assert result["total"] == 2

        assert db.get(r2["id"]) is None
        assert db.get(r1["id"]) is not None
        assert db.get(r3["id"]) is not None


class TestDefaultDatabase:
    def test_get_database_is_lazy_singleton(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        original = storage_db._default_db
        try:
            monkeypatch.setattr(storage_db.settings, "DATA_DIR", str(tmp_path))
            storage_db._default_db = None
            first = get_database()
            second = get_database()
            assert first is second
            assert first.db_path == str(tmp_path / "app.sqlite")
        finally:
            if storage_db._default_db is not None:
                storage_db._default_db.close()
            storage_db._default_db = original
