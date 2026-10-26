#!/usr/bin/env python3
"""Exhaustive exact D4 chamber and equivariant-decision oracle."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from test_d4_reflection_oracle import ROOTS, reflect_formula
from d4_canonical_exact import (IDENTITY, STATES, GROUP, GENERATORS, act,
                                compose, chamber, norm, label,
                                rejects_nonfixed_zero_action)


def check() -> dict:
    assert len(STATES) == 3281 and len(GROUP) == 192
    assert len(set(GROUP)) == 192 and GROUP[0] == IDENTITY
    assert ROOTS == ((1, -1, 0, 0), (0, 1, -1, 0),
                     (0, 0, 1, -1), (0, 0, 1, 1))
    group_set = set(GROUP)
    reached = {IDENTITY}
    frontier = [IDENTITY]
    for w in frontier:
        for generator in GENERATORS:
            next_w = compose(generator, w)
            assert next_w in group_set
            if next_w not in reached:
                reached.add(next_w)
                frontier.append(next_w)
    assert reached == group_set
    inverse_table = {
        w: next(v for v in GROUP if compose(w, v) == IDENTITY and
                compose(v, w) == IDENTITY) for w in GROUP
    }

    state_set = set(STATES)
    canonical = {}
    metadata = {}
    orbits = Counter()
    stabilizers = Counter()
    boundary = 0
    root_checks = 0
    image_checks = 0
    stabilizer_checks = 0
    for x in STATES:
        for generator, root in zip(GENERATORS, ROOTS):
            assert act(generator, x) == reflect_formula(x, root)
            root_checks += 1
        images = set()
        valid = []
        fixed = 0
        for w in GROUP:
            y = act(w, x)
            images.add(y)
            assert y in state_set and norm(y) == norm(x)
            assert label(y) == label(x)
            image_checks += 1
            if chamber(y):
                valid.append((w, y))
            if y == x:
                fixed += 1
        chamber_images = {y for _, y in valid}
        assert len(chamber_images) == 1
        c = next(iter(chamber_images))
        g = valid[0][0]
        assert g == min(w for w, y in valid if y == c)
        assert act(inverse_table[g], c) == x
        assert len(images) * fixed == len(GROUP)
        stabilizer_checks += 1
        assert label(c) == label(x)
        canonical[x], metadata[x] = c, g
        orbits[len(images)] += 1
        stabilizers[fixed] += 1
        boundary += any(c[i] == c[i + 1] for i in (0, 1)) or c[2] == abs(c[3])

    reps = set(canonical.values())
    assert all(canonical[c] == c and chamber(c) for c in reps)
    assert 192 in orbits and any(size < 192 for size in orbits)
    action = {}
    action_stabilizer_checks = 0
    for c in reps:
        scale = 1 + norm(c) % 3
        value = tuple(scale * v for v in c)
        for w in GROUP:
            if act(w, c) == c:
                assert act(w, value) == value
                action_stabilizer_checks += 1
    for x in STATES:
        c, g = canonical[x], metadata[x]
        f = tuple((1 + norm(c) % 3) * v for v in c)
        action[x] = act(inverse_table[g], f)
        assert action[x] == tuple((1 + norm(x) % 3) * v for v in x)

    equivariance_checks = 0
    for x in STATES:
        c = canonical[x]
        assert canonical[c] == c and chamber(c)
        for w in GROUP:
            y = act(w, x)
            assert canonical[y] == c
            assert label(y) == label(x)
            assert action[y] == act(w, action[x])
            equivariance_checks += 1

    negative_rejected = rejects_nonfixed_zero_action()
    assert negative_rejected
    return {
        "verdict": "PASS", "domain_count": len(STATES), "group_count": len(GROUP),
        "canonical_count": len(reps), "boundary_state_count": boundary,
        "orbit_size_histogram": dict(sorted(orbits.items())),
        "stabilizer_size_histogram": dict(sorted(stabilizers.items())),
        "orbit_stabilizer_checks": stabilizer_checks,
        "root_oracle_checks": root_checks, "image_norm_parity_label_checks": image_checks,
        "canonical_invariance_label_equivariance_checks": equivariance_checks,
        "canonical_idempotence_checks": len(STATES),
        "inverse_metadata_checks": len(STATES),
        "action_stabilizer_checks": action_stabilizer_checks,
        "negative_control_rejected": negative_rejected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        print(f"FAIL: evidence exists: {args.output}", file=sys.stderr)
        return 1
    try:
        result = check()
        result["source_revision"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip()
        result["source_dirty"] = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], text=True).strip())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except (AssertionError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: D4 canonical decision P0: {error}", file=sys.stderr)
        return 1
    print(f"PASS: D4 canonical decision P0; {result['domain_count']} states, "
          f"{result['canonical_count']} representatives, {result['group_count']} maps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
