# Software phase 1 — synthetic telemetry bench evidence

## Scope and requirements

| ID | Phase 1 implementation | Test / evidence | Status |
|---|---|---|---|
| REQ-OFF-001 | Procedural synthesis and WAV render use Python standard library; optional PortAudio playback has no network runtime calls. | Unit tests and network-free code inspection | Bench implementation; isolation test on target Pi pending |
| REQ-SAF-001 | Validate timestamp/range/finiteness; stale, invalid or missing data fades to silence, including expiration within a block. | `test_engine.py` | Verified in synthetic unit tests; hardware integration pending |
| REQ-LAT-001 | 256-frame block benchmark reports median/p95/max and blocks beyond the block period. | `python -m engine_sound_lab benchmark` | Synthesis-only measurement; end-to-end target remains unverified |
| REQ-CAN-001 | No CAN or network adapter is implemented. | Repository inspection | Vehicle interface not implemented |

## Phase 1 software acceptance

- [x] Five original deterministic profiles and synthetic acceleration/overrun cycle.
- [x] Stereo 48 kHz/16-bit WAV render with no overwrite of existing files.
- [x] Optional local PortAudio callback path, exercised using a simulated stream in unit tests.
- [x] Invalid/stale signal fade, bounded PCM and deterministic output tested.
- [x] Synthesis benchmark and CLI input validation.
- [ ] Real audio output on the user's computer verified.
- [ ] Raspberry Pi execution, optical output, thermal/load/underrun testing.
- [ ] Live vehicle telemetry, HELIX routing, warning audio and acoustic latency.

Checked boxes describe software implementation and tests only. They do not indicate vehicle readiness. The Pi bench and physical integration acceptance criteria remain open.

## Reproducible evidence

From `software/`, run `python -m unittest discover -s tests -v`, then `python -m engine_sound_lab benchmark --profile i5_turbo`. Record OS, Python version, CPU, power mode, block size, median, p95, maximum and over-budget blocks for each test. The printed synthesis measurements cannot be compared directly to the <50 ms accelerator-to-audible target.

## Sources

- [Python `wave` module](https://docs.python.org/3/library/wave.html), checked 2026-10-31.
- [python-sounddevice raw stream API](https://python-sounddevice.readthedocs.io/en/latest/api/raw-streams.html), checked 2026-10-31. Actual output device configuration is not yet verified.

## Desktop measurement — 2026-10-31

On the user's Windows desktop with Python 3.14.10, 12 unit tests passed and a 12-second WAV was rendered successfully. The optional `sounddevice` 0.5.6 package and PortAudio loaded, and output devices were enumerated; **no audible playback test was performed**.

Four synthesis-only measurements each processed 200 consecutive 256-frame blocks (5.333 ms per block). The first run exceeded that period for 13 blocks. Three subsequent runs recorded:

| Run | Median | p95 | Maximum | Blocks over 5.333 ms |
|---|---:|---:|---:|---:|
| 1 | 0.409 ms | 0.867 ms | 4.269 ms | 0 |
| 2 | 0.543 ms | 4.079 ms | 22.817 ms | 9 |
| 3 | 0.709 ms | 7.131 ms | 16.233 ms | 19 |

These are wall-clock measurements under uncontrolled desktop load and include operating-system scheduling. They are not PortAudio callback underrun measurements and do not demonstrate Raspberry Pi performance or end-to-end latency. The variability and missed block periods prevent treating this Python implementation as a validated real-time engine. Repeated paced playback tests, scheduling analysis and an optimized implementation are outstanding.
