import os
from pathlib import Path

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test_key")

from app.storage import files as storage_files


class TestValidateAudioId:
    """Normal id acceptance."""

    @pytest.mark.parametrize(
        "audio_id",
        [
            "550e8400-e29b-41d4-a716-446655440000",
            "abc123",
            "test_id",
            "a",
            "a-b_c",
        ],
    )
    def test_valid_ids_are_accepted(self, audio_id: str) -> None:
        storage_files._validate_audio_id(audio_id)

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            storage_files._validate_audio_id("")

    def test_dotdot_component_raises(self) -> None:
        with pytest.raises(ValueError, match="forbidden path component"):
            storage_files._validate_audio_id("../etc/passwd")

    def test_dotdot_in_middle_raises(self) -> None:
        with pytest.raises(ValueError, match="forbidden path component"):
            storage_files._validate_audio_id("foo/../bar")

    def test_trailing_dotdot_raises(self) -> None:
        with pytest.raises(ValueError, match="forbidden path component"):
            storage_files._validate_audio_id("foo/..")

    def test_absolute_unix_path_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be an absolute path"):
            storage_files._validate_audio_id("/etc/passwd")

    def test_absolute_windows_path_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be an absolute path"):
            storage_files._validate_audio_id("\\windows\\system32")

    def test_null_byte_raises(self) -> None:
        with pytest.raises(ValueError, match="null byte"):
            storage_files._validate_audio_id("good\x00evil")

    def test_invalid_characters_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid characters"):
            storage_files._validate_audio_id("foo/bar/baz")

    def test_dot_only_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid characters"):
            storage_files._validate_audio_id(".")

    def test_empty_with_slash_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be an absolute path"):
            storage_files._validate_audio_id("/")

    def test_space_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid characters"):
            storage_files._validate_audio_id("my id")

    def test_dot_inside_id_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid characters"):
            storage_files._validate_audio_id("file.wav")


class TestResolveAudioPath:
    def test_resolves_to_audio_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        path = storage_files.resolve_audio_path("abc123")
        expected = tmp_path / "audio" / "abc123.wav"
        assert path == expected

    def test_resolved_path_stays_under_audio_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        path = storage_files.resolve_audio_path("safe-id")
        path.resolve(strict=False).relative_to(
            (tmp_path / "audio").resolve(strict=False)
        )

    def test_bad_id_propagates_to_resolve(self) -> None:
        with pytest.raises(ValueError):
            storage_files.resolve_audio_path("../evil")


class TestSaveAndDeleteAudio:
    def test_save_and_read_back(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        audio_id = "550e8400-e29b-41d4-a716-446655440000"
        audio_bytes = b"\x00\x01\x02\x03"

        path = storage_files.save_audio(audio_id, audio_bytes)
        assert path.exists()
        assert path.read_bytes() == audio_bytes
        expected = tmp_path / "audio" / f"{audio_id}.wav"
        assert path == expected

    def test_save_overwrites_existing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        audio_id = "test-overwrite"
        v1 = b"version1"
        v2 = b"version2"

        storage_files.save_audio(audio_id, v1)
        storage_files.save_audio(audio_id, v2)
        path = storage_files.resolve_audio_path(audio_id)
        assert path.read_bytes() == v2

    def test_save_creates_audio_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        audio_dir = tmp_path / "audio"
        assert not audio_dir.exists()

        storage_files.save_audio("test-1", b"data")
        assert audio_dir.is_dir()

    def test_delete_existing_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        storage_files.save_audio("to-delete", b"bye")
        path = storage_files.resolve_audio_path("to-delete")
        assert path.exists()

        result = storage_files.delete_audio("to-delete")
        assert result is True
        assert not path.exists()

    def test_delete_missing_file_returns_false(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        result = storage_files.delete_audio("non-existent")
        assert result is False

    def test_delete_bad_id_raises(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        with pytest.raises(ValueError):
            storage_files.delete_audio("../evil")

    def test_delete_is_idempotent_for_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        storage_files.save_audio("idempotent", b"once")
        storage_files.delete_audio("idempotent")
        result = storage_files.delete_audio("idempotent")
        assert result is False

    def test_save_bad_id_raises(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(storage_files.settings, "DATA_DIR", str(tmp_path))
        with pytest.raises(ValueError):
            storage_files.save_audio("../bad", b"x")
