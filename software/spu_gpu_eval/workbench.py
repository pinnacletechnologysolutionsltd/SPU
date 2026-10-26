"""CLI orchestration for frozen scenes and existing T1d software paths."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

from . import device_packet
from .device_inspect import inspect_pixel
from .device_preview import write_device_preview
from .preview import PreviewError, write_preview
from .workbench_catalog import CatalogError, ROOT, find_scene, load_catalog


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _inspect(scene_id: str, x: int, y: int) -> dict[str, object]:
    entry = find_scene(scene_id)
    raw = Path(entry["absolute_path"]).read_bytes()
    report = inspect_pixel(raw, x, y)
    ideal = report["ideal_reference"]["depths"]
    device = report["device_decision"]["depths"]
    depth_rows = []
    for exact, bounded in zip(ideal, device):
        rational = Fraction(exact["numerator"], exact["denominator"])
        depth_rows.append({
            "triangle": exact["triangle"], "ideal": str(rational),
            "device_model": bounded["value"], "equal": rational == bounded["value"],
        })
    return {
        "format": "spu_gpu_workbench_pixel_v1", "scene_id": scene_id,
        "scene_sha256": entry["sha256"], "profile": report["profile"],
        "x": x, "y": y,
        "ideal_reference": report["ideal_reference"],
        "device_model": report["device_decision"],
        "comparison": {
            "coverage_equal": report["decision_match"]["coverage"],
            "covered_triangles_equal": report["decision_match"]["covered_by"],
            "winner_equal": report["decision_match"]["winner"],
            "rgb_equal": report["decision_match"]["rgb"],
            "depths_equal": all(row["equal"] for row in depth_rows),
            "depths": depth_rows,
        },
        "evidence": report["evidence"],
    }


def _inspect_packet(path: str) -> dict[str, object]:
    packet = Path(path).read_bytes()
    decoded = device_packet.decode_packet(packet)
    return {
        "format": "spu_gpu_workbench_packet_v1",
        "profile": "t1d-two-triangle-v1", "packet_bytes": len(packet),
        "sha256": hashlib.sha256(packet).hexdigest(),
        "start_byte": f"0x{packet[0]:02x}",
        "triangles": [
            {"edges": triangle.edges, "rgb444": triangle.rgb, "vertex_depths": triangle.z}
            for triangle in decoded.triangles
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spu-gpu-workbench")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list hash-checked frozen T1d scenes")
    render = commands.add_parser("render", help="render one frozen scene")
    render.add_argument("scene_id")
    render.add_argument("--mode", choices=("ideal", "device"), required=True)
    render.add_argument("--out", required=True)
    inspect = commands.add_parser("inspect", help="compare exact and bounded pixel decisions")
    inspect.add_argument("scene_id")
    inspect.add_argument("--x", type=int, required=True)
    inspect.add_argument("--y", type=int, required=True)
    packet = commands.add_parser("inspect-packet", help="decode one strict 64-byte T1d packet")
    packet.add_argument("path")
    view = commands.add_parser("view", help="serve the local T1d frame and pixel viewer")
    view.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "view":
            if not 1 <= args.port <= 65535:
                raise ValueError("port must be between 1 and 65535")
            from .workbench_viewer import serve
            serve(args.port)
            return 0
        if args.command == "list":
            for entry in load_catalog():
                print(f"{entry['id']}\t{entry['group']}\t{entry['sha256']}\t{entry['path']}")
            return 0
        if args.command == "inspect":
            print(_json(_inspect(args.scene_id, args.x, args.y)))
            return 0
        if args.command == "inspect-packet":
            print(_json(_inspect_packet(args.path)))
            return 0
        entry = find_scene(args.scene_id)
        target = write_preview if args.mode == "ideal" else write_device_preview
        output = target(entry["absolute_path"], args.out)
        print(f"{args.mode} render written to {output.relative_to(ROOT)}")
        return 0
    except (CatalogError, PreviewError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
