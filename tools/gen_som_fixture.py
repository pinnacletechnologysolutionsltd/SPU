#!/usr/bin/env python3
"""
Generate SOM fixture: Iris dataset quantized to Q(√3) surds + 64-node hex grid.

Outputs:
  tools/build/som_weights_64.h    — C header for firmware (SOM_WEIGHTS[64][4])
  tools/build/som_weights_64.py   — Python module for oracle tests
  tools/build/som_iris_accuracy.txt  — Classification accuracy report
"""

import argparse
import json
import math
import os
import sys
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "software"))
from lib.rational_som import RationalSurd as Rs, find_bmu, SomNode, rs

OUT = REPO / "tools" / "build"
OUT.mkdir(parents=True, exist_ok=True)

# ── Iris dataset loader ────────────────────────────────────────────────

def load_iris():
    """Return (features, labels) where features is list of 4-tuple floats."""
    try:
        from sklearn.datasets import load_iris
        data = load_iris()
        return data.data.tolist(), data.target.tolist()
    except ImportError:
        pass
    # Fallback: download from UCI
    import urllib.request
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    resp = urllib.request.urlopen(url)
    lines = resp.read().decode().strip().split("\n")
    features, labels = [], []
    label_map = {"Iris-setosa": 0, "Iris-versicolor": 1, "Iris-virginica": 2}
    for line in lines:
        if not line:
            continue
        parts = line.split(",")
        if len(parts) != 5:
            continue
        feats = [float(x) for x in parts[:4]]
        features.append(feats)
        labels.append(label_map.get(parts[4], 0))
    return features, labels


# ── Quantization ───────────────────────────────────────────────────────

def quantize_iris(features, scale=1000, bits=18):
    """Map float feature vectors to 18-bit signed surds (rational part only)."""
    qfeats = []
    max_val = 0
    for fv in features:
        qv = tuple(int(round(v * scale)) for v in fv)
        max_val = max(max_val, max(abs(v) for v in qv))
        qfeats.append(qv)
    limit = 2 ** (bits - 1) - 1
    assert max_val < limit, f"Quantized value {max_val} exceeds {bits}-bit signed range"
    return qfeats


# ── Hex grid generation ────────────────────────────────────────────────

HEX_DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

def hex_ring(center_q, center_r, radius):
    """Return axial coordinates of hex ring at given radius around center."""
    if radius == 0:
        return [(center_q, center_r)]
    q, r = center_q + radius, center_r
    coords = []
    for dq, dr in HEX_DIRS:
        for _ in range(radius):
            coords.append((q, r))
            q, r = q + dq, r + dr
    return coords

def hex_grid(n_nodes):
    """Return list of (axial_q, axial_r) for first n_nodes in spiral order."""
    coords = []
    radius = 0
    while len(coords) < n_nodes:
        ring = hex_ring(0, 0, radius)
        for c in ring:
            if len(coords) >= n_nodes:
                break
            coords.append(c)
        radius += 1
    return coords


# ── Centroid assignment ────────────────────────────────────────────────

def assign_clusters(coords, n_clusters=3):
    """Assign each hex coordinate to a cluster by angular slice."""
    labels = []
    for q, r in coords:
        if q == 0 and r == 0:
            labels.append(0)
            continue
        angle = math.atan2(r * math.sqrt(3), q * 2 + r)  # axial to pixel
        angle = angle if angle >= 0 else angle + 2 * math.pi
        label = int(angle / (2 * math.pi / n_clusters)) % n_clusters
        labels.append(label)
    return labels


