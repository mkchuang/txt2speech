"""POST /api/synthesize — M3 chunked synthesis (temporary internal contract).

M4 will replace this endpoint to return JSON:
    {id, created_at, metadata, audio_url}
instead of raw audio/wav bytes. Frontend MUST NOT depend on this M2 shape.
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.audio.pcm import PcmAudioError, concat_pcm_blocks, pcm_to_wav_bytes
from app.config import settings
from app.tts.chunker import ChunkingError, chunk_transcript
from app.tts.client import GeminiTtsClient, TtsClientError
from app.tts.prompt import build_prompt

logger = logging.getLogger(__name__)

router = APIRouter()


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Transcript text to synthesize")
    voice: str = Field(..., min_length=1, description="Voice name (e.g. Puck, Zephyr)")
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


@router.post("/api/synthesize")
async def synthesize(
    request: SynthesizeRequest,
    tts_client: GeminiTtsClient = Depends(get_tts_client),
) -> Response:
    # --- Temporary contract: returns raw audio/wav bytes ---
    # M4 will change this to return JSON: {id, created_at, metadata, audio_url}
    # Frontend MUST NOT depend on this M2 response shape.
    # ------------------------------------------------------------

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
        return Response(content=str(e), status_code=422, media_type="text/plain")

    if not chunks:
        return Response(
            content="transcript is empty after chunking",
            status_code=422,
            media_type="text/plain",
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
            pcm_blocks.append(tts_client.generate_content(chunk_prompt, request.voice))

        if len(pcm_blocks) == 1:
            pcm = pcm_blocks[0]
        else:
            pcm = concat_pcm_blocks(pcm_blocks)
    except TtsClientError as e:
        logger.error("TTS client error: %s", e)
        return Response(content=str(e), status_code=e.status_code, media_type="text/plain")
    except PcmAudioError as e:
        logger.error("Audio processing error: %s", e)
        return Response(content=str(e), status_code=502, media_type="text/plain")

    try:
        wav_bytes = pcm_to_wav_bytes(pcm)
    except PcmAudioError as e:
        logger.error("PCM conversion error: %s", e)
        return Response(content=str(e), status_code=502, media_type="text/plain")

    return Response(content=wav_bytes, media_type="audio/wav")
