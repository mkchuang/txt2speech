from app.tts.client import GeminiTtsClient, TtsClientError, AUDIO_MIME_PREFIX, DEFAULT_MODEL

SAMPLE_PROMPT = "Hello world. This is a test."
SAMPLE_VOICE = "Puck"
SAMPLE_PCM = b"\x00\x01\x02\x03" * 100


class FakeInlineData:
    def __init__(self, data: bytes, mime_type: str) -> None:
        self.data = data
        self.mime_type = mime_type


class FakePart:
    def __init__(self, inline_data: FakeInlineData | None = None) -> None:
        self.inline_data = inline_data


class FakeContent:
    def __init__(self, parts: list[FakePart]) -> None:
        self.parts = parts


class FakeCandidate:
    def __init__(self, content: FakeContent | None = None) -> None:
        self.content = content


class FakePartsResponse:
    def __init__(self, parts: list[FakePart]) -> None:
        self.parts = parts


class FakeCandidatesResponse:
    def __init__(self, candidates: list[FakeCandidate]) -> None:
        self.candidates = candidates


class FakeCountTokensResponse:
    def __init__(self, total_tokens: int) -> None:
        self.total_tokens = total_tokens


class FakeModels:
    def __init__(
        self,
        generate_content_response: FakePartsResponse | FakeCandidatesResponse | None = None,
        count_tokens_response: FakeCountTokensResponse | None = None,
        raise_error: Exception | None = None,
    ) -> None:
        self._generate_content_response = generate_content_response
        self._count_tokens_response = count_tokens_response
        self._raise_error = raise_error
        self.generate_content_calls: list[dict[str, object]] = []

    def generate_content(self, *, model: str, contents: str, config: object) -> object:
        self.generate_content_calls.append(
            {"model": model, "contents": contents, "config": config}
        )
        if self._raise_error:
            raise self._raise_error
        return self._generate_content_response

    def count_tokens(self, *, model: str, contents: str) -> FakeCountTokensResponse:
        if self._count_tokens_response is None:
            return FakeCountTokensResponse(total_tokens=42)
        return self._count_tokens_response


class FakeClient:
    def __init__(self, models: FakeModels) -> None:
        self.models = models


def _make_normal_response(
    audio_bytes: bytes = SAMPLE_PCM,
    mime_type: str = "audio/pcm",
) -> FakePartsResponse:
    return FakePartsResponse(
        parts=[FakePart(inline_data=FakeInlineData(data=audio_bytes, mime_type=mime_type))]
    )


def _make_candidates_response(
    audio_bytes: bytes = SAMPLE_PCM,
    mime_type: str = "audio/pcm",
) -> FakeCandidatesResponse:
    return FakeCandidatesResponse(
        candidates=[
            FakeCandidate(
                content=FakeContent(
                    parts=[
                        FakePart(
                            inline_data=FakeInlineData(
                                data=audio_bytes,
                                mime_type=mime_type,
                            )
                        )
                    ]
                )
            )
        ]
    )


def _make_config_tracker() -> tuple[list[str], object]:
    calls: list[str] = []

    def factory(voice_name: str) -> object:
        calls.append(voice_name)
        return {"voice": voice_name}

    return calls, factory


def _make_sleep_tracker() -> tuple[list[float], object]:
    calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        calls.append(seconds)

    return calls, fake_sleep


