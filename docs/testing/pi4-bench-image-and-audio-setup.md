# Raspberry Pi 4 — offline engine sound bench image and audio verification

**Purpose:** prepare a dedicated Raspberry Pi 4 test card and install the *synthetic-only* engine generator. This is not a vehicle-ready image, installer, background service, or hardware integration. Do not connect the Pi to the Tesla, S3XY Commander, vehicle networks or installed HELIX DSP.

## Verified OS media prepared on Windows DESKTOP — 2026-10-31

- Raspberry Pi Imager **v2.0.12** for Windows (upstream [release](https://github.com/raspberrypi/rpi-imager/releases/tag/v2.0.12)), SHA-256 `98bff90afe23339d0768915f6f68d35ac254740ec1eac2082ebeaa9ba41bc8e3`.
- Raspberry Pi OS **Lite 64-bit**, Debian 13 (Trixie), **2026-10-06** dated release, SHA-256 compressed image `483db18a48da399b5b7022ffae9a07bc6d99daab30e593aedac09b69ff422843`. [Official OS download listing](https://www.raspberrypi.com/software/operating-systems/).
- Files are placed in `D:\Downloads\TeslaEngineSoundLab-Pi4-Setup` (once each SHA-256 verification completes). They are **not a pre-flashed or personalized card**.
- On 2026-10-31, Windows reported *no removable SD storage*; therefore no flash, disk initialization or boot verification was performed.

## 1. Image a dedicated microSD card (Windows DESKTOP)

Use a **spare microSD card, 16 GB minimum, 32 GB or more recommended**; image writing **erases the entire selected card**. Do not select an internal NVMe/SATA drive or an SD card containing data you want to keep.

1. Connect the microSD card through a reader. Confirm its reported make/capacity and that it contains no data you need.
2. Start `D:\Downloads\TeslaEngineSoundLab-Pi4-Setup\imager-v2.0.12.exe` to install Raspberry Pi Imager if it is not already installed, then launch Imager.
3. Choose **Raspberry Pi 4** as the device. For the OS choose **Use custom** and point to `D:\Downloads\TeslaEngineSoundLab-Pi4-Setup\2026-10-06-raspios-trixie-arm64-lite.img.xz`.
4. Select **only the identified removable microSD card** as storage. Review the capacity and device name carefully; no unattended disk selection.
5. In Imager's OS customization, select a unique hostname (e.g. `engine-sound-lab`), **Europe/Amsterdam** timezone, a new non-default user, SSH enabled with your **public SSH key** (prefer key-only login), and wired Ethernet when possible. If using Wi-Fi, enter its credentials in the private Imager UI. Never store passwords, keys or SSIDs in this repository.
6. Review the **destructive erase warning**, then manually approve **Write** and **Verify**. Eject the card properly.
7. Insert card in Pi 4, connect **test speaker/headphones only** (analog 3.5 mm or a supported USB DAC), Ethernet and suitable Pi 4 power. Do not connect the HELIX installation or vehicle equipment.

Raspberry Pi Imager customizes credentials and SSH before first boot; the standard OS image alone does **not** include your application. Follow the [official imaging and headless setup documentation](https://www.raspberrypi.com/documentation/computers/getting-started.html).

## 2. Install the engine and dependencies on the Pi

Connect via SSH to your configured hostname/IP from an authorized computer. These are the packages automatically installed by the script:

| Package | Purpose |
| --- | --- |
| `python3`, `python3-venv`, `python3-pip` | Isolated Python environment |
| `git`, `ca-certificates` | Fetch the PR branch over HTTPS during initial provisioning |
| `libportaudio2`, `portaudio19-dev`, `libasound2-dev`, `libffi-dev` | PortAudio/ALSA and Python audio dependency support |
| `alsa-utils` | Enumerate/test local audio outputs |
| `stress-ng` | Optional CPU load during target benchmarks |
| `sounddevice==0.5.6` and editable `software[audio]` | Test audio driver and this application in a Python venv |

Run the following **after the optimization PR branch is pushed**:

```bash
git clone --branch fix/issue-13-low-allocation-audio \
  https://github.com/dutchdevil-83/tesla-engine-sound-lab.git
cd tesla-engine-sound-lab
bash software/tools/pi/setup-pi-bench.sh
```

The setup script updates/install packages, creates `.venv`, installs the Python application, runs the 20-test suite, lists available devices and saves evidence in `~/tesla-engine-sound-lab-evidence`. Provisioning needs internet access for `apt`/`pip` and Git; **runtime synthesis is offline**. The script does not configure audio auto-start, remote access, a vehicle connection or background services.

## 3. Check audio routing without playback

```bash
aplay -l
./.venv/bin/python -m sounddevice
vcgencmd measure_temp
vcgencmd get_throttled
```

Choose a physical audio device that you can identify. If using the Pi 4 analog headphone jack, verify that its analog output is enabled in Raspberry Pi OS audio configuration; a stereo USB DAC is an acceptable alternative. The Pi 4's 3.5 mm TRRS jack is **line-level**, not a powered speaker output; use powered speakers/headphones at safe volume. The exact audio-device name, sample rate and driver should be recorded.

## 4. Timed synthesis and actual audible output

With `./.venv/bin/python` and from the repository root:

```bash
for profile in i5_turbo inline_six v8_na v8_turbo v12; do
  ./.venv/bin/python -m engine_sound_lab benchmark \
    --profile "$profile" --paced --blocks 200 --runs 4
done
```

For an **explicitly selected local output device** and after setting a low physical gain, run:

```bash
./.venv/bin/python -m engine_sound_lab play \
  --profile i5_turbo --seconds 12 --volume 0.03 --device "YOUR_DEVICE_NAME"
```

If correct and safe, repeat `--seconds 60` for all five profiles. Record each run's `output_underflows`, `callback_errors`, callback timing, CPU load/latency when available, the actual output selection, temperature and `vcgencmd get_throttled`. Report whether you **personally heard** clean output, fade and any clicks/interruptions: software cannot confirm acoustic output without a listening or measurement device. If output is too loud, stop the test and reduce hardware gain.

For an optional short stress interval, run `stress-ng --cpu 2 --timeout 120s` in a separate SSH session while running paced benchmarks; monitor temperature and throttling. Keep full logs for every run, including failures. Do not assert 30-minute continuous playback acceptance from repeated 60-second invocations: the current stream API opens/closes between invocations.

## Acceptance gate

- Bench software: all tests pass, input-loss fade and bounded output preserved.
- Audio: listening confirmation plus repeated **real PortAudio callback** evidence, not solely synthetic pacing.
- Pi: sustained measurements under representative load, temperature, power/throttling, and repeatability across profiles.
- **Still excluded:** vehicle interfaces, HELIX/S/PDIF routing, warning-audio priority, actual end-to-end accelerator-to-speaker latency and automotive qualification. These need separate review, safe controls and authorization.

Relevant references: [official Raspberry Pi OS](https://www.raspberrypi.com/documentation/computers/os.html), [Raspberry Pi Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html), [sounddevice raw streams](https://python-sounddevice.readthedocs.io/en/latest/api/raw-streams.html).
