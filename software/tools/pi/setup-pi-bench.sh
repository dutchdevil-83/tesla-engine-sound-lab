#!/usr/bin/env bash
# Pi 4 offline engine sound benchmark setup. Never starts audio or vehicle adapters.
set -Eeuo pipefail
if [[ "${EUID}" -eq 0 ]]; then echo 'Run as a non-root Raspberry Pi user.' >&2; exit 2; fi
if [[ "$(uname -m)" != "aarch64" ]]; then
  echo 'Requires Raspberry Pi OS 64-bit (aarch64).' >&2
  exit 2
fi
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../.." && pwd)"
software="$repo_root/software"
if [[ ! -f "$software/pyproject.toml" ]]; then
  echo 'Run the script from the cloned Tesla Engine Sound Lab repository.' >&2
  exit 2
fi
model='Unknown'
if [[ -r /proc/device-tree/model ]]; then model="$(tr -d '\000' < /proc/device-tree/model)"; fi
printf 'Hardware: %s\n' "$model"
if [[ "$model" != *'Raspberry Pi 4'* ]]; then
  echo 'WARNING: Target validation is specified for Raspberry Pi 4.' >&2
fi
if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  printf 'OS: %s\n' "${PRETTY_NAME:-unknown}"
fi
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  ca-certificates git python3 python3-venv python3-pip \
  libportaudio2 portaudio19-dev libasound2-dev libffi-dev \
  alsa-utils stress-ng
venv="$repo_root/.venv"
if [[ ! -x "$venv/bin/python" ]]; then python3 -m venv "$venv"; fi
"$venv/bin/python" -m pip install --disable-pip-version-check \
  -e "$software[audio]" 'sounddevice==0.5.6'
evidence="$HOME/tesla-engine-sound-lab-evidence"
mkdir -p -- "$evidence"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$evidence/setup-utc.txt"
uname -a > "$evidence/uname.txt"
"$venv/bin/python" --version > "$evidence/python-version.txt" 2>&1
"$venv/bin/python" -m pip freeze > "$evidence/python-packages.txt"
git -C "$repo_root" rev-parse HEAD > "$evidence/git-commit.txt"
"$venv/bin/python" -m unittest discover -s "$software/tests" -v 2>&1 | tee "$evidence/unit-tests.txt"
"$venv/bin/python" -m engine_sound_lab profiles | tee "$evidence/profiles.txt"
"$venv/bin/python" -m engine_sound_lab benchmark --profile i5_turbo \
  --paced --blocks 200 --runs 3 | tee "$evidence/initial-paced-benchmark.txt"
echo 'Audio output enumeration (no device opened):'
"$venv/bin/python" -m sounddevice | tee "$evidence/audio-devices.txt" || \
  echo 'WARNING: configure analog or USB audio output before playback.' >&2
aplay -l 2>&1 | tee "$evidence/alsa-devices.txt" || true
if command -v vcgencmd >/dev/null 2>&1; then
  vcgencmd measure_temp | tee "$evidence/temperature.txt"
  vcgencmd get_throttled | tee "$evidence/throttled.txt"
fi
printf '\nSetup complete. Evidence: %s\n' "$evidence"
echo 'No playback, car connectivity, routing changes or background service configured.'