class TestGenerateContentNormal:
    def test_returns_pcm_bytes_from_response_parts(self) -> None:
        response = _make_normal_response(SAMPLE_PCM, "audio/pcm")
        models = FakeModels(generate_content_response=response)
        client_factory = lambda _: FakeClient(models)
        config_calls, config_factory = _make_config_tracker()
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            config_factory=config_factory,
            client_factory=client_factory,
            sleep_func=sleep_func,
        )
        result = tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)

        assert result == SAMPLE_PCM
        assert config_calls == [SAMPLE_VOICE]
        assert len(sleep_calls) == 0

    def test_returns_pcm_bytes_from_candidates_path(self) -> None:
        response = _make_candidates_response(SAMPLE_PCM, "audio/pcm")
        models = FakeModels(generate_content_response=response)
        client_factory = lambda _: FakeClient(models)
        config_calls, config_factory = _make_config_tracker()
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            config_factory=config_factory,
            client_factory=client_factory,
            sleep_func=sleep_func,
        )
        result = tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)

        assert result == SAMPLE_PCM
        assert config_calls == [SAMPLE_VOICE]
        assert len(sleep_calls) == 0

    def test_prefers_response_parts_over_candidates(self) -> None:
        parts_pcm = b"parts_audio"
        candidates_pcm = b"candidates_audio"
        inline_parts = FakeInlineData(data=parts_pcm, mime_type="audio/pcm")
        inline_candidates = FakeInlineData(data=candidates_pcm, mime_type="audio/pcm")

        response = FakePartsResponse(parts=[FakePart(inline_data=inline_parts)])
        response.candidates = [
            FakeCandidate(
                content=FakeContent(parts=[FakePart(inline_data=inline_candidates)])
            )
        ]

        models = FakeModels(generate_content_response=response)
        client_factory = lambda _: FakeClient(models)

        tts = GeminiTtsClient(
            api_key="test-key",
            client_factory=client_factory,
            config_factory=lambda _: None,
            sleep_func=lambda _: None,
        )
        result = tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)

        assert result == parts_pcm

    def test_skips_non_audio_inline_data_before_audio(self) -> None:
        response = FakePartsResponse(
            parts=[
                FakePart(inline_data=FakeInlineData(data=b"not_audio", mime_type="text/plain")),
                FakePart(inline_data=FakeInlineData(data=SAMPLE_PCM, mime_type="audio/pcm")),
            ]
        )
        models = FakeModels(generate_content_response=response)
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            client_factory=lambda _: FakeClient(models),
            config_factory=lambda _: None,
            sleep_func=sleep_func,
        )
        result = tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)

        assert result == SAMPLE_PCM
        assert len(models.generate_content_calls) == 1
        assert len(sleep_calls) == 0

    def test_uses_correct_model_and_contents(self) -> None:
        response = _make_normal_response(SAMPLE_PCM, "audio/pcm")
        models = FakeModels(generate_content_response=response)
        client_factory = lambda _: FakeClient(models)

        tts = GeminiTtsClient(
            api_key="test-key",
            model="gemini-3.1-flash-tts-preview",
            client_factory=client_factory,
            config_factory=lambda _: None,
            sleep_func=lambda _: None,
        )
        tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)

        call = models.generate_content_calls[0]
        assert call["model"] == "gemini-3.1-flash-tts-preview"
        assert call["contents"] == SAMPLE_PROMPT


class TestGenerateContentConfig:
    def test_voice_config_factory_receives_voice_name(self) -> None:
        response = _make_normal_response(SAMPLE_PCM, "audio/pcm")
        models = FakeModels(generate_content_response=response)
        config_calls, config_factory = _make_config_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            config_factory=config_factory,
            client_factory=lambda _: FakeClient(models),
            sleep_func=lambda _: None,
        )
        tts.generate_content(SAMPLE_PROMPT, "Zephyr")

        assert config_calls == ["Zephyr"]

    def test_default_model_is_set(self) -> None:
        response = _make_normal_response(SAMPLE_PCM, "audio/pcm")
        models = FakeModels(generate_content_response=response)

        tts = GeminiTtsClient(
            api_key="test-key",
            client_factory=lambda _: FakeClient(models),
            config_factory=lambda _: None,
            sleep_func=lambda _: None,
        )
        tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)

        assert models.generate_content_calls[0]["model"] == DEFAULT_MODEL


class TestGenerateContentEmptyBytes:
    def test_retries_on_empty_bytes_then_raises_502(self) -> None:
        empty_response = _make_normal_response(b"", "audio/pcm")
        models = FakeModels(generate_content_response=empty_response)
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            max_retries=3,
            backoff_base=2.0,
            client_factory=lambda _: FakeClient(models),
            config_factory=lambda _: None,
            sleep_func=sleep_func,
        )

        try:
            tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)
            assert False, "Expected TtsClientError"
        except TtsClientError as e:
            assert e.status_code == 502
            assert "empty audio" in str(e).lower()

        assert len(models.generate_content_calls) == 4
        assert len(sleep_calls) == 3
        assert sleep_calls[0] == 1.0
        assert sleep_calls[1] == 2.0
        assert sleep_calls[2] == 4.0


