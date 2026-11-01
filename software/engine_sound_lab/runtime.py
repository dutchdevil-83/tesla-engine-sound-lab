"""Offline render, bounded benchmarking and optional local audio playback."""

import array
import math
import statistics
import time
import wave
from pathlib import Path
from typing import Callable

from .profiles import EngineProfile
from .synth import EngineSynth
from .telemetry import Telemetry, synthetic_telemetry

SAMPLE_RATE = 48000
BLOCK_SIZE = 256
BLOCK_PERIOD_NS = round(BLOCK_SIZE * 1_000_000_000 / SAMPLE_RATE)


def render_wav(path: Path, profile: EngineProfile, seconds: float, volume: float) -> int:
    """Write a new WAV file; never overwrite an existing file."""
    validate_duration(seconds)
    engine = EngineSynth(profile, sample_rate=SAMPLE_RATE, volume=volume)
    total = round(seconds * SAMPLE_RATE)
    written = 0
    pcm = bytearray(BLOCK_SIZE * 4)
    buffer = memoryview(pcm)
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
                engine.render_into(signal, now, count, buffer[:count * 4])
                output.writeframesraw(buffer[:count * 4])
                written += count
    return written


def math_ceil_index(length: int, fraction: float) -> int:
    """Nearest-rank percentile index for a nonempty sorted list."""
    return max(0, min(length - 1, math.ceil(length * fraction) - 1))


