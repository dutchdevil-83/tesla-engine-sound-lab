import array
import math
import subprocess
import sys
import tempfile
import unittest
import wave
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path

from engine_sound_lab.profiles import PROFILES
from engine_sound_lab.runtime import benchmark, play_synthetic, render_wav
from engine_sound_lab.synth import EngineSynth
from engine_sound_lab.telemetry import Telemetry, synthetic_telemetry


def samples(data: bytes) -> array.array:
    result = array.array("h")
    result.frombytes(data)
    if sys.byteorder != "little":
        result.byteswap()
    return result


class TelemetryTests(unittest.TestCase):
    def test_fresh_range_and_invalid_values(self):
        self.assertTrue(Telemetry(.5, 50, 10).valid_at(10.1, .25))
        for value in (Telemetry(float("nan"), 10, 10), Telemetry(-.1, 10, 10),
                      Telemetry(.5, 301, 10), Telemetry(.5, 10, 11)):
            self.assertFalse(value.valid_at(10, .25))
        self.assertFalse(Telemetry(.5, 10, 10).valid_at(10.3, .25))
        self.assertFalse(Telemetry(.5, 10, 10).valid_at(float("nan"), .25))

    def test_synthetic_cycle_is_bounded(self):
        for t in range(120):
            self.assertTrue(synthetic_telemetry(t / 10, t / 10).valid_at(t / 10, .25))


class SynthTests(unittest.TestCase):
    def test_profiles_are_deterministic_distinct_and_bounded(self):
        signal = Telemetry(.8, 70, 1)
        outputs = []
        for profile in PROFILES.values():
            first = EngineSynth(profile).render(signal, 1, 4096)
            second = EngineSynth(profile).render(signal, 1, 4096)
            self.assertEqual(first, second)
            values = samples(first)
            self.assertEqual(len(values), 8192)
            self.assertGreater(max(map(abs, values)), 0)
            self.assertLessEqual(max(map(abs, values)), round(.18 * 32767))
            self.assertEqual(values[::2], values[1::2])
            outputs.append(first)
        self.assertEqual(len(set(outputs)), len(PROFILES))

    def test_stale_invalid_and_missing_input_fade_to_exact_silence(self):
        engine = EngineSynth(PROFILES["v8_na"], sample_rate=8000, fade_seconds=.05)
        active = samples(engine.render(Telemetry(.8, 60, 0), 0, 800))
        self.assertGreater(max(map(abs, active)), 0)
        faded = samples(engine.render(Telemetry(.8, 60, 0), 1, 800))
        self.assertEqual(list(faded[-100:]), [0] * 100)
        self.assertEqual(set(samples(engine.render(None, 2, 128))), {0})
        self.assertEqual(set(samples(engine.render(Telemetry(math.nan, 0, 2), 2, 128))), {0})

    def test_sample_expiring_inside_long_block_fades_to_silence(self):
        engine = EngineSynth(PROFILES["i5_turbo"], sample_rate=8000, stale_after=.1, fade_seconds=.05)
        output = samples(engine.render(Telemetry(.8, 60, 0), 0, 2400))
        self.assertGreater(max(map(abs, output[:1600])), 0)
        self.assertEqual(set(output[-800:]), {0})
        self.assertFalse(engine.valid)

    def test_invalid_configuration_rejected(self):
        for kwargs in ({"volume": float("nan")}, {"volume": .51}, {"fade_seconds": 0}, {"sample_rate": 1}):
            with self.assertRaises(ValueError):
                EngineSynth(PROFILES["v12"], **kwargs)
        with self.assertRaises(ValueError):
            EngineSynth(PROFILES["v12"]).render(None, 0, -1)

    def test_wav_output_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.wav"
            self.assertEqual(render_wav(path, PROFILES["i5_turbo"], 1, .18), 48000)
            with wave.open(str(path), "rb") as wav:
                self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()), (2, 2, 48000, 48000))
                self.assertNotEqual(set(wav.readframes(24000)), {0})
                wav.setpos(47900)
                self.assertEqual(set(wav.readframes(100)), {0})
            with self.assertRaises(FileExistsError):
                render_wav(path, PROFILES["i5_turbo"], 1, .18)

    def test_benchmark_reports_timing_without_claiming_latency(self):
        result = benchmark(PROFILES["inline_six"], blocks=5)
        self.assertEqual(result["blocks"], 5)
        self.assertGreaterEqual(result["max_ms"], result["p95_ms"])
        self.assertGreater(result["block_period_ms"], 0)

    def test_cli_rejects_out_of_range_volume(self):
        result = subprocess.run([sys.executable, "-m", "engine_sound_lab", "render", "--volume", "nan", "--output", "unused.wav"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(Path("unused.wav").exists())

    def test_cli_renders_a_new_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cli.wav"
            result = subprocess.run([sys.executable, "-m", "engine_sound_lab", "render", "--seconds", "1", "--output", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(path.is_file())

    def test_live_callback_uses_stereo_pcm_and_stops(self):
        class CallbackStop(Exception):
            pass
        class FakeStream:
            def __init__(self, **kwargs):
                self.callback = kwargs["callback"]
                self.active = False
                self.settings = kwargs
                self.buffers = []
            def __enter__(self):
                for _ in range(2):
                    out = bytearray(256 * 4)
                    try:
                        self.callback(out, 256, None, SimpleNamespace(output_underflow=False))
                    except CallbackStop:
                        pass
                    self.buffers.append(bytes(out))
                return self
            def __exit__(self, *_):
                return False
        fake = SimpleNamespace(RawOutputStream=FakeStream, CallbackStop=CallbackStop)
        with patch.dict(sys.modules, {"sounddevice": fake}), patch("engine_sound_lab.runtime.time.monotonic", side_effect=[10.0, 11.1, 11.2]):
            stats = play_synthetic(PROFILES["i5_turbo"], 1, .18)
        self.assertEqual(stats["callbacks"], 2)
        self.assertEqual(stats["callback_errors"], 0)

    def test_callback_failure_fills_silence_and_reports_failure(self):
        observed = []
        class CallbackStop(Exception):
            pass
        class FakeStream:
            def __init__(self, **kwargs):
                self.callback = kwargs["callback"]
                self.active = False
            def __enter__(self):
                output = bytearray([255] * 1024)
                try:
                    self.callback(output, 256, None, SimpleNamespace(output_underflow=False))
                except CallbackStop:
                    observed.append(bytes(output))
                return self
            def __exit__(self, *_):
                return False
        fake = SimpleNamespace(RawOutputStream=FakeStream, CallbackStop=CallbackStop)
        with patch.dict(sys.modules, {"sounddevice": fake}), patch.object(EngineSynth, "render", side_effect=RuntimeError("test")):
            with self.assertRaisesRegex(RuntimeError, "silenced"):
                play_synthetic(PROFILES["i5_turbo"], 1, .18)
        self.assertEqual(observed, [bytes(1024)])


if __name__ == "__main__":
    unittest.main()
