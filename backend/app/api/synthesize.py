"""POST /api/synthesize — chunked synthesis with persistence.

Returns JSON:
    {id, created_at, metadata, audio_url=/api/audio/{id}}

On failure records status=error in DB.
"""

import logging
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.audio.pcm import PcmAudioError, concat_pcm_blocks, pcm_to_wav_bytes
from app.config import settings
from app.storage.db import Database, get_database
from app.storage.files import delete_audio, resolve_audio_path, save_audio
from app.tts.chunker import ChunkingError, chunk_transcript
from app.tts.client import GeminiTtsClient, TtsClientError
from app.tts.prompt import build_prompt

logger = logging.getLogger(__name__)

router = APIRouter()

TEXT_EXCERPT_MAX_LEN = 200


class SynthesizeRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, description="Transcript text to synthesize"
    )
    voice: str = Field(
        ..., min_length=1, description="Voice name (e.g. Puck, Zephyr)"
    )
    style: str = Field(default="", description="Delivery style")
    pacing: str = Field(default="", description="Delivery pacing")
    accent: str = Field(default="", description="Pronunciation accent")

    @field_validator("text", "voice")
    @classmethod
    def reject_blank_required_fields(cls, value: str, info: ValidationInfo) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        if info.field_name == "voice":
            return stripped
        return value


def get_tts_client() -> GeminiTtsClient:
    return GeminiTtsClient(api_key=settings.GEMINI_API_KEY)


def get_db() -> Database:
    return get_database()


def _resolve_prompt_overhead_tokens(
    tts_client: GeminiTtsClient,
    request: SynthesizeRequest,
) -> int | None:
    count_tokens = getattr(tts_client, "count_tokens", None)
    if not callable(count_tokens):
        return None

    try:
        return count_tokens(
            build_prompt(
                transcript="",
                style=request.style,
                pacing=request.pacing,
                accent=request.accent,
                voice=request.voice,
            )
        )
    except Exception as e:
        logger.warning(
            "Gemini count_tokens unavailable, using heuristic estimation: %s",
            e,
        )
        return None


def _chunk_request(
    request: SynthesizeRequest,
    prompt_overhead_tokens: int | None,
) -> list[str]:
    return chunk_transcript(
        request.text,
        prompt_overhead_tokens=prompt_overhead_tokens,
        style=request.style,
        pacing=request.pacing,
        accent=request.accent,
        voice=request.voice,
    )


def _text_excerpt(text: str) -> str:
    if len(text) <= TEXT_EXCERPT_MAX_LEN:
        return text
    return text[:TEXT_EXCERPT_MAX_LEN]


def _build_metadata(request: SynthesizeRequest) -> dict:
    return {
        "text_excerpt": _text_excerpt(request.text),
        "char_count": len(request.text),
        "voice": request.voice,
        "pacing": request.pacing,
        "style": request.style,
        "accent": request.accent,
    }


def _record_error(
    db: Database,
    record_id: str,
    request: SynthesizeRequest,
) -> None:
    try:
        db.create(
            record_id=record_id,
            text_excerpt=_text_excerpt(request.text),
            char_count=len(request.text),
            voice=request.voice,
            format="wav",
            audio_path=str(resolve_audio_path(record_id)),
            status="error",
            pacing=request.pacing or None,
            style=request.style or None,
            accent=request.accent or None,
        )
    except Exception:
        logger.exception("Failed to record error synthesis status id=%s", record_id)


def _error_response(record_id: str, detail: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        content={"id": record_id, "detail": detail},
        status_code=status_code,
    )


@router.post("/api/synthesize", response_model=None)
async def synthesize(
    request: SynthesizeRequest,
    tts_client: GeminiTtsClient = Depends(get_tts_client),
    db: Database = Depends(get_db),
) -> dict | JSONResponse:
    record_id = str(uuid.uuid4())

    prompt_overhead_tokens = _resolve_prompt_overhead_tokens(
        tts_client,
        request,
    )

    try:
        chunks = _chunk_request(
            request,
            prompt_overhead_tokens,
        )
    except ChunkingError as e:
        logger.error("Chunking error: %s", e)
        _record_error(db, record_id, request)
        return _error_response(record_id, str(e), 422)

    if not chunks:
        _record_error(db, record_id, request)
        return _error_response(
            record_id,
            "transcript is empty after chunking",
            422,
        )

    try:
        pcm_blocks: list[bytes] = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = build_prompt(
                transcript=chunk,
                style=request.style,
                pacing=request.pacing,
                accent=request.accent,
                voice=request.voice,
            )
            logger.info(
                "Synthesizing chunk %d/%d (%d chars)",
                i + 1,
                len(chunks),
                len(chunk),
            )
            pcm_blocks.append(
                tts_client.generate_content(chunk_prompt, request.voice)
            )

        if len(pcm_blocks) == 1:
            pcm = pcm_blocks[0]
        else:
            pcm = concat_pcm_blocks(pcm_blocks)
    except TtsClientError as e:
        logger.error("TTS client error: %s", e)
        _record_error(db, record_id, request)
        return _error_response(record_id, str(e), e.status_code)
    except PcmAudioError as e:
        logger.error("Audio processing error: %s", e)
        _record_error(db, record_id, request)
        return _error_response(record_id, str(e), 502)

    try:
        wav_bytes = pcm_to_wav_bytes(pcm)
    except PcmAudioError as e:
        logger.error("PCM conversion error: %s", e)
        _record_error(db, record_id, request)
        return _error_response(record_id, str(e), 502)

    try:
        audio_path = save_audio(record_id, wav_bytes)
    except Exception as e:
        logger.error("Failed to save audio file: %s", e)
        _record_error(db, record_id, request)
        return _error_response(record_id, "failed to save audio file", 500)

    try:
        record = db.create(
            record_id=record_id,
            text_excerpt=_text_excerpt(request.text),
            char_count=len(request.text),
            voice=request.voice,
            format="wav",
            audio_path=str(audio_path),
            status="completed",
            pacing=request.pacing or None,
            style=request.style or None,
            accent=request.accent or None,
        )
    except Exception as e:
        logger.exception("Failed to record synthesis metadata id=%s", record_id)
        if not delete_audio(record_id):
            logger.warning("Failed to clean orphan audio file id=%s", record_id)
        return _error_response(record_id, "failed to record synthesis metadata", 500)

    logger.info(
        "Synthesis completed id=%s chunks=%d size=%d",
        record_id,
        len(chunks),
        len(wav_bytes),
    )

    return {
        "id": record["id"],
        "created_at": record["created_at"],
        "metadata": _build_metadata(request),
        "audio_url": f"/api/audio/{record['id']}",
    }
