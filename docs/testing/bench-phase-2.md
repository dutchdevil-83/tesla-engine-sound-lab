# Phase 2 — lower-allocation audio path and timing evidence

**Scope:** [Issue #13](https://github.com/dutchdevil-83/tesla-engine-sound-lab/issues/13). Synthetic telemetry only; offline Python bench implementation. No connection to a Tesla, S3XY Commander, Raspberry Pi, HELIX DSP, vehicle network, sound device, or optical output was made during this investigation.

## Implementation and invariants

- `EngineSynth.render_into(signal, now, frames, writable_buffer)` fills a caller-owned, interleaved 16-bit stereo buffer of exactly `frames * 4` bytes. The old `render()` API remains for compatibility.
- The callback writes directly to the PortAudio output buffer. WAV export and both synthesis benchmarks reuse their buffers instead of constructing a new PCM array and converting it into bytes for each block.
- Synthetic telemetry is produced on the playback control thread and read from the callback. This is a bench-only, GIL-mediated handoff; it is **not a real-time synchronization strategy for the Pi**. Loss of refresh still reaches the existing stale-input fade.
- Callback timing records are allocated before opening the stream and summarized after the stream stops. Error-path silence is preallocated and the stream requests `CallbackAbort` when available to avoid draining queued audio; already-issued hardware output cannot be recalled.
- Existing five profiles, sample ordering, deterministic synthesis, bounded amplitude, invalid-input rejection, no overwrite, and fade-to-silence logic are retained.

Python object allocations and OS scheduling remain in the callback. **This is a reduced-allocation prototype, not a lock-free, zero-allocation, or hard-real-time engine.**

## Definitions: three different measurements

1. **Consecutive synthesis:** duration of `render()` or `render_into()` alone (without pacing or audio device). The 5.333 ms threshold is a computation-period comparison, not an actual underflow.
2. **Paced synthetic driver:** each block is scheduled using `perf_counter_ns()` and `sleep()`. `wake_*` measures lateness relative to planned start. `paced_deadline_misses` means final PCM was computed after its scheduled 5.333 ms deadline; it is an inferred deadline miss, **not** a hardware underflow.
3. **PortAudio callback:** when a real `RawOutputStream` is opened, `output_underflows` counts callback status reports. `callback_*` measures Python callback execution; `portaudio_cpu_load` and `portaudio_output_latency_s` are queried outside the callback when supported. Device, host API, acoustic and vehicle latency are not measured by the synthetic benchmarks.

## Isolated A/B benchmark, 31 October 2026

Environment: isolated Linux x86_64 container, Python 3.13.5, five logical CPUs reported by the container. The OS/CPU scheduling, competing load, thermal state and power behavior were not controlled. This is **not** a run on the owner's Windows desktop or a Raspberry Pi.

Baseline synthesis source was reconstructed from GitHub `8bfbf745bf2c42c07347660cc7eec485cdf12ebf` and its Git blob hash independently matched `fc5e55c1445069fe8d99c124c2d495861cfa2635`. The local reconstructed snapshot has a different commit hash from GitHub, as noted in the raw JSON. The comparison driver uses the same 50-block warm-up, 200 measured blocks, samples and timing loop for each side, with alternating execution order. Python code is the only runtime change. Values below are **median of per-run medians**, not a pooled percentile.

| Profile | Baseline consecutive median (ms) | Optimized consecutive median (ms) | Relative change |
|---|---:|---:|---:|
| `i5_turbo` | 0.219 | 0.155 | -29% |
| `inline_six` | 0.217 | 0.155 | -29% |
| `v8_na` | 0.227 | 0.157 | -31% |
| `v8_turbo` | 0.223 | 0.155 | -30% |
| `v12` | 0.228 | 0.157 | -31% |

Each entry reflects four runs of 200 measured blocks; 800 blocks per variant/profile. In this sample, the baseline had one over-budget block (`v12`, 6.123 ms maximum); the optimized path had zero over-budget blocks across those consecutive measurements. This does **not** imply that a zero-overrun rate is sustained under other scheduling conditions.

**Paced A/B:** three runs of 200 blocks each, using the same driver. `i5_turbo` had 0 inferred deadline misses for either implementation. `v12` had 9 baseline deadline misses and 69 optimized deadline misses, despite the optimized median synthesis time dropping from approximately 0.269 ms to 0.187 ms. The optimized `v12` run experienced a 290.28 ms maximum late wake-up and 154.09 ms maximum synthesis wall time; the baseline `v12` maximum wake-up lateness was 49.26 ms. This outlier is consistent with a heavily interfered host scheduling interval, but its root cause is unproven. Two optimized `v12` blocks exceeded 5.333 ms of synthesis duration versus one baseline block. These large differences demonstrate that median improvement does **not** establish reliable deadline behavior.

**Allocations:** a separate exploratory `tracemalloc` check over 200 blocks reported approximately 3,413 bytes baseline versus 2,184 bytes optimized *peak Python-traced memory above the initial traced level*, for the tested profiles. This is not total process RSS, C-library allocation, or the cumulative number of allocations; interpret it only as a limited corroborating observation. The main structural win is avoiding the per-block PCM array and bytes copy in the callback.

The full individual-run evidence is in [`bench-phase-2-consecutive.json`](bench-phase-2-consecutive.json) and [`bench-phase-2-paced.json`](bench-phase-2-paced.json). The same benchmark driver is shipped in `software/tools/compare_synthesis.py`.

## Reproduction

From `software/` with Python 3.10+ and Git available, with **no vehicle or audio device**:

```powershell
& {
    Set-Location -LiteralPath 'X:\dev\worktrees\tesla-engine-sound-lab-issue13\software'
    py -3 -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed.' }
    py -3 -m engine_sound_lab benchmark --profile i5_turbo --paced --blocks 200 --runs 4 --warmup 50
    if ($LASTEXITCODE -ne 0) { throw 'Paced benchmark failed.' }
    py -3 tools/compare_synthesis.py --baseline-ref 8bfbf745bf2c42c07347660cc7eec485cdf12ebf --profiles i5_turbo v12 --blocks 200 --warmup 50 --runs 4 --paced --output 'D:\Downloads\Tesla-Issue13-Paced.json'
    if ($LASTEXITCODE -ne 0) { throw 'Read-only A/B comparison failed.' }
}
```

The comparison tool reads the baseline via `git show` and never checks it out, resets a branch or downloads files. Its `--output` option refuses to overwrite an existing file. Run the test repeatedly under recorded idle, load and thermal conditions. Keep individual results instead of selecting the best run.

Local callback instrumentation (optional **desktop-only** audio playback, requiring an explicitly selected working output device) can be tested with `python -m engine_sound_lab play --profile i5_turbo --seconds 12 --volume 0.10`; use a safe low hardware volume. This test was **not run** for this report.

## Verification and remaining acceptance gates

| Verification | Result |
|---|---|
| Original 12 unit tests | Passed against reconstructed baseline and new code |
| Eight additional tests: buffer reuse/validation, profiles/fade/expiry, paced deadline accounting, fake PortAudio underflow, partial-error silence | Passed |
| Bit-identical output against pinned baseline | Passed for 450 consecutive blocks × five profiles (2,250 blocks), including intermittent missing telemetry |
| Synthetic benchmark runs and raw evidence | Completed on isolated Linux host, with scheduling outliers |
| Actual PortAudio underflow testing | **Not run**; only mock callback-status tests passed |
| Real audible playback | **Not run** |
| Raspberry Pi 4 benchmarks, ALSA, thermal/load stress | **Not run** |
| S/PDIF, HELIX, vehicle data, safety sounds, end-to-end latency | **Not run**; remain separate authorization/commissioning gates |

**Disposition:** code change suitable for local review/testing, **not** Raspberry Pi or vehicle acceptance. Further target work must measure actual PortAudio/ALSA underflows and CPU/thermal behavior over sustained durations under representative loads. If callback deadlines remain unreliable, evaluate moving synthesis into a bounded native DSP worker with an explicitly tested queue, maintaining the stale-input mute invariant.

## Primary references

- [Issue #13 — missed block deadlines](https://github.com/dutchdevil-83/tesla-engine-sound-lab/issues/13), opened 2026-10-31.
- [PortAudio callback contract](https://files.portaudio.com/docs/v19-doxydocs/portaudio_8h.html), accessed 2026-10-31; warns against unpredictable callback work and requires buffers to be filled.
- [python-sounddevice raw output callback](https://python-sounddevice.readthedocs.io/en/latest/api/raw-streams.html), accessed 2026-10-31.
- [python-sounddevice stream timing/status/abort](https://python-sounddevice.readthedocs.io/en/latest/api/streams.html), accessed 2026-10-31; documents callback flags, `CallbackStop`, `CallbackAbort`, and reported stream latency.
