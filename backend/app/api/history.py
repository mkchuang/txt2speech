"""GET /api/history?limit=50&offset=0 — paginated history list
DELETE /api/history/{id} — delete single history item (file + DB row)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.storage.db import Database, get_database
from app.storage.files import delete_audio

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_api_item(db_row: dict) -> dict:
    return {
        "id": db_row["id"],
        "created_at": db_row["created_at"],
        "text_excerpt": db_row["text_excerpt"],
        "char_count": db_row["char_count"],
        "source": db_row["source"],
        "voice": db_row["voice"],
        "pacing": db_row["pacing"],
        "style": db_row["style"],
        "accent": db_row["accent"],
        "format": db_row["format"],
        "duration_ms": db_row["duration_ms"],
        "status": db_row["status"],
        "audio_url": f"/api/audio/{db_row['id']}",
    }


@router.get("/api/history")
async def list_history(
    limit: int = 50,
    offset: int = 0,
    db: Database = Depends(get_database),
) -> dict:
    result = db.list_items(limit=limit, offset=offset)
    result["items"] = [_to_api_item(item) for item in result["items"]]
    return result


@router.delete("/api/history/{item_id}")
async def delete_history_item(
    item_id: str,
    db: Database = Depends(get_database),
) -> dict:
    record = db.get(item_id)
    if record is None:
        raise HTTPException(status_code=404, detail="history item not found")

    delete_audio(item_id)

    db.delete(item_id)

    logger.info("Deleted history item id=%s", item_id)

    return {"id": item_id, "deleted": True}
