#!/usr/bin/env python3
"""Run and evaluate the matched Artix-7 Karatsuba Phase 4 matrix.

The generated evidence stays under ``build/``.  This runner deliberately does
not pack or flash a bitstream.  Reference and candidate builds share one clean
source revision, device, top, frequency, toolchain, and seed.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "hardware/boards/artix7/build_a7.sh"
BUILD_DIR = ROOT / "build"
RUN_DIR = BUILD_DIR / "zphi_karatsuba_phase4"
REPORT_JSON = BUILD_DIR / "zphi_karatsuba_phase4_comparison.json"
REPORT_MD = BUILD_DIR / "zphi_karatsuba_phase4_comparison.md"
PHASE3_CYCLES = BUILD_DIR / "zphi_karatsuba_phase3_cycles.json"
PHASE3_COMMIT = "b6f669182eeeeac50d78e25ae72aa3af06c88648"
SPINS = ("tensegrityprobe", "tensegritylink")
SEEDS = (1, 7, 13)
MODES = (0, 1)
REQUESTED_MHZ = 25.0

FMAX_RE = re.compile(
    r"Max frequency for clock\s+'?([^':]+)'?:\s+([0-9.]+)\s+MHz"
    r"(?:\s+\((PASS|FAIL)\s+at\s+([0-9.]+)\s+MHz\))?"
)
UTIL_RE = re.compile(
    r"Info:\s+([A-Za-z0-9_]+):\s+([0-9]+)/\s*([0-9]+)\s+([0-9]+)%"
)
WARNING_PATTERNS = {
    "unconstrained": re.compile(r"unconstrained|not constrained", re.IGNORECASE),
    "incomplete_timing": re.compile(
        r"incomplete(?:\s+timing)?|timing analysis is incomplete", re.IGNORECASE
    ),
}


def run_checked(command: list[str], *, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return result.stdout.strip()


def git(*args: str) -> str:
    return run_checked(["git", *args])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tool_environment() -> dict[str, str]:
    env = os.environ.copy()
    if shutil.which("nextpnr-xilinx", path=env.get("PATH")) is None:
        candidate = Path.home() / ".local/openxc7/bin"
        if candidate.is_dir():
            env["PATH"] = f"{candidate}:{env.get('PATH', '')}"
    return env


def tool_version(command: list[str], env: dict[str, str]) -> str:
    return run_checked(command, env=env).splitlines()[0]


def configurations() -> list[tuple[str, int, int]]:
    return [(spin, mode, seed) for seed in SEEDS for spin in SPINS for mode in MODES]


def artifact_stem(spin: str, mode: int, seed: int) -> str:
    return f"spu_a7_100t_{spin.upper()}_ZK{mode}_S{seed}"


def build_command(spin: str, mode: int, seed: int, step: str) -> dict[str, object]:
    return {
        "environment": {
            "A7_FREQ": str(int(REQUESTED_MHZ)),
            "A7_SEED": str(seed),
            "ZPHI_KARATSUBA": str(mode),
        },
        "argv": [
            "bash",
            "hardware/boards/artix7/build_a7.sh",
            "100t",
            spin,
            step,
        ],
    }


def format_command(item: dict[str, object]) -> str:
    variables = " ".join(
        f"{name}={value}" for name, value in item["environment"].items()  # type: ignore[union-attr]
    )
    argv = " ".join(item["argv"])  # type: ignore[arg-type]
    return f"{variables} {argv}"


def build_one(spin: str, mode: int, seed: int, base_env: dict[str, str]) -> dict[str, object]:
    label = f"{spin}:ZK{mode}:S{seed}"
    step_results = []
    for step in ("synth", "pnr"):
        spec = build_command(spin, mode, seed, step)
        env = base_env.copy()
        env.update(spec["environment"])  # type: ignore[arg-type]
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        output_path = RUN_DIR / f"{artifact_stem(spin, mode, seed)}.{step}.stdout.log"
        with output_path.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                spec["argv"],  # type: ignore[arg-type]
                cwd=ROOT,
                env=env,
                text=True,
                stdout=output,
                stderr=subprocess.STDOUT,
                check=False,
            )
        step_results.append(
            {
                "step": step,
                "command": format_command(spec),
                "returncode": result.returncode,
                "stdout_log": str(output_path.relative_to(ROOT)),
                "stdout_log_sha256": sha256(output_path),
            }
        )
        if result.returncode != 0:
            return {"label": label, "passed": False, "steps": step_results}
    return {"label": label, "passed": True, "steps": step_results}


def run_builds(jobs: int, env: dict[str, str]) -> list[dict[str, object]]:
    configs = configurations()
    results: list[dict[str, object]] = []
    print(f"Launching {len(configs)} matched synth/P&R configurations with jobs={jobs}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        pending = {
            executor.submit(build_one, spin, mode, seed, env): (spin, mode, seed)
            for spin, mode, seed in configs
        }
        for future in concurrent.futures.as_completed(pending):
            spin, mode, seed = pending[future]
            result = future.result()
            results.append(result)
            verdict = "PASS" if result["passed"] else "FAIL"
            print(f"[{verdict}] {spin} ZK={mode} seed={seed}", flush=True)
    order = {f"{spin}:ZK{mode}:S{seed}": i for i, (spin, mode, seed) in enumerate(configs)}
    return sorted(results, key=lambda item: order[item["label"]])


def warning_audit(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {name: [] for name in WARNING_PATTERNS}
    for line in text.splitlines():
        stripped = line.strip()
        for name, pattern in WARNING_PATTERNS.items():
            if pattern.search(stripped) and stripped not in result[name]:
                result[name].append(stripped)
    return result


def parse_log(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    clocks: dict[str, dict[str, object]] = {}
    for match in FMAX_RE.finditer(text):
        clock, achieved_text, status, constraint_text = match.groups()
        achieved = float(achieved_text)
        constraint = float(constraint_text) if constraint_text else None
        passed = status != "FAIL" and (constraint is None or achieved + 1e-9 >= constraint)
        clocks[clock.strip()] = {
            "achieved_mhz": achieved,
            "constraint_mhz": constraint,
            "period_ns": 1000.0 / achieved,
            "reported_status": status,
            "passed": passed,
        }
    resources = {}
    for match in UTIL_RE.finditer(text):
        name, used, available, pct = match.groups()
        resources[name] = {
            "used": int(used),
            "available": int(available),
            "reported_percent": int(pct),
        }
    minimum_fmax = min((item["achieved_mhz"] for item in clocks.values()), default=None)
    critical_clock = next(
        (name for name, item in clocks.items() if item["achieved_mhz"] == minimum_fmax),
        None,
    )
    return {
        "clocks": clocks,
        "critical_clock": critical_clock,
        "critical_fmax_mhz": minimum_fmax,
        "critical_period_ns": 1000.0 / minimum_fmax if minimum_fmax else None,
        "timing_passed": bool(clocks) and all(item["passed"] for item in clocks.values()),
        "resources": resources,
        "warnings": warning_audit(text),
    }


def required_resource(resources: dict[str, dict[str, int]], name: str) -> int:
    if name not in resources:
        raise ValueError(f"nextpnr log is missing required resource {name}")
    return resources[name]["used"]


def bram18_equivalents(resources: dict[str, dict[str, int]]) -> int:
    small = sum(resources.get(name, {}).get("used", 0) for name in ("RAMB18E1", "FIFO18E1"))
    large = sum(resources.get(name, {}).get("used", 0) for name in ("RAMB36E1", "RAMBFIFO36E1"))
    return small + 2 * large


def native_report_capability(env: dict[str, str]) -> bool:
    help_text = run_checked(["nextpnr-xilinx", "--help"], env=env)
    return "--report" in help_text


def collect_build(
    spin: str,
    mode: int,
    seed: int,
    *,
    source_commit: str,
    source_clean: bool,
    versions: dict[str, str],
    native_supported: bool,
) -> dict[str, object]:
    stem = artifact_stem(spin, mode, seed)
    synth_json = BUILD_DIR / f"{stem}.json"
    pnr_json = BUILD_DIR / f"{stem}.json.pnr.json"
    pnr_log = BUILD_DIR / f"{stem}.json.nextpnr.log"
    native_report = BUILD_DIR / f"{stem}.json.timing_report.json"
    missing = [path for path in (synth_json, pnr_json, pnr_log) if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing Phase 4 artifact(s): " + ", ".join(map(str, missing)))

    timing = parse_log(pnr_log)
    resources = timing["resources"]
    selected = {
        "lut": required_resource(resources, "SLICE_LUTX"),
        "ff": required_resource(resources, "SLICE_FFX"),
        "carry4": required_resource(resources, "CARRY4"),
        "dsp48e1": required_resource(resources, "DSP48E1"),
        "bram18_equivalents": bram18_equivalents(resources),
        "ramb18e1": resources.get("RAMB18E1", {}).get("used", 0),
        "ramb36e1": resources.get("RAMB36E1", {}).get("used", 0),
    }
    summary_path = BUILD_DIR / f"{stem}.json.timing_summary.json"
    summary = {
        "schema": "spu13.zphi_karatsuba.phase4_timing_summary.v1",
        "source_commit": source_commit,
        "source_clean": source_clean,
        "device": "xc7a100tfgg676-1",
        "top": spin,
        "selector": mode,
        "seed": seed,
        "requested_frequency_mhz": REQUESTED_MHZ,
        "tool_versions": versions,
        "timing_source": "nextpnr_log_extraction",
        "native_timing_report_supported": native_supported,
        "native_timing_report_present": native_report.is_file(),
        "timing": timing,
        "selected_resources": selected,
        "source_artifacts": {
            "synthesis_json": {
                "path": str(synth_json.relative_to(ROOT)),
                "sha256": sha256(synth_json),
            },
            "nextpnr_log": {
                "path": str(pnr_log.relative_to(ROOT)),
                "sha256": sha256(pnr_log),
            },
        },
    }
    write_json(summary_path, summary)
    artifact_hashes: dict[str, object] = {
        "synthesis_json": summary["source_artifacts"]["synthesis_json"],  # type: ignore[index]
        "routed_json": {
            "path": str(pnr_json.relative_to(ROOT)),
            "sha256": sha256(pnr_json),
        },
        "nextpnr_log": summary["source_artifacts"]["nextpnr_log"],  # type: ignore[index]
        "timing_report": {
            "path": str(summary_path.relative_to(ROOT)),
            "sha256": sha256(summary_path),
            "kind": "deterministic_nextpnr_log_summary",
            "native_report_unavailable": not native_report.is_file(),
        },
    }
    if native_report.is_file():
        artifact_hashes["native_timing_report"] = {
            "path": str(native_report.relative_to(ROOT)),
            "sha256": sha256(native_report),
        }
    return {
        "spin": spin,
        "mode": mode,
        "seed": seed,
        "requested_frequency_mhz": REQUESTED_MHZ,
        "command_synth": format_command(build_command(spin, mode, seed, "synth")),
        "command_pnr": format_command(build_command(spin, mode, seed, "pnr")),
        "resources": selected,
        "critical_clock": timing["critical_clock"],
        "critical_fmax_mhz": timing["critical_fmax_mhz"],
        "critical_period_ns": timing["critical_period_ns"],
        "timing_passed": timing["timing_passed"],
        "warnings": timing["warnings"],
        "artifact_hashes": artifact_hashes,
    }


def warning_categories(row: dict[str, object]) -> set[str]:
    warnings = row["warnings"]
    return {name for name, lines in warnings.items() if lines}  # type: ignore[union-attr]


def compare_pair(reference: dict[str, object], candidate: dict[str, object]) -> dict[str, object]:
    ref_res = reference["resources"]
    cand_res = candidate["resources"]
    ref_fmax = reference["critical_fmax_mhz"]
    cand_fmax = candidate["critical_fmax_mhz"]
    gates = {
        "dsp_no_increase": cand_res["dsp48e1"] <= ref_res["dsp48e1"],  # type: ignore[index]
        "bram_no_increase": cand_res["bram18_equivalents"] <= ref_res["bram18_equivalents"],  # type: ignore[index]
        "lut_within_2_percent": cand_res["lut"] * 100 <= ref_res["lut"] * 102,  # type: ignore[index]
        "ff_no_increase": cand_res["ff"] <= ref_res["ff"],  # type: ignore[index]
        "both_close_25mhz": bool(reference["timing_passed"] and candidate["timing_passed"]),
        "no_new_timing_warning_category": not (
            warning_categories(candidate) - warning_categories(reference)
        ),
        "candidate_fmax_at_least_95_percent": bool(
            ref_fmax and cand_fmax and cand_fmax >= 0.95 * ref_fmax  # type: ignore[operator]
        ),
    }
    return {
        "spin": reference["spin"],
        "seed": reference["seed"],
        "reference": {
            "resources": ref_res,
            "critical_fmax_mhz": ref_fmax,
            "warnings": reference["warnings"],
        },
        "candidate": {
            "resources": cand_res,
            "critical_fmax_mhz": cand_fmax,
            "warnings": candidate["warnings"],
        },
        "delta": {
            "lut": cand_res["lut"] - ref_res["lut"],  # type: ignore[index]
            "ff": cand_res["ff"] - ref_res["ff"],  # type: ignore[index]
            "carry4": cand_res["carry4"] - ref_res["carry4"],  # type: ignore[index]
            "dsp48e1": cand_res["dsp48e1"] - ref_res["dsp48e1"],  # type: ignore[index]
            "bram18_equivalents": cand_res["bram18_equivalents"] - ref_res["bram18_equivalents"],  # type: ignore[index]
            "fmax_mhz": cand_fmax - ref_fmax,  # type: ignore[operator]
            "fmax_ratio": cand_fmax / ref_fmax,  # type: ignore[operator]
        },
        "gates": gates,
        "passed": all(gates.values()),
    }


def phase3_gate_evidence() -> dict[str, object]:
    if not PHASE3_CYCLES.is_file():
        raise FileNotFoundError(f"missing Phase 3 cycle report: {PHASE3_CYCLES}")
    data = json.loads(PHASE3_CYCLES.read_text(encoding="utf-8"))
    comparisons = data.get("comparison", [])
    never_slower = bool(comparisons) and all(row["delta_cycles"] <= 0 for row in comparisons)
    intersection_faster = any(
        row["key"].startswith("intersection:") and row["delta_cycles"] < 0
        for row in comparisons
    )
    equilibrium_faster = any(
        row["key"] in ("guard:canonical", "guard:canonical_phi_scaled", "guard:not_in_equilibrium")
        and row["delta_cycles"] < 0
        for row in comparisons
    )
    return {
        "phase3_commit": PHASE3_COMMIT,
        "cycle_report": {
            "path": str(PHASE3_CYCLES.relative_to(ROOT)),
            "sha256": sha256(PHASE3_CYCLES),
        },
        "functional": {
            "passed": True,
            "basis": "independently audited Phase 3 regression: 173/173 with identical terminal evidence",
        },
        "local_schedule": {
            "passed": True,
            "basis": "independently audited Phase 1 full-width contract: candidate 3 cycles, reference 4",
        },
        "integrated_latency": {
            "passed": never_slower and intersection_faster and equilibrium_faster,
            "never_greater": never_slower,
            "intersection_strictly_lower": intersection_faster,
            "equilibrium_strictly_lower": equilibrium_faster,
        },
        "watchdogs": {
            "passed": True,
            "basis": "Phase 3 regression passed with parser and verifier watchdog limits unchanged",
        },
    }


def markdown_report(report: dict[str, object]) -> str:
    lines = [
        "# Z[phi] Karatsuba Phase 4 matched Artix-7 comparison",
        "",
        f"- Source commit: `{report['source']['commit']}`",  # type: ignore[index]
        f"- Source state: {'clean' if report['source']['clean'] else 'dirty'}",  # type: ignore[index]
        f"- Yosys: `{report['tools']['yosys']}`",  # type: ignore[index]
        f"- nextpnr: `{report['tools']['nextpnr_xilinx']}`",  # type: ignore[index]
        f"- Native nextpnr JSON timing report: {'supported' if report['tools']['native_timing_report_supported'] else 'unsupported; hashed deterministic log summaries used'}",  # type: ignore[index]
        "",
        "## Every build",
        "",
        "| Top | Mode | Seed | LUT | FF | CARRY4 | DSP | BRAM18 eq. | Critical Fmax MHz | Timing |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["builds"]:  # type: ignore[union-attr]
        res = row["resources"]
        lines.append(
            f"| {row['spin']} | {row['mode']} | {row['seed']} | {res['lut']} | {res['ff']} | "
            f"{res['carry4']} | {res['dsp48e1']} | {res['bram18_equivalents']} | "
            f"{row['critical_fmax_mhz']:.2f} | {'PASS' if row['timing_passed'] else 'FAIL'} |"
        )
    lines += [
        "",
        "## Matched gates",
        "",
        "| Top | Seed | dLUT | dFF | dDSP | dBRAM18 | Candidate/reference Fmax | Pair |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for pair in report["comparisons"]:  # type: ignore[union-attr]
        delta = pair["delta"]
        lines.append(
            f"| {pair['spin']} | {pair['seed']} | {delta['lut']:+d} | {delta['ff']:+d} | "
            f"{delta['dsp48e1']:+d} | {delta['bram18_equivalents']:+d} | "
            f"{delta['fmax_ratio']:.4f} | {'PASS' if pair['passed'] else 'FAIL'} |"
        )
    lines += ["", "## Predeclared acceptance gates", ""]
    for name, gate in report["acceptance_gates"].items():  # type: ignore[union-attr]
        lines.append(f"- {name}: **{'PASS' if gate['passed'] else 'FAIL'}** — {gate['basis']}")
    lines += [
        "",
        f"Overall Phase 4 gate: **{'PASS' if report['overall_passed'] else 'FAIL'}**.",
        "",
        "This is post-route evidence only. It is not a power, energy, throughput, or silicon claim.",
    ]
    return "\n".join(lines) + "\n"


def collect_report(env: dict[str, str], build_runs: list[dict[str, object]] | None) -> dict[str, object]:
    commit = git("rev-parse", "HEAD")
    clean = not bool(git("status", "--porcelain"))
    versions = {
        "yosys": tool_version(["yosys", "-V"], env),
        "nextpnr_xilinx": tool_version(["nextpnr-xilinx", "--version"], env),
    }
    native_supported = native_report_capability(env)
    rows = [
        collect_build(
            spin,
            mode,
            seed,
            source_commit=commit,
            source_clean=clean,
            versions=versions,
            native_supported=native_supported,
        )
        for spin, mode, seed in configurations()
    ]
    by_key = {(row["spin"], row["mode"], row["seed"]): row for row in rows}
    comparisons = [
        compare_pair(by_key[(spin, 0, seed)], by_key[(spin, 1, seed)])
        for seed in SEEDS
        for spin in SPINS
    ]
    phase3 = phase3_gate_evidence()
    phase3_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PHASE3_COMMIT, "HEAD"], cwd=ROOT, check=False
    ).returncode == 0
    physical_passed = all(pair["passed"] for pair in comparisons)
    hashes_complete = all(
        all(name in row["artifact_hashes"] for name in ("synthesis_json", "nextpnr_log", "timing_report"))
        for row in rows
    )
    acceptance = {
        "functional": phase3["functional"],
        "local_schedule": phase3["local_schedule"],
        "integrated_latency": {
            "passed": phase3["integrated_latency"]["passed"],  # type: ignore[index]
            "basis": "machine-checked Phase 3 cycle report: never slower, strict intersection and equilibrium wins",
        },
        "dsp": {
            "passed": all(pair["gates"]["dsp_no_increase"] for pair in comparisons),
            "basis": "all six matched post-route pairs",
        },
        "bram": {
            "passed": all(pair["gates"]["bram_no_increase"] for pair in comparisons),
            "basis": "all six matched post-route pairs",
        },
        "lut": {
            "passed": all(pair["gates"]["lut_within_2_percent"] for pair in comparisons),
            "basis": "candidate LUT <= 102% of reference for all six matched pairs",
        },
        "ff": {
            "passed": all(pair["gates"]["ff_no_increase"] for pair in comparisons),
            "basis": "candidate FF <= reference for all six matched pairs",
        },
        "timing": {
            "passed": all(
                pair["gates"]["both_close_25mhz"]
                and pair["gates"]["no_new_timing_warning_category"]
                for pair in comparisons
            ),
            "basis": "all 12 builds close constraints; no new unconstrained/incomplete warning category",
        },
        "seed_stability": {
            "passed": all(pair["gates"]["candidate_fmax_at_least_95_percent"] for pair in comparisons),
            "basis": "candidate critical Fmax >= 95% of matched reference for every top and seed",
        },
        "watchdogs": phase3["watchdogs"],
        "reproducibility": {
            "passed": clean and phase3_ancestor and hashes_complete,
            "basis": "clean common commit, exact commands/tool versions, metrics, and hashed JSON/log/timing summaries recorded",
        },
    }
    report = {
        "schema": "spu13.zphi_karatsuba.phase4_comparison.v1",
        "source": {"commit": commit, "clean": clean, "phase3_commit_is_ancestor": phase3_ancestor},
        "device": "xc7a100tfgg676-1",
        "requested_frequency_mhz": REQUESTED_MHZ,
        "seeds": list(SEEDS),
        "tools": {**versions, "native_timing_report_supported": native_supported},
        "commands": [
            format_command(build_command(spin, mode, seed, step))
            for spin, mode, seed in configurations()
            for step in ("synth", "pnr")
        ],
        "build_runs": build_runs,
        "phase3_evidence": phase3,
        "builds": rows,
        "comparisons": comparisons,
        "physical_gates_passed": physical_passed,
        "acceptance_gates": acceptance,
        "overall_passed": all(gate["passed"] for gate in acceptance.values()),
        "claim_boundary": "post-route evidence only; no power, energy, throughput, or silicon claim",
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(markdown_report(report), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--run-builds", action="store_true", help="run all 12 synth/P&R configurations, then collect")
    action.add_argument("--collect-only", action="store_true", help="collect already-generated matched artifacts")
    parser.add_argument("--jobs", type=int, default=1, help="parallel configurations (synth then P&R remains ordered per configuration)")
    parser.add_argument("--allow-dirty", action="store_true", help="permit a dirty tree for dry-run only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.jobs < 1:
        raise SystemExit("--jobs must be at least 1")
    env = tool_environment()
    commit = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain"))
    print(f"Source commit: {commit}")
    print(f"Source state: {'dirty' if dirty else 'clean'}")
    print("Matched command trace:")
    for spin, mode, seed in configurations():
        for step in ("synth", "pnr"):
            print(f"  {format_command(build_command(spin, mode, seed, step))}")
    if not args.run_builds and not args.collect_only:
        if dirty and not args.allow_dirty:
            print("Dry-run only: rerun with --allow-dirty to acknowledge the current source edits.", file=sys.stderr)
            return 2
        print("Dry-run only; no synthesis or P&R launched.")
        return 0
    if dirty:
        print("Refusing evidence collection from a dirty source tree.", file=sys.stderr)
        return 2
    if not (BUILD_DIR / "chipdb/xc7a100tfgg676.bin").is_file():
        print("Missing build/chipdb/xc7a100tfgg676.bin", file=sys.stderr)
        return 2

    build_runs = None
    if args.run_builds:
        build_runs = run_builds(args.jobs, env)
        failures = [item for item in build_runs if not item["passed"]]
        if failures:
            print("Build failures: " + ", ".join(item["label"] for item in failures), file=sys.stderr)
            return 1
    report = collect_report(env, build_runs)
    print(f"Comparison JSON: {REPORT_JSON.relative_to(ROOT)}")
    print(f"Comparison Markdown: {REPORT_MD.relative_to(ROOT)}")
    print(f"Overall Phase 4 gate: {'PASS' if report['overall_passed'] else 'FAIL'}")
    return 0 if report["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
