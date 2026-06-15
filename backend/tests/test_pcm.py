import io
import wave

import pytest

from app.audio.pcm import (
    CHANNELS,
    PcmAudioError,
    SAMPLE_RATE_HZ,
    SAMPLE_WIDTH_BYTES,
    frame_size,
    pcm_to_wav_bytes,
    validate_frame_alignment,
)


def _make_pcm(frame_count: int) -> bytes:
    return bytes(i % 256 for i in range(frame_count * frame_size()))


class TestDefaultConstants:
    def test_sample_rate(self) -> None:
        assert SAMPLE_RATE_HZ == 24000

    def test_channels(self) -> None:
        assert CHANNELS == 1

    def test_sample_width(self) -> None:
        assert SAMPLE_WIDTH_BYTES == 2

    def test_frame_size(self) -> None:
        assert frame_size() == 2
        assert frame_size(channels=2, sample_width_bytes=2) == 4
        assert frame_size(channels=1, sample_width_bytes=4) == 4


class TestValidateFrameAlignment:
    def test_valid_aligned_pcm_passes(self) -> None:
        pcm = _make_pcm(100)
        validate_frame_alignment(pcm)

    def test_empty_pcm_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="must not be empty"):
            validate_frame_alignment(b"")

    def test_odd_length_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="not a multiple of"):
            validate_frame_alignment(b"\x00\x01\x02")

    def test_stereo_odd_length_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="not a multiple of"):
            validate_frame_alignment(b"\x00\x01\x02\x03\x04", channels=2)

    def test_invalid_channels_zero_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="channels"):
            validate_frame_alignment(b"\x00\x01", channels=0)

    def test_invalid_channels_negative_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="channels"):
            validate_frame_alignment(b"\x00\x01", channels=-1)

    def test_invalid_sample_width_zero_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="sample_width_bytes"):
            validate_frame_alignment(b"\x00\x01", sample_width_bytes=0)

    def test_invalid_sample_width_three_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="sample_width_bytes"):
            validate_frame_alignment(b"\x00\x01\x02", sample_width_bytes=3)


class TestPcmToWavBytes:
    def test_empty_pcm_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="must not be empty"):
            pcm_to_wav_bytes(b"")

    def test_unaligned_pcm_raises(self) -> None:
        with pytest.raises(PcmAudioError, match="not a multiple of"):
            pcm_to_wav_bytes(b"\x00\x01\x02")

    def test_invalid_sample_rate_zero_raises(self) -> None:
        pcm = _make_pcm(10)
        with pytest.raises(PcmAudioError, match="sample_rate_hz"):
            pcm_to_wav_bytes(pcm, sample_rate_hz=0)

    def test_invalid_sample_rate_negative_raises(self) -> None:
        pcm = _make_pcm(10)
        with pytest.raises(PcmAudioError, match="sample_rate_hz"):
            pcm_to_wav_bytes(pcm, sample_rate_hz=-1)

    def test_invalid_channels_zero_raises(self) -> None:
        pcm = _make_pcm(10)
        with pytest.raises(PcmAudioError, match="channels"):
            pcm_to_wav_bytes(pcm, channels=0)

    def test_invalid_sample_width_raises(self) -> None:
        pcm = _make_pcm(10)
        with pytest.raises(PcmAudioError, match="sample_width_bytes"):
            pcm_to_wav_bytes(pcm, sample_width_bytes=3)


class TestWavOutput:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.frame_count = 480
        self.original = _make_pcm(self.frame_count)

    def _read_wav(self, wav_bytes: bytes) -> wave.Wave_read:
        return wave.open(io.BytesIO(wav_bytes), "rb")

    def test_wav_header_parameters_correct(self) -> None:
        wav_bytes = pcm_to_wav_bytes(self.original)
        with self._read_wav(wav_bytes) as wf:
            assert wf.getnchannels() == CHANNELS
            assert wf.getsampwidth() == SAMPLE_WIDTH_BYTES
            assert wf.getframerate() == SAMPLE_RATE_HZ
            assert wf.getnframes() == self.frame_count

    def test_frame_count_correct(self) -> None:
        wav_bytes = pcm_to_wav_bytes(self.original)
        with self._read_wav(wav_bytes) as wf:
            assert wf.getnframes() == self.frame_count
            all_frames = wf.readframes(wf.getnframes())
            assert len(all_frames) == self.frame_count * frame_size()

    def test_roundtrip_bytes_identical(self) -> None:
        wav_bytes = pcm_to_wav_bytes(self.original)
        with self._read_wav(wav_bytes) as wf:
            readback = wf.readframes(wf.getnframes())
            assert readback == self.original

    def test_single_frame_pcm(self) -> None:
        pcm = b"\x34\x12"
        wav_bytes = pcm_to_wav_bytes(pcm)
        with self._read_wav(wav_bytes) as wf:
            assert wf.getnframes() == 1
            assert wf.readframes(1) == pcm

    def test_custom_params_roundtrip(self) -> None:
        sr = 44100
        ch = 2
        sw = 2
        fs = ch * sw
        nf = 200
        pcm = bytes(i % 256 for i in range(nf * fs))
        wav_bytes = pcm_to_wav_bytes(
            pcm,
            sample_rate_hz=sr,
            channels=ch,
            sample_width_bytes=sw,
        )
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            assert wf.getnchannels() == ch
            assert wf.getsampwidth() == sw
            assert wf.getframerate() == sr
            assert wf.getnframes() == nf
            assert wf.readframes(nf) == pcm

    def test_large_pcm_roundtrip(self) -> None:
        nf = 24000
        pcm = bytes(i % 256 for i in range(nf * frame_size()))
        wav_bytes = pcm_to_wav_bytes(pcm)
        with self._read_wav(wav_bytes) as wf:
            assert wf.getnframes() == nf
            assert wf.readframes(nf) == pcm

    def test_wav_writable_to_non_seekable_stream_does_not_crash(self) -> None:
        pcm = _make_pcm(50)
        wav_bytes = pcm_to_wav_bytes(pcm)
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            assert wf.getnframes() == 50
