#!/usr/bin/env python3
"""Tests for the exact rational SOM/BMU reference model."""

import inspect
import os
import sys
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import rational_som
from lib.rational_som import (
    RationalSurd,
    SomNode,
    classify,
    find_bmu,
    hex_neighbors,
    rs,
    tiny_hex_fixture,
    weighted_quadrance,
)


PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {label}")


def check_rs(label, got, want):
    check(f"{label}: got {got}, want {want}", got == want)


def test_integer_bmu():
    nodes, feature_weights = tiny_hex_fixture()
    features = [rs(2), rs(1), rs(0), rs(0)]

    result = find_bmu(features, nodes, feature_weights)

    check("integer BMU valid", result.valid)
    check("integer BMU best node", result.best_node_id == 1)
    check("integer BMU second node stable tie", result.second_node_id == 0)
    check("integer BMU cluster label", result.cluster_label == 1)
    check_rs("integer BMU best_q", result.best_q, rs(2))
    check_rs("integer BMU second_q", result.second_q, rs(6))
    check_rs("integer BMU confidence gap", result.confidence_gap, rs(4))
    check("integer BMU not ambiguous", classify(result)[1] is False)


def test_surd_bmu():
    nodes, feature_weights = tiny_hex_fixture()
    features = [rs(0), rs(0), rs(-2), rs(2, 1)]

    result = find_bmu(features, nodes, feature_weights)

    check("surd BMU best node", result.best_node_id == 6)
    check("surd BMU cluster label", result.cluster_label == 3)
    check_rs("surd BMU best_q", result.best_q, rs(1))
    check("surd BMU has second", result.has_second)
    check("surd BMU gap positive", rational_som.rs_lt(rs(0), result.confidence_gap))


def test_weighted_quadrance_field_square():
    got = weighted_quadrance(
        [rs(2, 1)],
        [rs(0)],
        [rs(1)],
    )
    check_rs("(2+sqrt3)^2 uses field square", got, rs(7, 4))


def test_stable_tie_breaking():
    feature_weights = [rs(1)]
    nodes = [
        SomNode(5, 0, 0, 9, (rs(0),)),
        SomNode(1, 1, 0, 7, (rs(0),)),
        SomNode(3, 0, 1, 8, (rs(0),)),
    ]

    result = find_bmu([rs(0)], nodes, feature_weights)

    check("tie best lowest node id", result.best_node_id == 1)
    check("tie second next-lowest node id", result.second_node_id == 3)
    check_rs("tie zero gap", result.confidence_gap, rs(0))
    check("tie classified ambiguous", classify(result)[1] is True)
    check("tie cluster follows best", classify(result)[0] == 7)


def test_invalid_nodes_are_skipped():
    feature_weights = [rs(1)]
    nodes = [
        SomNode(0, 0, 0, 1, (rs(0),), valid=False),
        SomNode(1, 1, 0, 2, (rs(3),)),
    ]

    result = find_bmu([rs(0)], nodes, feature_weights)

    check("invalid node skipped best", result.best_node_id == 1)
    check("invalid node skipped no second", result.has_second is False)


def test_hex_neighbor_deltas():
    check(
        "hex neighbor deltas",
        hex_neighbors(0, 0)
        == ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)),
    )


def test_no_float_or_sqrt_in_hot_model():
    source = inspect.getsource(rational_som)
    tree = ast.parse(source)
    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"float", "sqrt"}:
                forbidden.append(node.func.id)
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "sqrt":
                forbidden.append("sqrt")
    check("no sqrt call in rational_som", "sqrt" not in forbidden)
    check("no float conversion call in rational_som", "float" not in forbidden)


def main():
    test_integer_bmu()
    test_surd_bmu()
    test_weighted_quadrance_field_square()
    test_stable_tie_breaking()
    test_invalid_nodes_are_skipped()
    test_hex_neighbor_deltas()
    test_no_float_or_sqrt_in_hot_model()

    if FAIL:
        print(f"FAIL ({FAIL} failures, {PASS} passes)")
        return 1
    print(f"PASS ({PASS} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
