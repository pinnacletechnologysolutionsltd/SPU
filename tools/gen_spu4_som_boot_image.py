#!/usr/bin/env python3
"""gen_spu4_som_boot_image.py — Generate spu4_som_edge weight boot image for SPI flash.

Flash image layout (consumed by hardware/rtl/core/spu4/spu4_som_flash_loader.v):
  4 nodes x feature_count x 4 bytes, node-major, feature-ascending.
  Each feature is P_hi P_lo Q_hi Q_lo — signed 16-bit big-endian halves,
  RationalSurd convention (P upper, Q lower).

Offset in SPI flash: 0x120000 (FLASH_SPU4_SOM_BASE)

Input is a JSON weights document (see WeightsError below for the schema), the
output of training spu4_som_edge's 4 nodes against
software/lib/rational_som.py. No trainer for that 4-node topology exists yet
(tools/som_trainer.py trains the SPU-13 7-node hex SOM, a different map
format entirely — do not conflate the two) — until one does, --profile
generates a synthetic image so this script and the loader RTL can be
exercised end to end without real training data.
"""

import argparse
import json
import os
import struct

NODE_COUNT = 4
FORMAT = "SPU4_SOM_BOOT_IMAGE_V1"


class WeightsError(ValueError):
    """Raised when a weights document violates the expected schema.

    {
      "format": "SPU4_SOM_BOOT_IMAGE_V1",
      "node_count": 4,
      "feature_count": <int>,
      "nodes": [
        {"id": 0, "weights": [{"p": <signed16>, "q": <signed16>}, ...]},
        ...
      ]
    }
    nodes must cover ids 0..3 exactly once; each node's weights list must be
    exactly feature_count entries long.
    """


def load_weights(path):
    with open(path, encoding="utf-8") as f:
        document = json.load(f)
    if document.get("format") != FORMAT:
        raise WeightsError(f"format must be {FORMAT}")
    if document.get("node_count") != NODE_COUNT:
        raise WeightsError(f"node_count must be {NODE_COUNT}")
    feature_count = document.get("feature_count")
    if not isinstance(feature_count, int) or feature_count <= 0:
        raise WeightsError("feature_count must be a positive integer")
    nodes = document.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != NODE_COUNT:
        raise WeightsError(f"nodes must be a list of {NODE_COUNT} entries")

    by_id = {}
    for node in nodes:
        node_id = node.get("id")
        if node_id not in range(NODE_COUNT):
            raise WeightsError(f"node id out of range 0..{NODE_COUNT - 1}: {node_id!r}")
        if node_id in by_id:
            raise WeightsError(f"duplicate node id: {node_id}")
        weights = node.get("weights")
        if not isinstance(weights, list) or len(weights) != feature_count:
            raise WeightsError(f"node {node_id}: weights must have {feature_count} entries")
        by_id[node_id] = [(w["p"], w["q"]) for w in weights]

    return feature_count, [by_id[i] for i in range(NODE_COUNT)]


def pack_feature(p, q):
    try:
        return struct.pack(">hh", p, q)
    except struct.error as exc:
        raise WeightsError(f"({p}, {q}) is outside signed 16-bit range") from exc


def build_image(feature_count, node_weights):
    image = bytearray()
    for node_id in range(NODE_COUNT):
        weights = node_weights[node_id]
        if len(weights) != feature_count:
            raise WeightsError(f"node {node_id}: expected {feature_count} features, got {len(weights)}")
        for p, q in weights:
            image.extend(pack_feature(p, q))
    return bytes(image)


ORACLE_FIXTURE_WEIGHTS = (
    ((100, 0), (0, 0), (0, 0), (0, 0)),
    ((0, 0), (0, 40), (0, 0), (0, 0)),
    ((-30, 0), (-30, 0), (60, 0), (0, 0)),
    ((0, 0), (0, 0), (0, 0), (50, 50)),
)


def synthetic_profile(profile, feature_count):
    """Weights with no training behind them, for exercising the loader RTL
    and this script before a real trainer exists.

    'zero' matches spu4_som_edge's own reset state (all weights 0) — loading
    it is a no-op, useful as a boot-image negative control.
    'demo' uses the exact formula spu4_som_flash_loader_tb.v's mock flash
    uses (P = 0x1000 + node*256 + feature*16 + 1, Q = same + 0x1000 + 1) —
    keep the two in sync if either changes, they are meant to cross-check.
    'oracle_fixture' reproduces software/lib/spu4_som_edge_oracle.py's NODES
    byte-for-byte — the same fixture already proven in simulation by
    software/tests/test_spu4_som_edge_oracle.py and
    hardware/tests/spu4/spu4_som_edge_full_chain_tb.v, and what
    spu13_tang25k_spu4_som_edge_probe.v's silicon bench expects flashed at
    FLASH_SPU4_SOM_BASE. Fixed at feature_count=4; keep all three in sync if
    any changes.
    """
    if profile == "oracle_fixture":
        if feature_count != 4:
            raise ValueError("oracle_fixture is fixed at feature_count=4")
        return [list(node) for node in ORACLE_FIXTURE_WEIGHTS]

    node_weights = [[] for _ in range(NODE_COUNT)]
    for node_id in range(NODE_COUNT):
        for feature in range(feature_count):
            if profile == "zero":
                p, q = 0, 0
            elif profile == "demo":
                p = _to_signed16(0x1000 + (node_id << 8) + (feature << 4) + 1)
                q = _to_signed16(0x2000 + (node_id << 8) + (feature << 4) + 2)
            else:
                raise ValueError(f"unknown profile: {profile}")
            node_weights[node_id].append((p, q))
    return node_weights


def _to_signed16(value):
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def checksum(image):
    total = 0
    for offset in range(0, len(image), 4):
        p, q = struct.unpack(">hh", image[offset:offset + 4])
        total = (total + (p & 0xFFFF) + (q & 0xFFFF)) & 0xFFFFFFFF
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--weights", help="path to a trained weights JSON document (see WeightsError docstring for schema)")
    parser.add_argument("--profile", choices=("zero", "demo", "oracle_fixture"), default="zero",
                         help="synthetic profile to use when --weights is not given (default: zero)")
    parser.add_argument("--features", type=int, default=4,
                         help="feature count for a synthetic profile (default: 4, the INA226 capture contract's value)")
    parser.add_argument("--output", help="output path; defaults to tools/build/spu4_som_boot_image.bin")
    args = parser.parse_args()

    if args.weights:
        feature_count, node_weights = load_weights(args.weights)
        source = args.weights
    else:
        feature_count = args.features
        node_weights = synthetic_profile(args.profile, feature_count)
        source = f"synthetic profile '{args.profile}'"

    image = build_image(feature_count, node_weights)

    output_dir = os.path.join(os.path.dirname(__file__), "build")
    os.makedirs(output_dir, exist_ok=True)
    output_path = args.output or os.path.join(output_dir, "spu4_som_boot_image.bin")

    with open(output_path, "wb") as f:
        f.write(image)

    print(f"SPU-4 SOM boot image: {output_path}")
    print(f"  Source: {source}")
    print(f"  {NODE_COUNT} nodes x {feature_count} features x 4 bytes = {len(image)} bytes")
    print(f"  Checksum: 0x{checksum(image):08X}")
    print(f"  Flash offset: 0x120000 (FLASH_SPU4_SOM_BASE)")
    print()
    print("Flash command:")
    print(f"  tools/rp2040_flash_pmod.py --port <tty> write {output_path} --offset 0x120000")


if __name__ == "__main__":
    main()
