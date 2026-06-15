import logging
import os
import re
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

_VALID_ID_RE = re.compile(r"^[A-Za-z0-9\-_]+$")

FORBIDDEN_COMPONENTS = ("..",)


def _validate_audio_id(audio_id: str) -> None:
    if not audio_id:
        raise ValueError("audio_id must not be empty")

    if "\x00" in audio_id:
        raise ValueError("audio_id contains null byte")

    if audio_id.startswith("/") or audio_id.startswith("\\"):
        raise ValueError(f"audio_id must not be an absolute path: {audio_id!r}")

    for component in audio_id.replace("\\", "/").split("/"):
        if component in FORBIDDEN_COMPONENTS:
            raise ValueError(
                f"audio_id contains forbidden path component: {audio_id!r}"
            )

    if not _VALID_ID_RE.match(audio_id):
        raise ValueError(
            f"audio_id contains invalid characters: {audio_id!r}"
        )


def _audio_dir() -> Path:
    return settings.data_dir_path / "audio"


def resolve_audio_path(audio_id: str) -> Path:
    _validate_audio_id(audio_id)
    audio_dir = _audio_dir()
    path = audio_dir / f"{audio_id}.wav"

    try:
        path.resolve(strict=False).relative_to(
            audio_dir.resolve(strict=False)
        )
    except ValueError as exc:
        raise ValueError(
            f"audio path escapes storage directory: {audio_id!r}"
        ) from exc

    return path


def save_audio(audio_id: str, audio_bytes: bytes) -> Path:
    path = resolve_audio_path(audio_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio_bytes)
    logger.info(
        "Saved audio file id=%s path=%s size=%d",
        audio_id,
        path,
        len(audio_bytes),
    )
    return path


def delete_audio(audio_id: str) -> bool:
    path = resolve_audio_path(audio_id)
    try:
        os.remove(path)
    except FileNotFoundError:
        return False
    logger.info("Deleted audio file id=%s path=%s", audio_id, path)
    return True
