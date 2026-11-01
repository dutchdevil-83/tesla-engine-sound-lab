"""Allocation path, deterministic deadline and fake PortAudio status tests."""

import array
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from engine_sound_lab.profiles import PROFILES
from engine_sound_lab.runtime import BLOCK_PERIOD_NS, benchmark_paced, play_synthetic
from engine_sound_lab.synth import EngineSynth
from engine_sound_lab.telemetry import Telemetry, synthetic_telemetry


class SyntheticClock:
    def __init__(self):
        self.ns = 0

    def perf_counter_ns(self):
        return self.ns

    def monotonic(self):
        return self.ns / 1_000_000_000

    def sleep(self, seconds):
        self.ns += round(seconds * 1_000_000_000)


class BufferTests(unittest.TestCase):
    def test_render_into_matches_legacy_bytes_for_every_profile_and_reuses_buffer(self):
        for profile in PROFILES.values():
            with self.subTest(profile=profile.id):
                old_style = EngineSynth(profile)
                low_allocation = EngineSynth(profile)
                pcm = bytearray(1024)
                object_id = id(pcm)
                for index in range(75):
                    now = index * 256 / 48000
                    signal = synthetic_telemetry(now, now) if index % 11 < 7 else None
                    expected = old_style.render(signal, now, 256)
                    low_allocation.render_into(signal, now, 256, pcm)
                    self.assertEqual(pcm, expected)
                    self.assertEqual(id(pcm), object_id)
                self.assertEqual((old_style.envelope, old_style.phase, old_style.valid),
                                 (low_allocation.envelope, low_allocation.phase, low_allocation.valid))

    def test_bad_buffers_rejected_before_state_mutation(self):
        synth = EngineSynth(PROFILES["i5_turbo"])
        signal = Telemetry(.7, 40, 0)
        state = (synth.rpm, synth.load, synth.envelope, synth.valid)
        for bad_buffer in (bytes(1024), bytearray(1023),
                           memoryview(bytearray(2048))[::2]):
            with self.subTest(type=type(bad_buffer).__name__):
                with self.assertRaises(ValueError):
                    synth.render_into(signal, 0.0, 256, bad_buffer)
                self.assertEqual((synth.rpm, synth.load, synth.envelope, synth.valid), state)
        with self.assertRaises(ValueError):
            synth.render_into(signal, 0.0, -1, bytearray(1024))

    def test_partial_buffer_and_fades_stay_bounded_for_all_profiles(self):
        for profile in PROFILES.values():
            with self.subTest(profile=profile.id):
                engine = EngineSynth(profile, sample_rate=8000, fade_seconds=.05)
                pcm = bytearray(400 * 4)
                engine.render_into(Telemetry(.9, 90, 0), 0.0, 400, pcm)
                self.assertNotEqual(set(pcm), {0})
                for bad_input in (None, Telemetry(float("nan"), 0, 2),
                                  Telemetry(.9, 0, 3), Telemetry(.9, 0, 1)):
                    # Every invalid/missing/stale segment must eventually mute.
                    engine.render_into(bad_input, 2.0, 400, pcm)
                    engine.render_into(bad_input, 2.05, 400, pcm)
                    self.assertEqual(set(pcm), {0})
                signal = Telemetry(1, 300, 2)
                engine.render_into(signal, 2, 400, pcm)
                pcm_array = array.array("h")
                pcm_array.frombytes(pcm)
                if sys.byteorder != "little":
                    pcm_array.byteswap()
                self.assertLessEqual(max(map(abs, pcm_array)), round(.18 * 32767))

    def test_expiry_mid_buffer_fades_completely(self):
        engine = EngineSynth(PROFILES["v12"], sample_rate=8000,
                             stale_after=.1, fade_seconds=.05)
        pcm = bytearray(2400 * 4)
        engine.render_into(Telemetry(.7, 70, 0), 0, 2400, pcm)
        self.assertNotEqual(set(pcm[:1000]), {0})
        self.assertEqual(set(pcm[-800:]), {0})
        self.assertFalse(engine.valid)


