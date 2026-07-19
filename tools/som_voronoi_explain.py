#!/usr/bin/env python3
"""Emit the exact winner/runner-up Voronoi inequality for an SPU SOM map."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(REPO / "tools"))

from lib.som_current_monitor import bridge_feature_vector, document_nodes  # noqa: E402
from lib.rational_som import find_bmu  # noqa: E402
from som_map import load_map  # noqa: E402


def explain(document: dict, features: Sequence[int]) -> dict:
    if len(features) != 4:
        raise ValueError("exactly four integer features are required")
    nodes, feature_weights = document_nodes(document)
    if any(weight.q != 0 or weight.p != 1 for weight in feature_weights):
        raise ValueError("v1 explanation requires unit integer feature weights")
    point = bridge_feature_vector(features)
    if any(value.q != 0 for value in point):
        raise ValueError("v1 explanation requires an integer point")
    result = find_bmu(point, nodes, feature_weights)
    winner = nodes[result.best_node_id]
    runner = nodes[result.second_node_id]
    if any(value.q != 0 for value in (*winner.weights, *runner.weights)):
        raise ValueError("v1 explanation requires integer map weights")
    coefficients = tuple(
        2 * (second.p - first.p)
        for first, second in zip(winner.weights, runner.weights)
    )
    rhs = sum(value.p * value.p for value in runner.weights) - sum(
        value.p * value.p for value in winner.weights
    )
    lhs = sum(coefficient * value for coefficient, value in zip(coefficients, features))
    gap = rhs - lhs
    if result.confidence_gap.q != 0 or gap != result.confidence_gap.p:
        raise ValueError("expanded Voronoi inequality disagrees with BMU quadrance gap")
    return {
        "format": "SPU_SOM_VORONOI_EXPLANATION_V1",
        "point": list(features),
        "winner": result.best_node_id,
        "runner_up": result.second_node_id,
        "label": result.cluster_label,
        "inequality": {
            "meaning": "winner is no farther than runner_up when lhs <= rhs",
            "coefficients": list(coefficients),
            "lhs": lhs,
            "relation": "<=",
            "rhs": rhs,
            "slack": gap,
        },
        "best_quadrance": result.best_q.p,
        "second_quadrance": result.second_q.p,
        "exact_tie": gap == 0,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_file")
    parser.add_argument("features", nargs=4, type=int)
    args = parser.parse_args(argv)
    try:
        document = load_map(args.map_file)
        print(json.dumps(explain(document, args.features), indent=2, sort_keys=True))
    except (OSError, ValueError) as exc:
        print(f"SOM_VORONOI: FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
