# Windows desktop — real PortAudio callback smoke test (2026-10-31)

This is **real local audio device callback evidence**, not a synthetic paced loop. A low-level playback run was started on the owner's Windows DESKTOP with physical headphones connected. No vehicle, HELIX DSP, S3XY device or Raspberry Pi was accessed.

- Test path: optimized branch `fix/issue-13-low-allocation-audio`
- Python 3.14.10; `sounddevice` 0.5.6
- Backend: **Windows DirectSound**, stereo headset output (actual personal device name withheld from this public repository)
- Source: `i5_turbo` generated synthetic telemetry, 48,000 Hz, 256-frame buffers, 16-bit stereo
- Duration: 12 seconds; PCM volume limit configured **0.02**, with no system gain changes
- The endpoint's native default samplerate is 44,100 Hz. WASAPI refused a 48,000 Hz stream; DirectSound accepted it. Host-side format conversion and buffering may apply. It is **not** evidence for an exclusive-mode 48 kHz, 256-frame device configuration.

| PortAudio metric | Observed |
|---|---:|
| Callbacks | 2,290 |
| `output_underflows` reported by callback | 0 |
| Callback errors | 0 |
| Timing samples recorded / dropped | 2,290 / 0 |
| Callback synthesis over per-call frame period | 0 |
| Callback median | 0.2193 ms |
| Callback p95 | 0.2761 ms |
| Callback max | 0.4288 ms |
| Callback interval p95 | 15.6557 ms |
| Callback interval max | 31.3515 ms |
| PortAudio reported CPU load | 0.036264 |
| PortAudio reported output latency | 0.24 s |

The measured interval distribution reflects host callback scheduling/buffering and should **not** be mistaken for fixed 5.333 ms callback cadence. The reported output latency is a PortAudio estimate, not acoustic or accelerator-to-speaker latency.

The raw log including the privately named endpoint is stored locally at `D:\Downloads\TeslaEngineSoundLab-Pi4-Setup\Windows-Headphones-Test-Result.json` and intentionally **not committed**.

**Not yet verified:** human listening confirmation (audibility, distortion, clicks), repeatability of real output across all five profiles under sustained load, analog/USB Raspberry Pi output, Pi thermal/underrun testing, and any vehicle or HELIX integration. No physical vehicle-hardware authorization or validation is implied by this desktop smoke test.