def compute_centroid_weights(coords, features, targets):
    """Train k-means centroids for each SOM node using Iris data.
    
    After training, each node receives the majority Iris class label
    of the samples assigned to its centroid.
    """
    import random
    random.seed(42)

    n_nodes = len(coords)
    n_feats = 4
    n_samples = len(features)

    # K-means++ initialization
    centroids = []
    indices = list(range(n_samples))
    first = random.choice(indices)
    centroids.append(list(features[first]))
    for _ in range(1, min(n_nodes, n_samples)):
        dists = []
        for s_idx in indices:
            min_d = min(sum((features[s_idx][j] - c[j]) ** 2 for j in range(n_feats))
                       for c in centroids)
            dists.append(min_d)
        total = sum(dists)
        r = random.random() * total
        cum = 0
        for s_idx, d in zip(indices, dists):
            cum += d
            if cum >= r:
                centroids.append(list(features[s_idx]))
                break
    # Pad to n_nodes
    while len(centroids) < n_nodes:
        centroids.append(list(centroids[len(centroids) % len(centroids)]))

    # K-means training (100 iterations)
    assignments = [[] for _ in range(n_nodes)]
    for _ in range(100):
        new_assign = [[] for _ in range(n_nodes)]
        for s_idx, feat in enumerate(features):
            best_d = float('inf')
            best_c = 0
            for c_idx, cent in enumerate(centroids):
                d = sum((feat[j] - cent[j]) ** 2 for j in range(n_feats))
                if d < best_d:
                    best_d = d
                    best_c = c_idx
            new_assign[best_c].append(s_idx)
        assignments = new_assign

        changed = False
        for c_idx in range(n_nodes):
            if assignments[c_idx]:
                old = list(centroids[c_idx])
                for j in range(n_feats):
                    centroids[c_idx][j] = int(round(
                        sum(features[s][j] for s in assignments[c_idx])
                        / len(assignments[c_idx])
                    ))
                if old != centroids[c_idx]:
                    changed = True
        if not changed:
            break

    # Assign each node the majority Iris class of its samples
    node_labels = []
    for c_idx in range(n_nodes):
        if assignments[c_idx]:
            votes = [0, 0, 0]
            for s_idx in assignments[c_idx]:
                votes[targets[s_idx]] += 1
            majority = max(range(3), key=lambda i: votes[i])
        else:
            # Empty cluster: assign nearest non-empty's label
            nearest = min(
                (j for j in range(n_nodes) if assignments[j]),
                key=lambda j: sum((centroids[c_idx][f] - centroids[j][f]) ** 2
                                  for f in range(n_feats))
            )
            majority = node_labels[nearest] if node_labels else 0
        node_labels.append(majority)

    # Build SomNode list with Iris-derived labels
    nodes = []
    for i, (q, r) in enumerate(coords):
        w = tuple(Rs(int(round(centroids[i][j])), 0) for j in range(4))
        nodes.append(SomNode(i, q, r, node_labels[i], w))
    return nodes


# ── Output generators ──────────────────────────────────────────────────

def pack_weight_hex(rs_val):
    """Pack a RationalSurd into {Q[17:0], P[17:0]} 36-bit hex."""
    p = rs_val.p & 0x3FFFF
    q = rs_val.q & 0x3FFFF
    return (q << 18) | p

def gen_c_header(nodes):
    """Generate C header with SOM_WEIGHTS[N][4] array."""
    n = len(nodes)
    lines = [
        f"// Auto-generated: {n}-node hex SOM fixture",
        f"// Generated by tools/gen_som_fixture.py",
        f"#ifndef SOM_WEIGHTS_{n}_H",
        f"#define SOM_WEIGHTS_{n}_H",
        "",
        "#include <stdint.h>",
        "",
        "// Per-feature packed format: data[35:0] = {Q[17:0], P[17:0]}",
        "// addr[4:2] = node_id, addr[1:0] = feature_id",
        "static const uint64_t SOM_WEIGHTS[{}][4] = {{".format(n),
    ]
    for node in nodes:
        feats = ", ".join(
            "0x{:010X}ULL".format(pack_weight_hex(node.weights[j]))
            for j in range(4)
        )
        lines.append("    {{{}}},  // node {} label {} ({},{})".format(
            feats, node.node_id, node.cluster_label, node.axial_q, node.axial_r))
    lines += [
        "};",
        "",
        "#endif // SOM_WEIGHTS_{}_H".format(n),
        "",
    ]
    return "\n".join(lines)


def gen_python_module(nodes, feature_weights):
    """Generate Python fixture module for oracle tests."""
    n = len(nodes)
    lines = [
        f'"""Auto-generated {n}-node SOM fixture for oracle tests."""',
        "from .rational_som import RationalSurd as Rs, SomNode",
        "",
        f"N_NODES = {n}",
        "FEATURE_WEIGHTS = [{}]".format(
            ", ".join("rs({})".format(fw.p) for fw in feature_weights)
        ),
        "",
        "def fixture():",
        '    """Return (nodes, feature_weights) for the {}-node hex map."""'.format(n),
        "    nodes = [",
    ]
    for node in nodes:
        ws = ", ".join("rs({}, {})".format(w.p, w.q) for w in node.weights)
        lines.append(
            "        SomNode({}, {}, {}, {}, ({}), valid=True),".format(
                node.node_id, node.axial_q, node.axial_r,
                node.cluster_label, ws
            )
        )
    lines += [
        "    ]",
        "    fw = FEATURE_WEIGHTS",
        "    return nodes, fw",
        "",
    ]
    return "\n".join(lines)


