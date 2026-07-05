#!/usr/bin/env python3
"""Collect FPGA timing/resource evidence into JSON and Markdown.

This script consumes nextpnr JSON reports and logs.  It intentionally records
post-route fmax and utilization as evidence artifacts; it does not infer timing
claims from simulation or synthesis-only output.
"""

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
from pathlib import Path


FMAX_RE = re.compile(
    r"Max frequency for clock\s+'?([^':]+)'?:\s+([0-9.]+)\s+MHz"
    r"(?:\s+\((PASS|FAIL)\s+at\s+([0-9.]+)\s+MHz\))?"
)

CROSS_RE = re.compile(
    r"Max delay\s+(.+?)\s*->\s*(.+?)\s*:\s*([0-9.]+)\s+ns"
)
UTIL_RE = re.compile(
    r"Info:\s+([A-Za-z0-9_]+):\s+([0-9]+)/\s*([0-9]+)\s+([0-9]+)%"
)


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def load_json(path):
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_log(path):
    result = {"fmax": {}, "cross_clock_delays": [], "log_utilization": {}}
    if not path:
        return result
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for match in FMAX_RE.finditer(text):
        clock, achieved, status, constraint = match.groups()
        result["fmax"][clock.strip()] = {
            "achieved_mhz": float(achieved),
            "constraint_mhz": float(constraint) if constraint else None,
            "status": status,
            "period_ns": 1000.0 / float(achieved) if float(achieved) else None,
        }
    for match in CROSS_RE.finditer(text):
        src, dst, delay = match.groups()
        result["cross_clock_delays"].append(
            {"from": src.strip(), "to": dst.strip(), "delay_ns": float(delay)}
        )
    for match in UTIL_RE.finditer(text):
        resource, used, available, pct = match.groups()
        result["log_utilization"][resource] = {
            "used": int(used),
            "available": int(available),
            "pct_reported": int(pct),
        }
    return result


def summarize_report(report):
    if not report:
        return {}

    summary = {}
    fmax = {}
    for clock, data in report.get("fmax", {}).items():
        achieved = data.get("achieved")
        fmax[clock] = {
            "achieved_mhz": achieved,
            "constraint_mhz": data.get("constraint"),
            "period_ns": 1000.0 / achieved if achieved else None,
        }
    summary["fmax"] = fmax

    util = {}
    for resource, data in report.get("utilization", {}).items():
        used = data.get("used")
        available = data.get("available")
        pct = None
        if available:
            pct = 100.0 * used / available
        util[resource] = {"used": used, "available": available, "pct": pct}
    summary["utilization"] = util

    paths = []
    for path in report.get("critical_paths", []):
        total = sum(float(step.get("delay", 0.0)) for step in path.get("path", []))
        paths.append(
            {
                "from": path.get("from"),
                "to": path.get("to"),
                "delay_ns": total,
                "stages": len(path.get("path", [])),
            }
        )
    summary["critical_paths"] = paths
    return summary


def merged_metrics(args):
    report = summarize_report(load_json(args.report))
    log = parse_log(args.log)
    fmax = report.get("fmax") or log.get("fmax") or {}

    metrics = {
        "name": args.name,
        "board": args.board,
        "device": args.device,
        "toolchain": args.toolchain,
        "top": args.top,
        "generated_utc": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat(),
        "git_commit": git_commit(),
        "source_report": args.report,
        "source_log": args.log,
        "fmax": fmax,
        "cross_clock_delays": log.get("cross_clock_delays", []),
        "utilization": report.get("utilization", {}),
        "log_utilization": log.get("log_utilization", {}),
        "critical_paths": report.get("critical_paths", []),
        "claim_level": "post-route" if args.report or args.log else "unknown",
        "notes": args.note,
    }
    return metrics


