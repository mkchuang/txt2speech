import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.1-flash-tts-preview"
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 2.0
AUDIO_MIME_PREFIX = "audio/"


class TtsClientError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def _default_client_factory(api_key: str) -> Any:
    from google import genai

    return genai.Client(api_key=api_key)


def _default_config_factory(voice_name: str) -> Any:
    from google.genai import types

    return types.GenerateContentConfig(
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_name,
                )
            )
        ),
    )


class GeminiTtsClient:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        client_factory: Callable[[str], Any] | None = None,
        config_factory: Callable[[str], Any] | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._client_factory = client_factory or _default_client_factory
        self._config_factory = config_factory or _default_config_factory
        self._sleep = sleep_func

    def _get_client(self) -> Any:
        return self._client_factory(self._api_key)

    def generate_content(self, prompt: str, voice_name: str) -> bytes:
        client = self._get_client()
        config = self._config_factory(voice_name)

        for attempt in range(self._max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=config,
                )

                audio_bytes, mime_type = self._extract_audio(response)

                if audio_bytes is None or len(audio_bytes) == 0:
                    if attempt < self._max_retries:
                        logger.warning(
                            "TTS response audio bytes empty (attempt %d/%d)",
                            attempt + 1,
                            self._max_retries,
                        )
                        self._sleep(self._backoff_base**attempt)
                        continue
                    raise TtsClientError(
                        "Gemini TTS returned empty audio after all retries",
                        status_code=502,
                    )

                if mime_type is None or not mime_type.startswith(AUDIO_MIME_PREFIX):
                    if attempt < self._max_retries:
                        logger.warning(
                            "TTS response mime is not audio: %s (attempt %d/%d)",
                            mime_type,
                            attempt + 1,
                            self._max_retries,
                        )
                        self._sleep(self._backoff_base**attempt)
                        continue
                    raise TtsClientError(
                        f"Gemini TTS returned non-audio response: mime={mime_type}",
                        status_code=502,
                    )

                return audio_bytes

            except TtsClientError:
                raise
            except TimeoutError as e:
                if attempt < self._max_retries:
                    logger.warning(
                        "TTS request timed out (attempt %d/%d): %s",
                        attempt + 1,
                        self._max_retries,
                        e,
                    )
                    self._sleep(self._backoff_base**attempt)
                    continue
                raise TtsClientError(
                    f"Gemini TTS timed out after {self._max_retries + 1} attempts",
                    status_code=504,
                ) from e
            except Exception as e:
                if attempt < self._max_retries:
                    logger.warning(
                        "TTS generate_content failed: %s (attempt %d/%d)",
                        e,
                        attempt + 1,
                        self._max_retries,
                    )
                    self._sleep(self._backoff_base**attempt)
                    continue
                raise TtsClientError(
                    f"Gemini TTS failed after {self._max_retries + 1} attempts: {e}",
                    status_code=502,
                ) from e

        raise TtsClientError(
            "Gemini TTS exhausted retries unexpectedly", status_code=502
        )

    @staticmethod
    def _extract_audio(response: Any) -> tuple[bytes | None, str | None]:
        fallback: tuple[bytes | None, str | None] | None = None

        def inspect_parts(parts: Any) -> tuple[bytes | None, str | None] | None:
            nonlocal fallback
            for part in parts:
                if (
                    not hasattr(part, "inline_data")
                    or part.inline_data is None
                    or not hasattr(part.inline_data, "data")
                ):
                    continue

                inline_data = part.inline_data
                audio_data = getattr(inline_data, "data")
                mime_type = getattr(inline_data, "mime_type", None)
                candidate = (audio_data, mime_type)
                if fallback is None:
                    fallback = candidate
                if (
                    audio_data
                    and mime_type is not None
                    and mime_type.startswith(AUDIO_MIME_PREFIX)
                ):
                    return candidate
            return None

        if hasattr(response, "parts") and response.parts:
            audio = inspect_parts(response.parts)
            if audio is not None:
                return audio

        if hasattr(response, "candidates") and response.candidates:
            for candidate in response.candidates:
                if not hasattr(candidate, "content") or candidate.content is None:
                    continue
                content = candidate.content
                if hasattr(content, "parts") and content.parts:
                    audio = inspect_parts(content.parts)
                    if audio is not None:
                        return audio

        return fallback or (None, None)

    def count_tokens(self, prompt: str) -> int:
        client = self._get_client()
        response = client.models.count_tokens(
            model=self._model,
            contents=prompt,
        )
        return response.total_tokens
