"""Compare pinned phase-1 synthesis against the current local implementation.

Read-only ``git show`` loads the baseline source: no checkout, download,
vehicle connectivity, audio device or working-tree modifications are needed.
Python execution remains subject to normal OS scheduling variability.
"""

import argparse
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
import types
from datetime import datetime, timezone
from pathlib import Path

SOFTWARE = Path(__file__).resolve().parents[1]
REPOSITORY = SOFTWARE.parent
sys.path.insert(0, str(SOFTWARE))

from engine_sound_lab.profiles import PROFILES  # noqa: E402
from engine_sound_lab.synth import EngineSynth  # noqa: E402
from engine_sound_lab.telemetry import synthetic_telemetry  # noqa: E402

BASELINE_REF = "8bfbf745bf2c42c07347660cc7eec485cdf12ebf"
FRAMES = 256
RATE = 48000
PERIOD_S = FRAMES / RATE
PERIOD_NS = round(FRAMES * 1_000_000_000 / RATE)


def git_text(*arguments: str) -> str:
    try:
        done = subprocess.run(["git", *arguments], cwd=REPOSITORY, check=True,
                              capture_output=True, text=True, encoding="utf-8")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"Unable to read pinned local git baseline: {exc}") from exc
    return done.stdout


def load_baseline(ref: str) -> type:
    # The imported source is a local, explicitly chosen repository revision.
    source = git_text("show", f"{ref}:software/engine_sound_lab/synth.py")
    module = types.ModuleType("engine_sound_lab._phase1_synth_reference")
    module.__package__ = "engine_sound_lab"
    exec(compile(source, f"{ref}:software/engine_sound_lab/synth.py", "exec"), module.__dict__)
    return module.EngineSynth


def _summary(values_ns: list[int]) -> dict[str, float | int]:
    ordered = sorted(values_ns)
    return {"median_ms": round(statistics.median(values_ns) / 1e6, 6),
            "p95_ms": round(ordered[math.ceil(.95 * len(ordered)) - 1] / 1e6, 6),
            "max_ms": round(ordered[-1] / 1e6, 6),
            "over_budget_blocks": sum(n > PERIOD_NS for n in values_ns)}


def run_variant(engine_type: type, profile_id: str, blocks: int,
                warmup: int, paced: bool, into: bool) -> dict[str, float | int]:
    engine = engine_type(PROFILES[profile_id])
    buffer = bytearray(FRAMES * 4)

    def render(now: float) -> None:
        signal = synthetic_telemetry(now, now)
        if into:
            engine.render_into(signal, now, FRAMES, buffer)
        else:
            engine.render(signal, now, FRAMES)

    for i in range(warmup):
        render(i * PERIOD_S)

    render_times_ns: list[int] = []
    wake_lateness_ns: list[int] = []
    deadline_misses = 0
    origin_ns = time.perf_counter_ns()
    for i in range(blocks):
        scheduled_ns = origin_ns + i * PERIOD_NS
        if paced:
            remaining = scheduled_ns - time.perf_counter_ns()
            if remaining > 0:
                time.sleep(remaining / 1e9)
        woke_ns = time.perf_counter_ns()
        logical_now = (i + warmup) * PERIOD_S
        signal = synthetic_telemetry(logical_now, logical_now)
        start_ns = time.perf_counter_ns()
        if into:
            engine.render_into(signal, logical_now, FRAMES, buffer)
        else:
            engine.render(signal, logical_now, FRAMES)
        end_ns = time.perf_counter_ns()
        render_times_ns.append(end_ns - start_ns)
        if paced:
            wake_lateness_ns.append(max(0, woke_ns - scheduled_ns))
            deadline_misses += end_ns > scheduled_ns + PERIOD_NS

    outcome = _summary(render_times_ns)
    if paced:
        ordered = sorted(wake_lateness_ns)
        outcome.update({"wake_median_ms": round(statistics.median(ordered) / 1e6, 6),
                        "wake_p95_ms": round(ordered[math.ceil(.95 * len(ordered)) - 1] / 1e6, 6),
                        "wake_max_ms": round(ordered[-1] / 1e6, 6),
                        "paced_deadline_misses": deadline_misses})
    return outcome


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only paired benchmark against the phase-1 commit")
    p.add_argument("--baseline-ref", default=BASELINE_REF)
    p.add_argument("--profiles", nargs="+", choices=sorted(PROFILES), default=list(PROFILES))
    p.add_argument("--blocks", type=int, default=200)
    p.add_argument("--runs", type=int, default=4)
    p.add_argument("--warmup", type=int, default=50)
    p.add_argument("--paced", action="store_true")
    p.add_argument("--output", type=Path, help="write JSON without overwriting an existing file")
    args = p.parse_args()
    if not 1 <= args.blocks <= 10000 or not 1 <= args.runs <= 20 or not 0 <= args.warmup <= 5000:
        p.error("blocks: 1-10000, runs: 1-20, warmup: 0-5000")
    try:
        baseline_type = load_baseline(args.baseline_ref)
        baseline_sha = git_text("rev-parse", "--verify", f"{args.baseline_ref}^{{commit}}").strip()
        current_sha = git_text("rev-parse", "HEAD").strip()
        result = {"run_utc": datetime.now(timezone.utc).isoformat(),
                  "machine": platform.platform(), "python": platform.python_version(),
                  "architecture": platform.machine(), "logical_cpus": os.cpu_count(),
                  "baseline_commit": baseline_sha, "local_head_commit": current_sha,
                  "baseline_synth_blob_sha": git_text("rev-parse", f"{args.baseline_ref}:software/engine_sound_lab/synth.py").strip(),
                  "optimized_synth_blob_sha": git_text("hash-object", "software/engine_sound_lab/synth.py").strip(),
                  "local_worktree_dirty": bool(git_text("status", "--porcelain")),
                  "mode": "paced synthetic loop (NOT PortAudio)" if args.paced else "consecutive synthesis-only loop",
                  "frame_count": FRAMES, "sample_rate_hz": RATE, "period_ms": PERIOD_NS / 1e6,
                  "blocks_per_run": args.blocks, "warmup_blocks": args.warmup,
                  "limits": "No actual audio device, end-to-end latency, Pi thermal/CPU, or underrun measurement",
                  "results": []}
        for profile_id in args.profiles:
            for run_index in range(args.runs):
                order = (("baseline", baseline_type, False), ("optimized", EngineSynth, True))
                if run_index % 2:
                    order = tuple(reversed(order))
                for name, engine_type, into in order:
                    reading = run_variant(engine_type, profile_id, args.blocks,
                                          args.warmup, args.paced, into)
                    result["results"].append({"profile": profile_id, "run": run_index + 1,
                                              "variant": name, **reading})
        encoded = json.dumps(result, indent=2) + "\n"
        if args.output is not None:
            with args.output.open("x", encoding="utf-8") as dest:
                dest.write(encoded)
            print(f"Wrote {args.output}")
        else:
            print(encoded)
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Benchmark comparison failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
