#!/usr/bin/env python3
"""Emit exact rational robotics trace vectors for demos and RTL fixtures."""

from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "software"))

from lib.rational_robotics import (  # noqa: E402
    six_step_kinematics_trace,
    six_step_trace_to_dict,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the six-step rational robotics ROTC trace.",
    )
    parser.add_argument(
        "--angle",
        type=int,
        default=1,
        help="Corrected ROTC angle to command for six phases (default: 1).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write JSON to this path instead of stdout.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    trace = six_step_kinematics_trace(angle=args.angle)
    data = six_step_trace_to_dict(trace)
    text = json.dumps(data, indent=args.indent, sort_keys=True) + "\n"

    if args.output:
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
