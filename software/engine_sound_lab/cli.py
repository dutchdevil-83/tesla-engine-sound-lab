"""Command-line entry point for the offline bench prototype."""

import argparse
import json
import math
import sys
from pathlib import Path
from .profiles import PROFILES
from .runtime import benchmark, play_synthetic, render_wav


def bounded_float(minimum: float, maximum: float):
    def parse(value: str) -> float:
        try:
            number = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be a number") from exc
        if not math.isfinite(number) or not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"must be between {minimum} and {maximum}")
        return number
    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline engine sound bench prototype; synthetic telemetry only")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("profiles", help="list original procedural profiles")
    for name in ("render", "play", "benchmark"):
        command = sub.add_parser(name)
        command.add_argument("--profile", choices=sorted(PROFILES), default="i5_turbo")
        if name != "benchmark":
            command.add_argument("--seconds", type=bounded_float(1, 60), default=12)
            command.add_argument("--volume", type=bounded_float(0, .5), default=.18)
        if name == "render":
            command.add_argument("--output", type=Path, required=True, help="new WAV path; existing files are never overwritten")
        if name == "play":
            command.add_argument("--device", help="optional PortAudio output device name")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "profiles":
        for profile in PROFILES.values():
            print(f"{profile.id:12} {profile.label}")
        return 0
    try:
        profile = PROFILES[args.profile]
        if args.command == "render":
            frames = render_wav(args.output, profile, args.seconds, args.volume)
            print(f"Wrote {frames} stereo frames at 48000 Hz to {args.output}")
        elif args.command == "benchmark":
            print(json.dumps(benchmark(profile), indent=2))
            print("Synthesis timing only; not accelerator-to-speaker latency.")
        else:
            print("Synthetic audio will play on the selected local output. Start with the output volume low.")
            print(json.dumps(play_synthetic(profile, args.seconds, args.volume, args.device)))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
