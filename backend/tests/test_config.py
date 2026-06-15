import os
from pathlib import Path
from unittest import mock

import pytest
from pydantic import ValidationError

os.environ.setdefault("GEMINI_API_KEY", "test_key")

from app.config import Settings  # noqa: E402


class TestSettingsDefaults:
    def test_data_dir_default(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            s = Settings()
            assert s.DATA_DIR == "data"

    def test_cors_origins_default(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            s = Settings()
            assert s.CORS_ORIGINS == "http://localhost:3000"

    def test_missing_api_key_raises(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_unknown_environment_field_is_ignored(self) -> None:
        with mock.patch.dict(
            os.environ, {"GEMINI_API_KEY": "test_key", "UNKNOWN_FIELD": "value"}, clear=True
        ):
            s = Settings()
            assert not hasattr(s, "UNKNOWN_FIELD")

    def test_extra_init_field_raises(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            with pytest.raises(ValidationError):
                Settings(UNKNOWN_FIELD="value")  # type: ignore[call-arg]


class TestSettingsProperties:
    def test_data_dir_path_returns_path(self) -> None:
        with mock.patch.dict(
            os.environ, {"GEMINI_API_KEY": "test_key", "DATA_DIR": "/tmp/my_data"}, clear=True
        ):
            s = Settings()
            assert s.data_dir_path == Path("/tmp/my_data")
            assert isinstance(s.data_dir_path, Path)

    def test_data_dir_path_relative(self) -> None:
        with mock.patch.dict(
            os.environ, {"GEMINI_API_KEY": "test_key", "DATA_DIR": "data"}, clear=True
        ):
            s = Settings()
            assert s.data_dir_path == Path("data")

    def test_cors_origins_list_single(self) -> None:
        with mock.patch.dict(
            os.environ, {"GEMINI_API_KEY": "test_key", "CORS_ORIGINS": "http://localhost:3000"},
            clear=True,
        ):
            s = Settings()
            assert s.cors_origins_list == ["http://localhost:3000"]

    def test_cors_origins_list_multiple(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test_key",
                "CORS_ORIGINS": "http://localhost:3000, https://example.com",
            },
            clear=True,
        ):
            s = Settings()
            assert s.cors_origins_list == ["http://localhost:3000", "https://example.com"]

    def test_cors_origins_list_strips_whitespace(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "test_key",
                "CORS_ORIGINS": " http://localhost:3000 , https://example.com ",
            },
            clear=True,
        ):
            s = Settings()
            assert s.cors_origins_list == ["http://localhost:3000", "https://example.com"]


class TestSettingsLoad:
    def test_loads_from_environment(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "env_key",
                "DATA_DIR": "my_data_dir",
                "CORS_ORIGINS": "http://a.com,http://b.com",
            },
            clear=True,
        ):
            s = Settings()
            assert s.GEMINI_API_KEY == "env_key"
            assert s.DATA_DIR == "my_data_dir"
            assert s.CORS_ORIGINS == "http://a.com,http://b.com"
