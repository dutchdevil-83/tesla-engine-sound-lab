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
