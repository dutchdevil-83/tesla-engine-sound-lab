# Engine Sound Lab — phase 1 bench prototype

The first software phase generates original procedural engine sounds from **synthetic telemetry only**. It can render a WAV file, benchmark synthesis blocks, or play the simulation on a local PortAudio output. There is no CAN, network, Tesla, Commander, DSP control or vehicle integration in this phase.

The output is a design prototype: profiles and virtual gearing are fictional sound-design parameters, not verified engine simulations. The lower-allocation callback still executes Python and can allocate bookkeeping objects; this is **not yet a hard-real-time or automotive-qualified implementation**. Pi performance, ALSA/optical compatibility, underruns, and accelerator-to-speaker latency remain unmeasured.

## Requirements

- Python 3.10 or newer. Offline WAV rendering, tests and benchmarking use only the standard library.
- Optional local playback: `sounddevice` 0.5.x and a working PortAudio output device. Installing this dependency requires a package source; normal playback uses no network.
- Start with your computer's output volume low. Do not connect this prototype to installed vehicle hardware without separate authorization.

## Windows quick start

Run from the existing checkout on **DESKTOP**. The render command creates a new file and refuses to overwrite an existing one.

```powershell
& {
    $projectPath = 'X:\dev\repos\personal\tesla-engine-sound-lab\software'
    if (-not (Test-Path -LiteralPath $projectPath)) { throw "Project folder not found: $projectPath" }
    Set-Location -LiteralPath $projectPath
    py -3 -m engine_sound_lab profiles
    py -3 -m engine_sound_lab render --profile i5_turbo --seconds 12 --output 'D:\Downloads\TeslaEngineSoundLab-i5-demo.wav'
    if ($LASTEXITCODE -ne 0) { throw 'WAV rendering failed; inspect the error above.' }
}
```

Expected result: a 48 kHz, 16-bit stereo WAV at the specified location. If it already exists, choose another filename; no existing file is overwritten.

## Optional playback on the local computer

```powershell
& {
    $projectPath = 'X:\dev\repos\personal\tesla-engine-sound-lab\software'
    if (-not (Test-Path -LiteralPath $projectPath)) { throw "Project folder not found: $projectPath" }
    Set-Location -LiteralPath $projectPath
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    & '.\.venv\Scripts\python.exe' -m pip install '.[audio]'
    if ($LASTEXITCODE -ne 0) { throw 'Optional audio dependency installation failed.' }
    & '.\.venv\Scripts\python.exe' -m sounddevice
    & '.\.venv\Scripts\python.exe' -m engine_sound_lab play --profile i5_turbo --seconds 12 --volume 0.10
    if ($LASTEXITCODE -ne 0) { throw 'Playback failed; check the selected audio device and PortAudio.' }
}
```

Use `--device "device name"` with `play` to choose a listed output. No sound will play until `play` is explicitly invoked. The `--volume` range is 0–0.5; it does not replace safe hardware gain control.

## Verification

```powershell
& {
    Set-Location -LiteralPath 'X:\dev\repos\personal\tesla-engine-sound-lab\software'
    py -3 -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Engine tests failed.' }
    py -3 -m engine_sound_lab benchmark --profile i5_turbo
    if ($LASTEXITCODE -ne 0) { throw 'Benchmark failed.' }
}
```

The default benchmark reports consecutive block synthesis time and missed 256-frame computation periods on the current computer. It excludes telemetry acquisition, operating-system scheduling, audio buffers, S/PDIF, HELIX processing and the speaker. It is **not** an end-to-end latency measurement.

## Lower-allocation callback and repeatable timing (issue #13)

`EngineSynth.render_into()` fills a reusable byte buffer directly; `render()` remains available. Playback creates synthetic telemetry outside the PortAudio callback and captures bounded processing times, callback intervals and PortAudio `output_underflows` status flags. Callback error silence is preallocated. Invalid/stale input still fades to silence. **Python remains non-real-time.**

Run a paced simulation with no audio device and compare against the pinned phase-1 implementation without resetting or modifying your checkout:

```powershell
& {
    Set-Location -LiteralPath 'X:\dev\repos\personal\tesla-engine-sound-lab\software'
    py -3 -m engine_sound_lab benchmark --profile i5_turbo --paced --blocks 200 --warmup 50 --runs 4
    if ($LASTEXITCODE -ne 0) { throw 'Paced timing benchmark failed.' }
    py -3 tools/compare_synthesis.py --profiles i5_turbo v12 --paced --runs 4 --output 'D:\Downloads\Tesla-Issue13-Paced.json'
    if ($LASTEXITCODE -ne 0) { throw 'Baseline comparison failed.' }
}
```

`paced_deadline_misses` are **not** actual audio underruns. Real `output_underflows` require a PortAudio device playback test. A 12-second, low-volume Windows DirectSound headphone callback test was performed: 2,290 callbacks, 0 reported output underflows, 0 callback errors; listening confirmation is still pending. See [Windows audio evidence](../docs/testing/bench-phase-2-windows-audio-20261031.md). Raspberry Pi performance remains unverified. See [phase-2 synthesis evidence](../docs/testing/bench-phase-2.md) and [Pi 4 image and setup](../docs/testing/pi4-bench-image-and-audio-setup.md) for the remaining test gates.

## Safety behavior and limits

- Telemetry values require finite pedal (0–1), speed (0–300 km/h), and fresh timestamps on the same monotonic clock. Missing, future, invalid or stale input fades output to exact silence. Validity is checked within a block, not only at block boundaries.
- The output uses bounded 16-bit stereo PCM and a configurable limit capped at 0.5. It does not replace measured DSP limits, speaker protection or commissioning.
- The demo generates its own data; it cannot access or command the car. Any future vehicle adapter must be separately reviewed and demonstrably receive-only.
- `play` uses Python's callback and records reported output underflows. Its allocation and scheduling behavior must be redesigned or proven suitable on the actual Pi before vehicle deployment.

Profiles: `i5_turbo`, `inline_six`, `v8_na`, `v8_turbo`, `v12`. Parameters are in [`engine_sound_lab/profiles.py`](engine_sound_lab/profiles.py). No recordings or third-party engine sound assets are included.

See [bench-phase-1.md](../docs/testing/bench-phase-1.md), [bench-phase-2.md](../docs/testing/bench-phase-2.md), [Pi 4 bench setup](../docs/testing/pi4-bench-image-and-audio-setup.md), and [issue #13](https://github.com/dutchdevil-83/tesla-engine-sound-lab/issues/13) for evidence and remaining work.