def gen_mem_files(nodes, out_dir):
    """Generate .mem files for BRAM initialization (one per feature)."""
    n = len(nodes)
    for feat in range(4):
        lines = []
        for node in nodes:
            val = pack_weight_hex(node.weights[feat])
            lines.append("{:09X}".format(val))
        path = out_dir / f"som_weights_f{feat}.mem"
        path.write_text("\n".join(lines) + "\n")
    return True


# ── Accuracy evaluation ────────────────────────────────────────────────

def evaluate(nodes, feature_weights, qfeats, targets):
    """Run all samples through BMU and report accuracy."""
    correct = 0
    total = len(qfeats)
    for i, (feat, tgt) in enumerate(zip(qfeats, targets)):
        fv = [Rs(v, 0) for v in feat]
        result = find_bmu(fv, nodes, feature_weights)
        predicted = result.cluster_label
        if predicted == tgt:
            correct += 1
    return correct, total, correct / total * 100


# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate SOM fixtures")
    parser.add_argument("--nodes", type=int, default=64,
                        help="Number of SOM nodes (default: 64)")
    parser.add_argument("--scale", type=int, default=1000,
                        help="Quantization scale factor (default: 1000)")
    parser.add_argument("--eval", action="store_true", default=True,
                        help="Run Iris accuracy evaluation")
    args = parser.parse_args()

    print("=== SOM Fixture Generator ===\n")

    # 1. Load Iris
    print("Loading Iris dataset...")
    features_f, targets = load_iris()
    print(f"  {len(features_f)} samples, {len(set(targets))} classes\n")

    # 2. Quantize
    print(f"Quantizing (scale={args.scale}, 18-bit surds)...")
    qfeats = quantize_iris(features_f, scale=args.scale)
    print(f"  Max quantized value: {max(max(abs(v) for v in f) for f in qfeats)}\n")

    # 3. Generate hex grid
    print(f"Generating {args.nodes}-node hex grid...")
    coords = hex_grid(args.nodes)
    assert len(coords) == args.nodes
    print(f"  Radius: {int(math.sqrt(args.nodes / math.pi))}\n")

    print("Computing centroid weights from Iris data via k-means...")
    feature_weights = [rs(1), rs(1), rs(1), rs(1)]  # uniform weights for Iris
    nodes = compute_centroid_weights(
        coords, qfeats, targets)
    print(f"  {len(nodes)} nodes with Iris-trained centroids\n")

    # Show label distribution
    label_counts = [0, 0, 0]
    for n in nodes:
        if n.cluster_label < 3:
            label_counts[n.cluster_label] += 1
    print(f"  Label distribution: {label_counts}\n")

    # 5. Evaluate
    if args.eval:
        print("Evaluating classification accuracy...")
        correct, total, pct = evaluate(nodes, feature_weights, qfeats, targets)
        print(f"  {correct}/{total} correct ({pct:.1f}%)\n")
        # Save accuracy report
        report = (
            f"Iris classification accuracy on {args.nodes}-node SOM fixture\n"
            f"  Quantization scale: {args.scale}\n"
            f"  Feature weights: uniform [1, 1, 1, 1]\n"
            f"  Correct: {correct}/{total} ({pct:.1f}%)\n"
        )
        (OUT / "som_iris_accuracy.txt").write_text(report)

    # 6. Generate outputs
    print("Generating output files...")

    c_hdr = gen_c_header(nodes)
    (OUT / f"som_weights_{args.nodes}.h").write_text(c_hdr)
    print(f"  C header: som_weights_{args.nodes}.h ({len(c_hdr)} bytes)")

    py_mod = gen_python_module(nodes, feature_weights)
    (OUT / f"som_weights_{args.nodes}.py").write_text(py_mod)
    print(f"  Python module: som_weights_{args.nodes}.py")

    gen_mem_files(nodes, OUT)
    print(f"  .mem files: som_weights_f[0-3].mem")

    print("\nDone.")


if __name__ == "__main__":
    main()