class PacingTests(unittest.TestCase):
    def test_paced_runner_separates_late_wake_and_synthesis_overrun(self):
        clock = SyntheticClock()
        original = EngineSynth.render_into
        costs = iter([1_000_000, 6_000_000, 1_000_000])

        def fake_cost(engine, telemetry, now, frames, buffer):
            original(engine, telemetry, now, frames, buffer)
            clock.ns += next(costs)

        with patch.object(EngineSynth, "render_into", fake_cost):
            result = benchmark_paced(PROFILES["i5_turbo"], blocks=3, warmup_blocks=0,
                                     clock_ns=clock.perf_counter_ns, sleep=clock.sleep)
        self.assertEqual(result["over_budget_blocks"], 1)
        self.assertEqual(result["paced_deadline_misses"], 1)
        self.assertGreater(result["wake_max_ms"], 0)
        self.assertEqual(result["blocks"], 3)
        self.assertAlmostEqual(result["block_period_ms"], BLOCK_PERIOD_NS / 1e6, places=5)
        self.assertIn("no audio device", result["measurement"])

    def test_paced_runner_rejects_invalid_lengths(self):
        for kwargs in ({"blocks": 0}, {"blocks": 10001},
                       {"warmup_blocks": -1}, {"warmup_blocks": 5001}):
            with self.assertRaises(ValueError):
                benchmark_paced(PROFILES["v8_na"], **kwargs)


class PortAudioCallbackTests(unittest.TestCase):
    def test_fake_portaudio_underflow_and_processing_deadline_are_distinct(self):
        clock = SyntheticClock()
        audio_outputs = []

        class CallbackStop(Exception):
            pass

        class FakeStream:
            active = False

            def __init__(self, **kwargs):
                self.callback = kwargs["callback"]

            def __enter__(self):
                for i, underflow in enumerate((False, True)):
                    if i:
                        clock.ns += 1_100_000_000
                    output = bytearray(1024)
                    try:
                        self.callback(output, 256, None, SimpleNamespace(output_underflow=underflow))
                    except CallbackStop:
                        pass
                    audio_outputs.append(bytes(output))
                return self

            def __exit__(self, *_):
                return False

        original_render_into = EngineSynth.render_into
        processing_costs = iter([2_000_000, 7_000_000])

        def timed_render(engine, telemetry, now, frames, buffer):
            original_render_into(engine, telemetry, now, frames, buffer)
            clock.ns += next(processing_costs)

        fake = SimpleNamespace(RawOutputStream=FakeStream, CallbackStop=CallbackStop)
        with patch.dict(sys.modules, {"sounddevice": fake}), \
             patch("engine_sound_lab.runtime.time.monotonic", clock.monotonic), \
             patch("engine_sound_lab.runtime.time.perf_counter_ns", clock.perf_counter_ns), \
             patch.object(EngineSynth, "render_into", timed_render):
            result = play_synthetic(PROFILES["i5_turbo"], 1, .18)
        self.assertEqual(result["callbacks"], 2)
        self.assertEqual(result["output_underflows"], 1)
        self.assertEqual(result["callback_over_budget_blocks"], 1)
        self.assertEqual(result["timing_samples"], 2)
        self.assertEqual(result["timing_samples_dropped"], 0)
        self.assertGreaterEqual(result["callback_max_ms"], 7)
        self.assertNotEqual(set(audio_outputs[0]), {0})

    def test_callback_error_clears_partially_written_audio(self):
        audio_outputs = []
        aborts = []

        class CallbackStop(Exception):
            pass

        class CallbackAbort(Exception):
            pass

        class FakeStream:
            active = False

            def __init__(self, **kwargs):
                self.callback = kwargs["callback"]

            def __enter__(self):
                output = bytearray([255] * 1024)
                try:
                    self.callback(output, 256, None, SimpleNamespace(output_underflow=False))
                except CallbackAbort:
                    aborts.append(True)
                audio_outputs.append(output)
                return self

            def __exit__(self, *_):
                return False

        def partial_failure(_engine, _signal, _now, _frames, buffer):
            buffer[:16] = bytes([34] * 16)
            raise RuntimeError("synthetic failure")

        fake = SimpleNamespace(RawOutputStream=FakeStream,
                               CallbackStop=CallbackStop, CallbackAbort=CallbackAbort)
        with patch.dict(sys.modules, {"sounddevice": fake}), \
             patch.object(EngineSynth, "render_into", partial_failure):
            with self.assertRaisesRegex(RuntimeError, "silenced"):
                play_synthetic(PROFILES["v8_turbo"], 1, .18)
        self.assertEqual(audio_outputs, [bytes(1024)])
        self.assertEqual(aborts, [True])


if __name__ == "__main__":
    unittest.main()
