"""Deterministic one-pixel comparison for the T1d software model."""

from __future__ import annotations

import hashlib

from .device_model import pixel_decision as device_pixel_decision
from .device_model import prepare_scene
from .packet import compile_packet
from .reference import pixel_decision as ideal_pixel_decision
from .scene import HEIGHT, PROFILE, WIDTH, parse_scene_bytes


def inspect_pixel(raw_scene_bytes: bytes, x: int, y: int) -> dict[str, object]:
    if type(x) is not int or type(y) is not int:
        raise ValueError("pixel coordinates must be integers")
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        raise ValueError("pixel coordinate outside the active 640x480 rectangle")

    scene = parse_scene_bytes(raw_scene_bytes)
    packet = compile_packet(scene)
    ideal = ideal_pixel_decision(scene, x, y)
    device = device_pixel_decision(prepare_scene(packet), x, y)
    return {
        "format": "spu_gpu_pixel_inspection_s3_v1",
        "profile": PROFILE,
        "x": x,
        "y": y,
        "input_scene_sha256": hashlib.sha256(raw_scene_bytes).hexdigest(),
        "scene_packet_sha256": hashlib.sha256(packet).hexdigest(),
        "ideal_reference": ideal,
        "device_decision": device,
        "decision_match": {
            key: ideal[key] == device[key]
            for key in ("coverage", "covered_by", "winner", "rgb")
        },
        "evidence": {
            "device_model": True,
            "physical_observation": False,
            "cycle_timing_model": False,
        },
    }
