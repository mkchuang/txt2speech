"""POST /api/synthesize — M2 single-chunk synthesis (temporary internal contract).

M4 will replace this endpoint to return JSON:
    {id, created_at, metadata, audio_url}
instead of raw audio/wav bytes. Frontend MUST NOT depend on this M2 shape.
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.audio.pcm import PcmAudioError, pcm_to_wav_bytes
from app.config import settings
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


@router.post("/api/synthesize")
async def synthesize(
    request: SynthesizeRequest,
    tts_client: GeminiTtsClient = Depends(get_tts_client),
) -> Response:
    # --- M2 temporary contract: returns raw audio/wav bytes ---
    # M4 will change this to return JSON: {id, created_at, metadata, audio_url}
    # Frontend MUST NOT depend on this M2 response shape.
    # ------------------------------------------------------------

    prompt = build_prompt(
        transcript=request.text,
        style=request.style,
        pacing=request.pacing,
        accent=request.accent,
        voice=request.voice,
    )

    try:
        pcm = tts_client.generate_content(prompt, request.voice)
    except TtsClientError as e:
        logger.error("TTS client error: %s", e)
        return Response(content=str(e), status_code=e.status_code, media_type="text/plain")

    try:
        wav_bytes = pcm_to_wav_bytes(pcm)
    except PcmAudioError as e:
        logger.error("PCM conversion error: %s", e)
        return Response(content=str(e), status_code=502, media_type="text/plain")

    return Response(content=wav_bytes, media_type="audio/wav")
