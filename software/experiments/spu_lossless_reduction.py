#!/usr/bin/env python3
"""R0 experimental encoding; proves no GPU device equivalence.

Blocks contain at most 32 ZigZag integers, packed low bits first. Factored
surds are (g, a, b, scale), meaning g*(a+b*sqrt(3))/scale. Triangle edges
are opposite vertices 0, 1, 2 and pair with depths in that same order.
"""
import argparse
import json
import math
import os
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

MIN_I64, MAX_I64, MAX_COUNT = -(1 << 63), (1 << 63) - 1, 1_000_000
ROOT = Path(__file__).resolve().parents[2]

def integers(values):
    values = tuple(values)
    if len(values) > MAX_COUNT or any(type(x) is not int for x in values):
        raise ValueError("expected at most 1,000,000 non-boolean integers")
    return values

def pack(values):
    values = integers(values)
    if any(not MIN_I64 <= x <= MAX_I64 for x in values):
        raise ValueError("signed 64-bit range exceeded")
    output = bytearray(len(values).to_bytes(4, "little"))
    for start in range(0, len(values), 32):
        block = [2*x if x >= 0 else -2*x-1 for x in values[start:start+32]]
        width = max(x.bit_length() for x in block)
        payload = sum(x << (i*width) for i, x in enumerate(block))
        output.append(width)
        output.extend(payload.to_bytes((len(block)*width+7)//8, "little"))
    return bytes(output)

def unpack(data):
    if not isinstance(data, bytes) or len(data) < 4:
        raise ValueError("expected complete bytes header")
    count = int.from_bytes(data[:4], "little")
    if count > MAX_COUNT:
        raise ValueError("excessive element count")
    cursor, blocks = 4, []
    for start in range(0, count, 32):
        if cursor == len(data):
            raise ValueError("missing block width")
        width, size = data[cursor], min(32, count-start)
        bits, cursor = size*width, cursor+1
        end = cursor + (bits+7)//8
        if width > 64 or end > len(data):
            raise ValueError("invalid width or truncated block")
        payload = int.from_bytes(data[cursor:end], "little")
        if payload >> bits:
            raise ValueError("nonzero padding")
        blocks.append((size, width, payload))
        cursor = end
    if cursor != len(data):
        raise ValueError("trailing data")
    # All stream lengths and padding are checked before output allocation.
    values = []
    for size, width, payload in blocks:
        mask = (1 << width)-1
        for i in range(size):
            u = (payload >> (i*width)) & mask
            values.append(u//2 if u % 2 == 0 else -(u//2)-1)
    if pack(values) != data:
        raise ValueError("noncanonical width")
    return values

def factor(values):
    values = integers(values)
    g = math.gcd(*(abs(x) for x in values)) or 1
    return g, tuple(x//g for x in values)

def factor_pack(values):
    g, reduced = factor(values)
    if g >= 1 << 64:
        raise ValueError("factor exceeds unsigned 64-bit storage")
    return g.to_bytes(8, "little") + pack(reduced)

def reduce_surd(a, b, scale):
    integers((a, b, scale))
    if scale <= 0:
        raise ValueError("scale must be positive")
    g, (a, b) = factor((a, b))
    return g, a, b, scale

def multiply_surds(left, right):
    g, a, b, scale = left
    h, c, d, other_scale = right
    integers(left + right)
    if min(g, h, scale, other_scale) <= 0:
        raise ValueError("factors and scales must be positive")
    return (Fraction(g*h*(a*c+3*b*d), scale*other_scale),
            Fraction(g*h*(a*d+b*c), scale*other_scale))

def reduce_rational(p, q):
    integers((p, q))
    if q == 0:
        raise ValueError("zero denominator")
    if q < 0:
        p, q = -p, -q
    g = math.gcd(p, q)
    return p//g, q//g

def triangle_edges(vertices):
    if len(vertices) != 3 or any(len(v) != 3 for v in vertices):
        raise ValueError("expected three (x,y,z) vertices")
    for vertex in vertices:
        integers(vertex)
    edges = []
    for i in range(3):
        px, py, _ = vertices[(i+1) % 3]
        qx, qy, _ = vertices[(i+2) % 3]
        edges.append((py-qy, qx-px, px*qy-py*qx))
    x, y, _ = vertices[0]
    area = edges[0][0]*x + edges[0][1]*y + edges[0][2]
    if not area:
        raise ValueError("degenerate triangle")
    return tuple(tuple(-c for c in edge) if area < 0 else edge for edge in edges)

def edge_depth(edges, depths, x, y):
    weights = [a*x+b*y+c for a, b, c in edges]
    if any(w < 0 for w in weights):
        return None
    return Fraction(sum(w*z for w, z in zip(weights, depths)), sum(weights))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    target = parser.parse_args().out.resolve()
    base = (ROOT / "build/spu_lossless_reduction").resolve()
    if not target.is_relative_to(base) or target == base or target.exists():
        parser.error("output must be a fresh child of build/spu_lossless_reduction")
    sys.path.insert(0, str(ROOT))
    from software.tests.test_spu_lossless_reduction import collect_results
    record, success = collect_results()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".r0_", dir=target.parent) as temporary:
        source = Path(temporary) / "results.json"
        source.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        target.mkdir()  # exclusive reservation; never replace another run
        os.replace(source, target / "results.json")
    print(json.dumps({"results": str(target / "results.json"), "pass": success}))
    return 0 if success else 1

if __name__ == "__main__":
    raise SystemExit(main())