def _timing_summary(durations_ns: list[int] | array.array) -> dict[str, float]:
    if not durations_ns:
        return {"median_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}
    ordered = sorted(durations_ns)
    return {"median_ms": statistics.median(durations_ns) / 1_000_000,
            "p95_ms": ordered[math_ceil_index(len(ordered), .95)] / 1_000_000,
            "max_ms": ordered[-1] / 1_000_000}


def _validate_blocks(blocks: int) -> None:
    if not isinstance(blocks, int) or not 1 <= blocks <= 10000:
        raise ValueError("blocks must be an integer between 1 and 10000")


def benchmark(profile: EngineProfile, blocks: int = 200) -> dict[str, float | int]:
    """Measure consecutive synthesis calls; excludes scheduling and audio I/O."""
    _validate_blocks(blocks)
    engine = EngineSynth(profile)
    pcm = bytearray(BLOCK_SIZE * 4)
    durations_ns = []
    for index in range(blocks):
        now = index * BLOCK_SIZE / SAMPLE_RATE
        signal = synthetic_telemetry(now, now)
        started_ns = time.perf_counter_ns()
        engine.render_into(signal, now, BLOCK_SIZE, pcm)
        durations_ns.append(time.perf_counter_ns() - started_ns)
    return {"blocks": blocks, "block_frames": BLOCK_SIZE,
            "block_period_ms": BLOCK_SIZE / SAMPLE_RATE * 1000,
            **_timing_summary(durations_ns),
            "over_budget_blocks": sum(ns > BLOCK_PERIOD_NS for ns in durations_ns)}


def benchmark_paced(profile: EngineProfile, blocks: int = 200, warmup_blocks: int = 50,
                    *, clock_ns: Callable[[], int] | None = None,
                    sleep: Callable[[float], None] | None = None) -> dict[str, float | int | str]:
    """Pace synthetic blocks with a monotonic clock; no audio device is opened.

    Deadline misses include wake-up lateness and synthesis work. They are NOT
    PortAudio underflows or acoustic latency measurements. Injected clock/sleep
    permit deterministic scheduler tests without real-time waits.
    """
    _validate_blocks(blocks)
    if not isinstance(warmup_blocks, int) or not 0 <= warmup_blocks <= 5000:
        raise ValueError("warmup_blocks must be an integer between 0 and 5000")
    if clock_ns is None:
        clock_ns = time.perf_counter_ns
    if sleep is None:
        sleep = time.sleep
    engine = EngineSynth(profile)
    pcm = bytearray(BLOCK_SIZE * 4)
    period_s = BLOCK_SIZE / SAMPLE_RATE
    for i in range(warmup_blocks):
        now = i * period_s
        engine.render_into(synthetic_telemetry(now, now), now, BLOCK_SIZE, pcm)

    origin_ns = clock_ns()
    render_times_ns: list[int] = []
    wake_lateness_ns: list[int] = []
    deadline_misses = 0
    for i in range(blocks):
        scheduled_ns = origin_ns + i * BLOCK_PERIOD_NS
        until_ns = scheduled_ns - clock_ns()
        if until_ns > 0:
            sleep(until_ns / 1_000_000_000)
        woke_ns = clock_ns()
        logical_now = (warmup_blocks + i) * period_s
        signal = synthetic_telemetry(logical_now, logical_now)
        start_ns = clock_ns()
        engine.render_into(signal, logical_now, BLOCK_SIZE, pcm)
        end_ns = clock_ns()
        render_times_ns.append(end_ns - start_ns)
        wake_lateness_ns.append(max(0, woke_ns - scheduled_ns))
        if end_ns > scheduled_ns + BLOCK_PERIOD_NS:
            deadline_misses += 1
    rendering = _timing_summary(render_times_ns)
    wake = _timing_summary(wake_lateness_ns)
    return {"measurement": "paced synthetic clock, no audio device",
            "blocks": blocks, "warmup_blocks": warmup_blocks,
            "block_frames": BLOCK_SIZE, "block_period_ms": period_s * 1000,
            **rendering, "over_budget_blocks": sum(ns > BLOCK_PERIOD_NS for ns in render_times_ns),
            "wake_median_ms": wake["median_ms"], "wake_p95_ms": wake["p95_ms"],
            "wake_max_ms": wake["max_ms"], "paced_deadline_misses": deadline_misses}


def play_synthetic(profile: EngineProfile, seconds: float, volume: float,
                   device: str | None = None) -> dict[str, float | int]:
    """Optional local PortAudio playback with off-callback telemetry generation.

    Actual ``output_underflows`` come ONLY from PortAudio callback status.
    The timing samples measure Python callback processing, not device or
    end-to-end latency. All buffers and instrumentation arrays are preallocated.
    """
    validate_duration(seconds)
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Audio playback requires the optional audio extra; see software/README.md.") from exc

    engine = EngineSynth(profile, volume=volume)
    fade_start = max(0.0, seconds - engine.fade_seconds - 2 * BLOCK_SIZE / SAMPLE_RATE)
    # Allow more records than nominal callbacks; cap allocation for max 60 s.
    capacity = math.ceil(seconds * SAMPLE_RATE / BLOCK_SIZE * 2) + 64
    processing_ns = array.array("q", [0]) * capacity
    callback_interval_ns = array.array("q", [0]) * capacity
    frame_counts = array.array("I", [0]) * capacity
    # [callbacks, reported output underflows, errors, finished, last start ns]
    state: list[int | bool] = [0, 0, 0, False, -1]
    first_callback: list[float | None] = [None]
    initial_time = time.monotonic()
    latest: list[Telemetry | None] = [synthetic_telemetry(0.0, initial_time)]
    # Preallocate all supported silence sizes. The slice is only used on error.
    silence = memoryview(bytes(65536 * 4))

    def callback(outdata: object, frames: int, _time_info: object, status: object) -> None:
        started_ns = time.perf_counter_ns()
        index = int(state[0])
        state[0] = index + 1
        stop = False
        try:
            if getattr(status, "output_underflow", False):
                state[1] = int(state[1]) + 1
            now = time.monotonic()
            if first_callback[0] is None:
                first_callback[0] = now
            elapsed = now - first_callback[0]
            engine.render_into(latest[0] if elapsed < fade_start else None, now, frames, outdata)
            stop = elapsed >= seconds
        except Exception:
            state[2] = int(state[2]) + 1
            # Never let partially synthesized data escape from an error.
            length = len(outdata)  # type: ignore[arg-type]
            outdata[:] = (silence[:length] if length <= len(silence)
                          else bytes(length))  # type: ignore[index]
            # Abort on failure rather than drain already queued sound.
            raise getattr(sd, "CallbackAbort", sd.CallbackStop)
        finally:
            if index < capacity:
                frame_counts[index] = frames
                callback_interval_ns[index] = started_ns - int(state[4]) if state[4] != -1 else 0
                processing_ns[index] = time.perf_counter_ns() - started_ns
            state[4] = started_ns
        if stop:
            state[3] = True
            raise sd.CallbackStop

    portaudio_cpu_load = None
    portaudio_latency_s = None
    with sd.RawOutputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, device=device,
                            channels=2, dtype="int16", callback=callback) as stream:
        deadline = time.monotonic() + seconds + 5
        while stream.active and time.monotonic() < deadline and not state[2]:
            now = time.monotonic()
            if first_callback[0] is not None:
                elapsed = now - first_callback[0]
                latest[0] = synthetic_telemetry(elapsed, now) if elapsed < fade_start else None
            time.sleep(.01)
        if stream.active and not state[2]:
            raise RuntimeError("Audio stream did not finish in time; output was stopped.")
        # Query device statistics on the foreground thread only.
        portaudio_cpu_load = getattr(stream, "cpu_load", None)
        portaudio_latency_s = getattr(stream, "latency", None)

    callbacks = int(state[0])
    if state[2]:
        raise RuntimeError("Audio callback failed; output was silenced.")
    if not callbacks:
        raise RuntimeError("Audio stream stopped without producing any callbacks.")
    if not state[3]:
        raise RuntimeError("Audio stream stopped before the requested duration.")
    recorded = min(callbacks, capacity)
    durations = processing_ns[:recorded]
    intervals = callback_interval_ns[1:recorded]
    # Use the actual supplied frame count rather than assuming 256 forever.
    over_budget = sum(durations[i] > frame_counts[i] * 1_000_000_000 / SAMPLE_RATE
                      for i in range(recorded))
    summary = _timing_summary(durations)
    interval_summary = _timing_summary(intervals)
    result = {"callbacks": callbacks, "output_underflows": int(state[1]),
            "callback_errors": int(state[2]), "timing_samples": recorded,
            "timing_samples_dropped": callbacks - recorded,
            "callback_over_budget_blocks": over_budget,
            "callback_median_ms": summary["median_ms"],
            "callback_p95_ms": summary["p95_ms"],
            "callback_max_ms": summary["max_ms"],
            "callback_interval_p95_ms": interval_summary["p95_ms"],
            "callback_interval_max_ms": interval_summary["max_ms"]}
    if isinstance(portaudio_cpu_load, (int, float)) and math.isfinite(portaudio_cpu_load):
        result["portaudio_cpu_load"] = float(portaudio_cpu_load)
    if isinstance(portaudio_latency_s, (int, float)) and math.isfinite(portaudio_latency_s):
        result["portaudio_output_latency_s"] = float(portaudio_latency_s)
    return result


def validate_duration(seconds: float) -> None:
    if not math.isfinite(seconds) or not 1 <= seconds <= 60:
        raise ValueError("duration must be between 1 and 60 seconds")
