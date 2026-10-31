"""Check PCM and state equivalence against the pinned original Git revision.

Requires the baseline commit in the local Git object database; unlike CI's
shallow checkout, a developer worktree with full history can run this.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine_sound_lab.profiles import PROFILES
from engine_sound_lab.synth import EngineSynth
from engine_sound_lab.telemetry import Telemetry, synthetic_telemetry
from compare_synthesis import BASELINE_REF, load_baseline

FRAMES = 256
BLOCKS = 450
RATE = 48000

def main() -> None:
    reference = load_baseline(BASELINE_REF)
    checks = 0
    for profile in PROFILES.values():
        old = reference(profile)
        new = EngineSynth(profile)
        pcm = bytearray(FRAMES * 4)
        for i in range(BLOCKS):
            now = i * FRAMES / RATE
            if i % 19 in (0, 1):
                telemetry = None
            elif i % 41 == 2:
                telemetry = Telemetry(float("nan"), 10, now)
            elif i % 47 == 3:
                telemetry = Telemetry(0.5, 40, now + 1)
            elif i % 53 == 4:
                telemetry = Telemetry(0.5, 40, now - 2)
            else:
                telemetry = synthetic_telemetry(now, now)
            expected = old.render(telemetry, now, FRAMES)
            new.render_into(telemetry, now, FRAMES, pcm)
            if pcm != expected:
                raise AssertionError(f"PCM mismatch for {profile.id} at block {i}")
            for field in ("rpm", "load", "phase", "whine_phase", "filter_state", "envelope", "valid"):
                if getattr(new, field) != getattr(old, field):
                    raise AssertionError(f"State mismatch for {profile.id} block {i}: {field}")
            checks += 1
        print(f"{profile.id}: {BLOCKS} matching blocks")
    print(f"VERIFIED: {checks} byte-identical blocks and matching synthesis states")

if __name__ == "__main__":
    main()
