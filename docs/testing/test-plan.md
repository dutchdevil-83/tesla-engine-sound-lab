# Test plan and report template

## Bench acceptance tests

| Test ID | Requirement | Procedure | Acceptance | Result/evidence |
|---|---|---|---|---|
| TEST-DATA-01 | REQ-SAF-001 | Feed valid, stale, malformed and out-of-range synthetic telemetry | Invalid/stale values cause bounded fade to mute; no stuck sound | Not run |
| TEST-AUDIO-01 | REQ-AUD-001 | Play independent analog and optical sources through verified DSP routing | Both audible continuously with no source switch | Not run |
| TEST-MUTE-01 | REQ-DSP-001 | Change digital source volume/mute using intended control | Digital contribution mutes; analog remains unchanged | Not run |
| TEST-OPT-01 | REQ-AUD-001 | Output 48 kHz stereo PCM from Pi interface | Stable optical lock, no underruns for agreed interval | Not run |
| TEST-LAT-01 | REQ-LAT-001 | Timestamp input edge and capture acoustic response | p95 <50 ms, uncertainty reported, no unacceptable dropouts | Not run |
| TEST-POWER-01 | REQ-PWR-001 | Simulate power loss and controlled shutdown | No filesystem corruption or parked draw outside approved limit | Not run |

## Report template

- Test ID / requirement IDs:
- Date, operator and environment:
- Hardware revisions and software/firmware:
- Equipment/calibration:
- Preconditions and safety controls:
- Exact procedure:
- Raw measurements and uncertainty:
- Pass/fail against criterion:
- Deviations, defects and risk impact:
- Evidence file location (sanitized):
- Reviewer/sign-off:
