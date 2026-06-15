import io
import wave
from collections.abc import Sequence

SAMPLE_RATE_HZ: int = 24000
CHANNELS: int = 1
SAMPLE_WIDTH_BYTES: int = 2

VALID_SAMPLE_WIDTHS: set[int] = {1, 2, 4}


class PcmAudioError(ValueError):
    """Raised when PCM audio cannot be converted safely."""


def _validate_params(
    sample_rate_hz: int,
    channels: int,
    sample_width_bytes: int,
) -> None:
    if sample_rate_hz <= 0:
        raise PcmAudioError(f"sample_rate_hz must be > 0, got {sample_rate_hz}")
    if channels <= 0:
        raise PcmAudioError(f"channels must be > 0, got {channels}")
    if sample_width_bytes not in VALID_SAMPLE_WIDTHS:
        raise PcmAudioError(
            f"sample_width_bytes must be one of {sorted(VALID_SAMPLE_WIDTHS)}, "
            f"got {sample_width_bytes}"
        )


def frame_size(
    channels: int = CHANNELS,
    sample_width_bytes: int = SAMPLE_WIDTH_BYTES,
) -> int:
    """Return the number of bytes in one PCM frame."""
    return channels * sample_width_bytes


def validate_frame_alignment(
    pcm: bytes,
    channels: int = CHANNELS,
    sample_width_bytes: int = SAMPLE_WIDTH_BYTES,
) -> None:
    """Validate non-empty PCM bytes align to whole audio frames."""
    _validate_params(
        sample_rate_hz=1,
        channels=channels,
        sample_width_bytes=sample_width_bytes,
    )
    fs = frame_size(channels, sample_width_bytes)
    if not pcm:
        raise PcmAudioError("PCM data must not be empty")
    if len(pcm) % fs != 0:
        raise PcmAudioError(
            f"PCM byte length {len(pcm)} is not a multiple of "
            f"frame_size={fs} (channels={channels}, "
            f"sample_width_bytes={sample_width_bytes})"
        )


def concat_pcm_blocks(
    pcm_blocks: Sequence[bytes],
    channels: int = CHANNELS,
    sample_width_bytes: int = SAMPLE_WIDTH_BYTES,
) -> bytes:
    """Concatenate multiple raw PCM blocks into a single PCM byte sequence.

    Each block is validated for frame alignment before concatenation.

    Args:
        pcm_blocks: List of raw PCM byte sequences (non-empty, all frame-aligned).
        channels: Number of audio channels (default 1).
        sample_width_bytes: Bytes per sample (default 2).

    Returns:
        Concatenated raw PCM bytes.

    Raises:
        PcmAudioError: If no blocks provided or any block is not frame-aligned.
    """
    if not pcm_blocks:
        raise PcmAudioError("pcm_blocks must not be empty")
    _validate_params(
        sample_rate_hz=1,
        channels=channels,
        sample_width_bytes=sample_width_bytes,
    )
    for block in pcm_blocks:
        validate_frame_alignment(block, channels, sample_width_bytes)
    return b"".join(pcm_blocks)


def pcm_to_wav_bytes(
    pcm: bytes,
    sample_rate_hz: int = SAMPLE_RATE_HZ,
    channels: int = CHANNELS,
    sample_width_bytes: int = SAMPLE_WIDTH_BYTES,
) -> bytes:
    """Wrap raw PCM bytes in a WAV container."""
    _validate_params(sample_rate_hz, channels, sample_width_bytes)
    fs = frame_size(channels, sample_width_bytes)
    if not pcm:
        raise PcmAudioError("PCM data must not be empty")
    if len(pcm) % fs != 0:
        raise PcmAudioError(
            f"PCM byte length {len(pcm)} is not a multiple of "
            f"frame_size={fs} (channels={channels}, "
            f"sample_width_bytes={sample_width_bytes})"
        )
    frame_count = len(pcm) // fs
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width_bytes)
        wf.setframerate(sample_rate_hz)
        wf.setnframes(frame_count)
        wf.writeframes(pcm)
    return buf.getvalue()
