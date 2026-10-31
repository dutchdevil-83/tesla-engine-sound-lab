"""Deterministic synthesis for bench use, not a vehicle-ready real-time engine."""

import array
import math
import sys
from .profiles import EngineProfile
from .telemetry import Telemetry


class EngineSynth:
    """Generate 16-bit stereo PCM with bounded output and a stale-input fade."""

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
        if not isinstance(frames, int) or not 0 <= frames <= 65536:
            raise ValueError("frames must be an integer from 0 to 65536")
        self.valid = telemetry is not None and telemetry.valid_at(now, self.stale_after)
        valid_frames = 0
        if self.valid and telemetry is not None:
            remaining = self.stale_after - (now - telemetry.timestamp)
            valid_frames = frames if remaining >= frames / self.sample_rate else max(0, math.floor(remaining * self.sample_rate) + 1)
        if self.valid and telemetry is not None:
            # The virtual gearing is deliberately fictional and not a CAN mapping.
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
        pcm = array.array("h")
        for index in range(frames):
            self.envelope = min(1.0, self.envelope + fade_step) if index < valid_frames else max(0.0, self.envelope - fade_step)
            if self.envelope == 0:
                pcm.extend((0, 0))
                continue
            self.phase = (self.phase + phase_step) % (2 * math.pi)
            self.whine_phase = (self.whine_phase + whine_step) % (2 * math.pi)
            wave = (math.sin(self.phase) + self.profile.harmonic_2 * math.sin(2 * self.phase)
                    + self.profile.harmonic_3 * math.sin(3 * self.phase))
            self.filter_state += coefficient * (wave - self.filter_state)
            whine = self.profile.turbo_mix * self.load * math.sin(self.whine_phase)
            shaped = math.tanh((self.filter_state * .9 + wave * .18 + whine) * (0.55 + self.load * .45))
            sample = max(-32767, min(32767, round(shaped * self.envelope * self.volume * 32767)))
            pcm.extend((sample, sample))
        if sys.byteorder != "little":
            pcm.byteswap()
        self.valid = self.valid and valid_frames == frames
        return pcm.tobytes()
