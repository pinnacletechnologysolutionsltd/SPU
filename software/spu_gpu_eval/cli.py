"""Command-line entry point for the T1d software preview."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .preview import PreviewError, write_preview
from .device_preview import write_device_preview
from .device_inspect import inspect_pixel


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spu-gpu-eval")
    commands = parser.add_subparsers(dest="command", required=True)
    preview = commands.add_parser("preview", help="compile and preview a T1d scene")
    preview.add_argument("scene", help="path to spu_gpu_scene_v1 JSON")
    preview.add_argument("--out", required=True, help="new child of build/gpu_evaluation")
    device = commands.add_parser("device-preview", help="model settled-frame T1d device behavior")
    device.add_argument("scene", help="path to spu_gpu_scene_v1 JSON")
    device.add_argument("--out", required=True, help="new child of build/gpu_evaluation")
    inspect = commands.add_parser("inspect", help="compare ideal and device-model decisions at one pixel")
    inspect.add_argument("scene", help="path to spu_gpu_scene_v1 JSON")
    inspect.add_argument("--x", required=True, type=int, help="active pixel x coordinate")
    inspect.add_argument("--y", required=True, type=int, help="active pixel y coordinate")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            report = inspect_pixel(Path(args.scene).read_bytes(), args.x, args.y)
            sys.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
            return 0
        target = (write_preview(args.scene, args.out) if args.command == "preview"
                  else write_device_preview(args.scene, args.out))
    except (PreviewError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"preview artifacts written to {target.relative_to(target.parents[1])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