def fmt_float(value, digits=2):
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def write_markdown(metrics, path):
    resources = [
        "LUT4", "DFF", "ALU", "BSRAM",
        "MULT12X12", "MULTALU27X18", "MULTADDALU12X12",
        "LUT", "FDRE", "FDSE", "DSP48E1", "RAMB18E1", "RAMB36E1",
        "IOB", "BUFG",
    ]

    lines = [
        f"# FPGA Metrics: {metrics['name']}",
        "",
        f"- Board: {metrics.get('board') or ''}",
        f"- Device: {metrics.get('device') or ''}",
        f"- Toolchain: {metrics.get('toolchain') or ''}",
        f"- Top: {metrics.get('top') or ''}",
        f"- Claim level: {metrics.get('claim_level')}",
        f"- Generated UTC: {metrics.get('generated_utc')}",
        f"- Git commit: {metrics.get('git_commit') or ''}",
        f"- Report: `{metrics.get('source_report') or ''}`",
        f"- Log: `{metrics.get('source_log') or ''}`",
        "",
        "## Fmax",
        "",
        "| Clock | Achieved MHz | Period ns | Constraint MHz |",
        "|---|---:|---:|---:|",
    ]
    for clock, data in sorted(metrics.get("fmax", {}).items()):
        lines.append(
            f"| {clock} | {fmt_float(data.get('achieved_mhz'))} | "
            f"{fmt_float(data.get('period_ns'))} | "
            f"{fmt_float(data.get('constraint_mhz'))} |"
        )

    if metrics.get("cross_clock_delays"):
        lines += ["", "## Cross-Clock Delays", "", "| From | To | Delay ns |", "|---|---|---:|"]
        for item in metrics["cross_clock_delays"]:
            lines.append(f"| {item['from']} | {item['to']} | {fmt_float(item['delay_ns'])} |")

    lines += ["", "## Utilization", "", "| Resource | Used | Available | Percent |", "|---|---:|---:|---:|"]
    util = metrics.get("utilization", {})
    seen = set()
    for resource in resources:
        if resource not in util:
            continue
        seen.add(resource)
        data = util[resource]
        lines.append(
            f"| {resource} | {data.get('used')} | {data.get('available')} | "
            f"{fmt_float(data.get('pct'))} |"
        )
    for resource in sorted(set(util) - seen):
        data = util[resource]
        lines.append(
            f"| {resource} | {data.get('used')} | {data.get('available')} | "
            f"{fmt_float(data.get('pct'))} |"
        )

    log_util = metrics.get("log_utilization", {})
    if log_util:
        lines += [
            "",
            "## Console Utilization",
            "",
            "| Resource | Used | Available | Reported Percent |",
            "|---|---:|---:|---:|",
        ]
        for resource in resources:
            if resource not in log_util:
                continue
            data = log_util[resource]
            lines.append(
                f"| {resource} | {data.get('used')} | {data.get('available')} | "
                f"{data.get('pct_reported')} |"
            )
        for resource in sorted(set(log_util) - set(resources)):
            data = log_util[resource]
            lines.append(
                f"| {resource} | {data.get('used')} | {data.get('available')} | "
                f"{data.get('pct_reported')} |"
            )

    lines += ["", "## Critical Paths", "", "| From | To | Delay ns | Stages |", "|---|---|---:|---:|"]
    for path_item in metrics.get("critical_paths", [])[:8]:
        lines.append(
            f"| {path_item.get('from') or ''} | {path_item.get('to') or ''} | "
            f"{fmt_float(path_item.get('delay_ns'))} | {path_item.get('stages')} |"
        )

    if metrics.get("notes"):
        lines += ["", "## Notes", ""]
        lines.extend(f"- {note}" for note in metrics["notes"])

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--board", default="")
    parser.add_argument("--device", default="")
    parser.add_argument("--toolchain", default="")
    parser.add_argument("--top", default="")
    parser.add_argument("--report")
    parser.add_argument("--log")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--note", action="append", default=[])
    args = parser.parse_args()

    metrics = merged_metrics(args)
    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.out_md) or ".", exist_ok=True)
    Path(args.out_json).write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(metrics, args.out_md)


if __name__ == "__main__":
    main()
