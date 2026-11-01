"""Deterministic offline synthesis; not a vehicle-ready real-time engine."""

import math
import struct
import sys

from .profiles import EngineProfile
from .telemetry import Telemetry


class EngineSynth:
    """Generate bounded little-endian 16-bit stereo PCM with a stale-input fade.

    ``render_into`` writes to a caller-owned buffer, avoiding one PCM array
    allocation, repeated array extensions, and a bytes conversion per block.
    It still executes Python code and is not a hard-real-time guarantee.
    """

    def __init__(self, profile: EngineProfile, sample_rate: int = 48000,
                 volume: float = .18, stale_after: float = .25, fade_seconds: float = .2):
        if not isinstance(sample_rate, int) or not 8000 <= sample_rate <= 192000:
            raise ValueError("sample_rate must be between 8000 and 192000")
        if not math.isfinite(volume) or not 0 <= volume <= .5:
            raise ValueError("volume must be between 0 and 0.5")
        if not math.isfinite(stale_after) or stale_after <= 0 or not math.isfinite(fade_seconds) or fade_seconds <= 0:
            raise ValueError("stale_after and fade_seconds must be positive and finite")
        self.profile = profile
        self.sample_rate = sample_rate
        self.volume = volume
        self.stale_after = stale_after
        self.fade_seconds = fade_seconds
        self.rpm = profile.idle_rpm
        self.phase = 0.0
        self.whine_phase = 0.0
        self.filter_state = 0.0
        self.envelope = 0.0
        self.load = 0.0
        self.valid = False

    def render(self, telemetry: Telemetry | None, now: float, frames: int) -> bytes:
        """Convenience API returning bytes; ``render_into`` is the low-allocation API."""
        if not isinstance(frames, int) or not 0 <= frames <= 65536:
            raise ValueError("frames must be an integer from 0 to 65536")
        pcm = bytearray(frames * 4)
        self.render_into(telemetry, now, frames, pcm)
        return bytes(pcm)

    def render_into(self, telemetry: Telemetry | None, now: float,
                    frames: int, outdata: object) -> None:
        """Fill exactly ``frames * 4`` writable bytes of interleaved stereo PCM.

        The caller retains and may reuse the buffer. Any bad buffer is rejected
        before changing the synthesizer's internal state.
        """
        if not isinstance(frames, int) or not 0 <= frames <= 65536:
            raise ValueError("frames must be an integer from 0 to 65536")
        pcm = memoryview(outdata)
        if pcm.readonly or not pcm.contiguous or pcm.nbytes != frames * 4:
            raise ValueError("outdata must be writable, contiguous, and exactly frames * 4 bytes")
        if pcm.format != "B" or pcm.ndim != 1:
            pcm = pcm.cast("B")
        # Direct native signed-16 writes on little-endian systems; an explicit
        # little-endian struct fallback preserves the WAV/PortAudio byte format.
        samples = pcm.cast("h") if sys.byteorder == "little" else None

        valid = telemetry is not None and telemetry.valid_at(now, self.stale_after)
        valid_frames = 0
        if valid and telemetry is not None:
            remaining = self.stale_after - (now - telemetry.timestamp)
            valid_frames = frames if remaining >= frames / self.sample_rate else max(0, math.floor(remaining * self.sample_rate) + 1)
        if valid and telemetry is not None:
            # Virtual gearing is intentionally fictional, not a CAN mapping.
            gear = 1 + sum(telemetry.speed_kph >= threshold for threshold in (25, 50, 80, 115, 155))
            target = self.profile.idle_rpm + telemetry.speed_kph * (60 / gear) + telemetry.pedal * 1600
            target = min(self.profile.redline_rpm, max(self.profile.idle_rpm, target))
            smoothing = 1 - math.exp(-frames / (self.sample_rate * .12))
            self.rpm += (target - self.rpm) * smoothing
            self.load += (telemetry.pedal - self.load) * smoothing

        fade_step = 1.0 / (self.fade_seconds * self.sample_rate)
        phase_step = 2 * math.pi * (self.rpm * self.profile.cylinders / 120) / self.sample_rate
        whine_step = 2 * math.pi * (450 + self.rpm * .12) / self.sample_rate
        coefficient = 1 - math.exp(-2 * math.pi * self.profile.resonance_hz / self.sample_rate)
        envelope, phase = self.envelope, self.phase
        whine_phase, filter_state = self.whine_phase, self.filter_state
        harmonic_2, harmonic_3 = self.profile.harmonic_2, self.profile.harmonic_3
        turbo_mix, load = self.profile.turbo_mix, self.load
        volume = self.volume
        sin, tanh = math.sin, math.tanh
        tau = 2 * math.pi

        for index in range(frames):
            envelope = min(1.0, envelope + fade_step) if index < valid_frames else max(0.0, envelope - fade_step)
            if envelope == 0:
                sample = 0
            else:
                phase = (phase + phase_step) % tau
                whine_phase = (whine_phase + whine_step) % tau
                wave = (sin(phase) + harmonic_2 * sin(2 * phase)
                        + harmonic_3 * sin(3 * phase))
                filter_state += coefficient * (wave - filter_state)
                whine = turbo_mix * load * sin(whine_phase)
                shaped = tanh((filter_state * .9 + wave * .18 + whine) * (0.55 + load * .45))
                sample = max(-32767, min(32767, round(shaped * envelope * volume * 32767)))
            if samples is not None:
                samples[2 * index] = sample
                samples[2 * index + 1] = sample
            else:
                struct.pack_into("<hh", pcm, 4 * index, sample, sample)

        self.envelope, self.phase = envelope, phase
        self.whine_phase, self.filter_state = whine_phase, filter_state
        self.valid = valid and valid_frames == frames
