# Issue 13 — Windows DESKTOP validation (2026-10-31)

This record describes tests actually executed on the owner's DESKTOP using the isolated worktree `X:\dev\worktrees\tesla-engine-sound-lab-issue13`, branch `fix/issue-13-low-allocation-audio`. Main remained unchanged. Python 3.14.10, reported platform `Windows-11-10.0.29698-SP0`.

## Result

- Patch applied cleanly to pinned main `efb3718835b9e673b4d8d0626d7ada98b50acc5c`.
- 20/20 tests passed using `py -3 -m unittest discover -s tests -v`.
- An initial optimized, synthesis-only benchmark of 200 blocks: median 0.14045 ms, p95 0.146 ms, max 0.2225 ms, 0 processing-period exceedances.
- Actual local A/B comparisons were measured using `software/tools/compare_synthesis.py`, baseline source pinned to `8bfbf745bf2c42c07347660cc7eec485cdf12ebf`. Each consecutive A/B variant/profile had 4 runs x 200 measured blocks plus 50 warm-ups per run.

| Profile | Baseline mean of run medians (ms) | Optimized mean of run medians (ms) | Change | Baseline / optimized processing-period exceedances |
|---|---:|---:|---:|---|
| i5_turbo | 0.1908 | 0.1453 | -23.9% | 0 / 0 |
| inline_six | 0.1883 | 0.1434 | -23.9% | 0 / 0 |
| v8_na | 0.1911 | 0.1438 | -24.7% | 0 / 0 |
| v8_turbo | 0.1893 | 0.1433 | -24.3% | 0 / 0 |
| v12 | 0.1913 | 0.1439 | -24.8% | 0 / 0 |

## Paced A/B

Synthetic software pacing was tested for `i5_turbo` and `v12`, each 4 x 200 measured blocks per variant, 50 warm-ups. A *paced deadline miss* is not a PortAudio hardware underflow.

| Profile and path | Mean of run medians synthesis (ms) | Inferred deadline misses | Synthesis over-period blocks | Max wake lateness (ms) | Max synth (ms) |
|---|---:|---:|---:|---:|---:|
| i5_turbo baseline | 0.2146 | 0 | 0 | 0.557 | 0.520 |
| i5_turbo optimized | 0.1563 | 0 | 0 | 0.542 | 0.392 |
| v12 baseline | 0.2108 | 0 | 0 | 0.842 | 0.508 |
| v12 optimized | 0.1634 | 0 | 0 | 0.580 | 0.365 |

## Raw evidence

- `D:\Downloads\Tesla-Issue13-Windows-Consecutive-20261031.json`
- `D:\Downloads\Tesla-Issue13-Windows-Paced-20261031.json`
- `D:\Downloads\Tesla-Issue13-Patch-20261031-195608.log`

The data above are host-specific, short-duration snapshots. Device output/PortAudio underflows, playback, CPU/power/thermal stability and Raspberry Pi performance were not measured. No end-to-end vehicle audio latency claim is supported. No audio devices or car equipment were used. No commit, push, merge or publication was performed.
