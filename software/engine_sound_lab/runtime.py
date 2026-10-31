"""Offline render, benchmark and optional local audio playback."""

import statistics
import math
import time
import wave
from pathlib import Path
from .profiles import EngineProfile
from .synth import EngineSynth
from .telemetry import synthetic_telemetry

SAMPLE_RATE = 48000
BLOCK_SIZE = 256


def render_wav(path: Path, profile: EngineProfile, seconds: float, volume: float) -> int:
    """Write a new WAV file; never overwrite an existing file."""
    validate_duration(seconds)
    engine = EngineSynth(profile, sample_rate=SAMPLE_RATE, volume=volume)
    total = round(seconds * SAMPLE_RATE)
    written = 0
    with path.open("xb") as raw:
        with wave.open(raw, "wb") as output:
            output.setnchannels(2)
            output.setsampwidth(2)
            output.setframerate(SAMPLE_RATE)
            while written < total:
                count = min(BLOCK_SIZE, total - written)
                now = written / SAMPLE_RATE
                # Allow for block rounding and floating-point boundary comparisons.
                fade_start = max(0, seconds - engine.fade_seconds - 2 * BLOCK_SIZE / SAMPLE_RATE)
                signal = None if now >= fade_start else synthetic_telemetry(now, now)
                output.writeframesraw(engine.render(signal, now, count))
                written += count
    return written


def benchmark(profile: EngineProfile, blocks: int = 200) -> dict[str, float | int]:
    """Measure local block synthesis only; excludes device and acoustic latency."""
    if not isinstance(blocks, int) or not 1 <= blocks <= 10000:
        raise ValueError("blocks must be an integer between 1 and 10000")
    engine = EngineSynth(profile)
    durations = []
    for index in range(blocks):
        now = index * BLOCK_SIZE / SAMPLE_RATE
        signal = synthetic_telemetry(now, now)
        start = time.perf_counter()
        engine.render(signal, now, BLOCK_SIZE)
        durations.append((time.perf_counter() - start) * 1000)
    ordered = sorted(durations)
    return {"blocks": blocks, "block_frames": BLOCK_SIZE, "block_period_ms": BLOCK_SIZE / SAMPLE_RATE * 1000,
            "median_ms": statistics.median(durations), "p95_ms": ordered[math_ceil_index(len(ordered), .95)],
            "max_ms": max(durations), "over_budget_blocks": sum(x > BLOCK_SIZE / SAMPLE_RATE * 1000 for x in durations)}


def math_ceil_index(length: int, fraction: float) -> int:
    """Nearest-rank percentile index for a nonempty sorted list."""
    return max(0, min(length - 1, math.ceil(length * fraction) - 1))


def play_synthetic(profile: EngineProfile, seconds: float, volume: float, device: str | None = None) -> dict[str, int]:
    """Play the synthetic cycle locally via PortAudio; never opens vehicle interfaces."""
    validate_duration(seconds)
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Audio playback requires the optional audio extra; see software/README.md.") from exc
    engine = EngineSynth(profile, volume=volume)
    first_callback: list[float] = []
    stats = {"callbacks": 0, "output_underflows": 0, "callback_errors": 0}
    finished = [False]

    def callback(outdata: object, frames: int, _time_info: object, status: object) -> None:
        # Python/PortAudio allocations here are acceptable only for this bench prototype.
        stats["callbacks"] += 1
        if getattr(status, "output_underflow", False):
            stats["output_underflows"] += 1
        now = time.monotonic()
        if not first_callback:
            first_callback.append(now)
        elapsed = now - first_callback[0]
        try:
            fade_start = max(0, seconds - engine.fade_seconds - 2 * BLOCK_SIZE / SAMPLE_RATE)
            sample = synthetic_telemetry(elapsed, now) if elapsed < fade_start else None
            outdata[:] = engine.render(sample, now, frames)  # type: ignore[index]
        except Exception:
            stats["callback_errors"] += 1
            outdata[:] = bytes(frames * 4)  # type: ignore[index]
            raise sd.CallbackStop
        if elapsed >= seconds:
            finished[0] = True
            raise sd.CallbackStop

    with sd.RawOutputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, device=device,
                            channels=2, dtype="int16", callback=callback) as stream:
        deadline = time.monotonic() + seconds + 5
        while stream.active and time.monotonic() < deadline and not stats["callback_errors"]:
            time.sleep(.05)
        if stream.active:
            raise RuntimeError("Audio stream did not finish in time; output was stopped.")
    if stats["callback_errors"]:
        raise RuntimeError("Audio callback failed; output was silenced.")
    if not stats["callbacks"]:
        raise RuntimeError("Audio stream stopped without producing any callbacks.")
    if not finished[0]:
        raise RuntimeError("Audio stream stopped before the requested duration.")
    return stats


def validate_duration(seconds: float) -> None:
    if not math.isfinite(seconds) or not 1 <= seconds <= 60:
        raise ValueError("duration must be between 1 and 60 seconds")
