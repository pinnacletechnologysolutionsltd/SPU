"""Deterministic D4-CYCLE-0 consistency, corruption and holonomy fixtures."""

import argparse
import json
from pathlib import Path

from software.research.lattice_comparison import d4

from .cycle import IDENTITY_D4, compose_edges, edge_from_frames, inverse, matches_expected
from .types import FrameID, GroupElementD4


FRAMES = tuple(FrameID(name) for name in "ABCD")
GAUGES = (
    GroupElementD4(d4.IDENTITY),
    GroupElementD4(d4.GENERATORS[0]),
    GroupElementD4(d4.descriptor((1, 3))),
    GroupElementD4(d4.descriptor((0, 2, 3))),
)
CYCLES = (
    ("ABC", "A", "B", "C", "A"),
    ("ABD", "A", "B", "D", "A"),
    ("ACD", "A", "C", "D", "A"),
    ("BCD", "B", "C", "D", "B"),
    ("ABCD", "A", "B", "C", "D", "A"),
    ("ABDC", "A", "B", "D", "C", "A"),
    ("ACBD", "A", "C", "B", "D", "A"),
)
CORRUPT_BY = GroupElementD4(d4.descriptor((0, 1, 2)))
HOLONOMY = GroupElementD4(d4.descriptor((0, 3)))


def _cycle_edges(names, edge_map):
    return tuple(edge_map[(FRAMES[ord(a) - ord("A")], FRAMES[ord(b) - ord("A")])]
                 for a, b in zip(names, names[1:]))


def _cycle_records(edge_map, expected=IDENTITY_D4):
    records = []
    for fixture in CYCLES:
        name, *nodes = fixture
        edges = _cycle_edges(nodes, edge_map)
        product = compose_edges(edges)
        records.append({"cycle": name, "product": product.descriptor,
                        "expected": expected.descriptor, "matches": product == expected})
    return records


def evaluate():
    edge_map = {}
    for i, source in enumerate(FRAMES):
        for j, target in enumerate(FRAMES):
            if i != j:
                edge_map[(source, target)] = edge_from_frames(
                    source, target, GAUGES[i], GAUGES[j])
    consistent = _cycle_records(edge_map)

    corrupted = dict(edge_map)
    forward_key = (FRAMES[0], FRAMES[1])
    original = corrupted[forward_key]
    changed = GroupElementD4(d4.compose(CORRUPT_BY.descriptor,
                                         original.element.descriptor))
    corrupted[forward_key] = type(original)(original.source, original.target, changed)
    reverse_key = (FRAMES[1], FRAMES[0])
    reverse = corrupted[reverse_key]
    corrupted[reverse_key] = type(reverse)(reverse.source, reverse.target, inverse(changed))
    corrupted_records = _cycle_records(corrupted)
    inconsistent = [row for row in corrupted_records if not row["matches"]]
    candidates = sorted({f"{a}->{b}" for row in inconsistent
                         for a, b in zip(row["cycle"], row["cycle"][1:])})

    a, b, c = FRAMES[:3]
    nontrivial_path = (
        type(edge_map[(a, b)])(a, b, IDENTITY_D4),
        type(edge_map[(b, c)])(b, c, IDENTITY_D4),
        type(edge_map[(c, a)])(c, a, HOLONOMY),
    )
    nontrivial_product = compose_edges(nontrivial_path)
    return {
        "study": "D4-CYCLE-0",
        "group_order": len(d4.group()),
        "consistent_graph": {"cycles": consistent,
                             "all_identity": all(row["matches"] for row in consistent)},
        "corrupted_graph": {"corrupted_edge": "A->B",
                            "cycles": corrupted_records,
                            "inconsistent_cycles": [row["cycle"] for row in inconsistent],
                            "candidate_edges_only": candidates,
                            "unique_fault_localization_claimed": False},
        "prescribed_holonomy": {
            "expected": HOLONOMY.descriptor,
            "actual": nontrivial_product.descriptor,
            "matches_declared_expectation": matches_expected(nontrivial_path, HOLONOMY),
            "matches_identity_expectation": matches_expected(nontrivial_path, IDENTITY_D4),
        },
        "claim_scope": "exact finite-group cycle checks for frozen fixtures; no arbitrary-cycle error, source trust, localization, learning, performance, or hardware claim",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise SystemExit("refusing to overwrite output: " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evaluate(), indent=2, sort_keys=True) + "\n")
    print(target)


if __name__ == "__main__":
    main()
