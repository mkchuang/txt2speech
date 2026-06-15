"""GET /api/audio/{id} — serve audio file with Range support and download option."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import FileResponse

from app.storage.db import Database, get_database
from app.storage.files import resolve_audio_path

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/audio/{item_id}")
async def get_audio(
    item_id: str,
    download: bool = Query(False),
    db: Database = Depends(get_database),
) -> FileResponse:
    record = db.get(item_id)
    if record is None:
        raise HTTPException(status_code=404, detail="audio not found")

    path = resolve_audio_path(item_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="audio file not found")

    media_type = "audio/wav"

    if download:
        return FileResponse(
            path,
            media_type=media_type,
            filename=f"{item_id}.wav",
        )

    return FileResponse(path, media_type=media_type)
