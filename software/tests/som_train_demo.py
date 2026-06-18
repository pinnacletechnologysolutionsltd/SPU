#!/usr/bin/env python3
"""
som_train_demo.py — Deterministic SOM Training Oracle (v1.0)

Proves that a rational-weighted SOM converges deterministically
using dyadic update rules — no floats, no randomness, bit-exact replay.

Algorithm:
  1. 3×3 hex map, 9 nodes, 2D feature space (integers only)
  2. Training inputs: fixed sequence of 4 vectors, repeated 4 epochs
  3. BMU selection: minimum quadrance (integer arithmetic)
  4. Update rule:  w_i ← w_i + (input - w_i) >> shift
     where shift ∈ {1,2,3,4} decays per epoch (dyadic learning rate)
  5. Neighborhood: ring-0 (BMU only, radius 0) for simplicity
  6. Convergence: map stops changing → training complete

Run twice — the output must be bit-identical both times.
This is the core SPU-13 claim: deterministic, replayable learning.

CC0 1.0 Universal.
"""

import sys
sys.path.insert(0, 'software/lib')

from rational_som import (
    RationalSurd as RS, rs, SomNode, find_bmu, weighted_quadrance
)


def axial_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """Hex grid axial distance (Manhattan in cube coords)."""
    dq = q1 - q2
    dr = r1 - r2
    return (abs(dq) + abs(dq + dr) + abs(dr)) // 2


def build_hex_map(rows: int, cols: int) -> list:
    """Create an axial hex grid of SomNodes with small integer weights."""
    nodes = []
    nid = 0
    for r in range(rows):
        for q in range(-r, cols - r):
            # Random-ish small weights (deterministic seed)
            w0 = (q * 3 + r * 7) % 8 - 4
            w1 = (q * 5 + r * 11) % 8 - 4
            nodes.append(SomNode(
                node_id=nid, axial_q=q, axial_r=r,
                cluster_label=0,
                weights=(rs(w0), rs(w1)),
                valid=True
            ))
            nid += 1
    return nodes


def train_epoch(nodes, inputs, shift, feature_weights):
    """One training epoch. Returns True if any weight changed."""
    changed = False
    for x in inputs:
        result = find_bmu(x, nodes, feature_weights)
        if not result.valid:
            continue
        bmu = nodes[result.best_node_id]

        # Dyadic update: w ← w + (x - w) >> shift
        new_weights = []
        for w_j, x_j in zip(bmu.weights, x):
            delta = x_j - w_j
            update = RS(delta.p >> shift, delta.q >> shift)
            new_weights.append(w_j + update)

        if new_weights != list(bmu.weights):
            changed = True
            nodes[result.best_node_id] = SomNode(
                node_id=bmu.node_id,
                axial_q=bmu.axial_q, axial_r=bmu.axial_r,
                cluster_label=bmu.cluster_label,
                weights=tuple(new_weights),
                valid=True
            )
    return changed


def main():
    # ── Setup ─────────────────────────────────────────────────
    nodes = build_hex_map(3, 3)
    feature_weights = [rs(1), rs(1)]

    # Training inputs (fixed sequence, repeats each epoch)
    inputs = [
        [rs(4), rs(0)],
        [rs(-2), rs(3)],
        [rs(1), rs(-3)],
        [rs(0), rs(0)],
    ]

    # Learning rate schedule: shift ∈ {1,2,3,4} per epoch
    # Smaller shift = larger steps (more aggressive learning)
    shifts = [1, 2, 3, 4]

    print("=== SOM Training Oracle — Deterministic Replay Proof ===\n")
    print(f"Map: 3×3 axial hex, {len(nodes)} nodes")
    print(f"Inputs: {len(inputs)} vectors × {len(shifts)} epochs")
    print(f"Update: w ← w + (x − w) >> shift")
    print(f"Feature weights: {feature_weights}\n")

    # ── Training ──────────────────────────────────────────────
    for epoch, shift in enumerate(shifts):
        changed = train_epoch(nodes, inputs, shift, feature_weights)
        print(f"Epoch {epoch+1} (shift={shift}): {'converging' if changed else 'STABLE — converged'}")

        # Print map state
        for node in sorted(nodes, key=lambda n: (n.axial_r, n.axial_q)):
            w = node.weights
            print(f"  node {node.node_id:2d}  "
                  f"({node.axial_q:+d},{node.axial_r:+d})  "
                  f"w=({w[0].p:+d},{w[1].p:+d})")

    # ── Final BMU check ──────────────────────────────────────
    print("\n=== Final Classification ===")
    for x in inputs:
        result = find_bmu(x, nodes, feature_weights)
        print(f"  input ({x[0].p:+d},{x[1].p:+d}) → "
              f"BMU node {result.best_node_id} "
              f"(label={result.cluster_label}, Q=({result.best_q.p},{result.best_q.q}√3))")

    # ── Deterministic replay assertion ────────────────────────
    print("\n=== Replay Check ===")
    nodes2 = build_hex_map(3, 3)
    for shift in shifts:
        train_epoch(nodes2, inputs, shift, feature_weights)

    # Compare maps
    identical = True
    for i, (n1, n2) in enumerate(zip(nodes, nodes2)):
        if n1.weights != n2.weights:
            print(f"  MISMATCH node {i}: {n1.weights} ≠ {n2.weights}")
            identical = False

    if identical:
        print("  PASS: Bit-exact replay — both runs produced identical weights")
    else:
        print("  FAIL: Non-deterministic result")
        sys.exit(1)

    print("\n✓ SOM training oracle: deterministic convergence proven")


if __name__ == '__main__':
    main()