class TestGenerateContentMissingInlineData:
    def test_retries_on_missing_inline_data_then_raises_502(self) -> None:
        response = FakePartsResponse(parts=[FakePart(inline_data=None)])
        models = FakeModels(generate_content_response=response)
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            max_retries=2,
            client_factory=lambda _: FakeClient(models),
            config_factory=lambda _: None,
            sleep_func=sleep_func,
        )

        try:
            tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)
            assert False, "Expected TtsClientError"
        except TtsClientError as e:
            assert e.status_code == 502

        assert len(models.generate_content_calls) == 3
        assert len(sleep_calls) == 2

    def test_retries_when_parts_is_empty_list(self) -> None:
        response = FakePartsResponse(parts=[])
        models = FakeModels(generate_content_response=response)
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            max_retries=1,
            client_factory=lambda _: FakeClient(models),
            config_factory=lambda _: None,
            sleep_func=sleep_func,
        )

        try:
            tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)
            assert False, "Expected TtsClientError"
        except TtsClientError as e:
            assert e.status_code == 502

        assert len(sleep_calls) == 1


class TestGenerateContentNonAudioMime:
    def test_retries_on_text_mime_then_raises_502(self) -> None:
        text_response = _make_normal_response(SAMPLE_PCM, "text/plain")
        models = FakeModels(generate_content_response=text_response)
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            max_retries=2,
            client_factory=lambda _: FakeClient(models),
            config_factory=lambda _: None,
            sleep_func=sleep_func,
        )

        try:
            tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)
            assert False, "Expected TtsClientError"
        except TtsClientError as e:
            assert e.status_code == 502
            assert "non-audio" in str(e).lower()

        assert len(models.generate_content_calls) == 3
        assert len(sleep_calls) == 2

    def test_retries_on_video_mime_then_raises_502(self) -> None:
        video_response = _make_normal_response(SAMPLE_PCM, "video/mp4")
        models = FakeModels(generate_content_response=video_response)
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            max_retries=1,
            client_factory=lambda _: FakeClient(models),
            config_factory=lambda _: None,
            sleep_func=sleep_func,
        )

        try:
            tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)
            assert False, "Expected TtsClientError"
        except TtsClientError as e:
            assert e.status_code == 502

        assert len(sleep_calls) == 1


class TestGenerateContentTimeout:
    def test_timeout_after_all_retries_maps_to_504(self) -> None:
        models = FakeModels(raise_error=TimeoutError("timed out"))
        sleep_calls, sleep_func = _make_sleep_tracker()

        tts = GeminiTtsClient(
            api_key="test-key",
            max_retries=2,
            client_factory=lambda _: FakeClient(models),
            config_factory=lambda _: None,
            sleep_func=sleep_func,
        )

        try:
            tts.generate_content(SAMPLE_PROMPT, SAMPLE_VOICE)
            assert False, "Expected TtsClientError"
        except TtsClientError as e:
            assert e.status_code == 504

        assert len(models.generate_content_calls) == 3
        assert len(sleep_calls) == 2


class TestCountTokens:
    def test_returns_total_tokens(self) -> None:
        count_resp = FakeCountTokensResponse(total_tokens=128)
        models = FakeModels(count_tokens_response=count_resp)
        client_factory = lambda _: FakeClient(models)

        tts = GeminiTtsClient(
            api_key="test-key",
            client_factory=client_factory,
            config_factory=lambda _: None,
            sleep_func=lambda _: None,
        )
        result = tts.count_tokens(SAMPLE_PROMPT)

        assert result == 128


class TestTtsClientError:
    def test_status_code_defaults_to_502(self) -> None:
        err = TtsClientError("test")
        assert err.status_code == 502

    def test_status_code_can_be_overridden(self) -> None:
        err = TtsClientError("test", status_code=504)
        assert err.status_code == 504

    def test_is_exception_instance(self) -> None:
        err = TtsClientError("test")
        assert isinstance(err, Exception)
