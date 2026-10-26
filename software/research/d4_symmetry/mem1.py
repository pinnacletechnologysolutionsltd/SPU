"""Finite exact D4 memory-strategy comparison for the D4-MEM-1 contract."""

import argparse
import hashlib
import json
from pathlib import Path

from software.research.lattice_comparison import d4

from .canonical import GROUP, IDENTITY, orbit


SOURCES = (((1, 2, 4, 7), "generic"), ((1, 1, 2, 2), "stabilizer"))
MISS = (1, 2, 4, 8)
OP_NAMES = ("vector_transforms", "key_comparisons", "witness_candidates",
            "inverse_candidates", "action_transforms", "key_probes")


def _counter():
    return {name: 0 for name in OP_NAMES}


def _canonical_counted(vector, ops):
    images = []
    for element in GROUP:
        images.append((d4.act(element, vector), element))
        ops["vector_transforms"] += 1
    key = images[0][0]
    for image, _ in images[1:]:
        ops["key_comparisons"] += 1
        if image < key:
            key = image
    for image, element in images:
        ops["witness_candidates"] += 1
        if image == key:
            return key, element
    raise AssertionError("D4_CANONICAL_WITNESS")


def _inverse_counted(element, ops):
    for candidate in GROUP:
        ops["inverse_candidates"] += 1
        if (d4.compose(candidate, element) == IDENTITY
                and d4.compose(element, candidate) == IDENTITY):
            return candidate
    raise AssertionError("D4_INVERSE")


def _json_bytes(records):
    encoded = json.dumps(records, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True).encode("utf-8")
    return len(encoded)


def _query_set():
    queries = []
    expected = {}
    for source, payload in SOURCES:
        for value in orbit(source):
            queries.append(value)
            expected[value] = (payload, value)
        queries.append(source)
        expected[source] = (payload, source)
    queries.append(MISS)
    return queries, expected


def _result(hits, expected, prep_ops, total_ops, byte_count, queries):
    supported = sum(query in expected for query in queries)
    payload_correct = sum(
        query in hits and hits[query][0] == expected[query][0]
        for query in queries if query in expected
    )
    action_correct = sum(
        query in hits and hits[query][1] == expected[query][1]
        for query in queries if query in expected
    )
    misses = sum(query not in hits for query in queries)
    false_aliases = sum(query not in expected and query in hits for query in queries)
    query_ops = {key: total_ops[key] - prep_ops[key] for key in OP_NAMES}
    return {
        "query_count": len(queries),
        "unique_supported_query_count": len(expected),
        "supported_query_occurrences": supported,
        "payload_correct_supported_queries": payload_correct,
        "action_correct_supported_queries": action_correct,
        "misses": misses,
        "false_aliases": false_aliases,
        "serialized_association_bytes": byte_count,
        "preparation_operations": prep_ops,
        "query_operations": query_ops,
        "total_operations": sum(total_ops.values()),
        "operations_per_query": {
            key: {"numerator": value, "denominator": len(queries)}
            for key, value in query_ops.items()
        },
    }


def evaluate():
    sources = tuple((x, payload, x) for x, payload in SOURCES)
    queries, expected = _query_set()
    fixture = {"sources": sources, "queries": queries}
    fixture_digest = hashlib.sha256(
        json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    raw, augmented, canonical, group_aware = {}, {}, {}, {}
    prep = {name: _counter() for name in ("raw", "augmented", "canonical", "group_aware")}

    for vector, payload, action in sources:
        raw[vector] = (payload, action)
        group_aware[vector] = (payload, action)
        for element in GROUP:
            transformed = d4.act(element, vector)
            transformed_action = d4.act(element, action)
            prep["augmented"]["vector_transforms"] += 1
            prep["augmented"]["action_transforms"] += 1
            prep["augmented"]["key_probes"] += 1
            if transformed not in augmented:
                augmented[transformed] = (payload, transformed_action)
        key, witness = _canonical_counted(vector, prep["canonical"])
        canonical_action = d4.act(witness, action)
        prep["canonical"]["action_transforms"] += 1
        canonical[key] = (payload, canonical_action)

    # Keep deterministic serialized representations separate from Python heap use.
    serialized = {
        "raw": _json_bytes([[x, p, a] for x, (p, a) in sorted(raw.items())]),
        "augmented": _json_bytes([[x, p, a] for x, (p, a) in sorted(augmented.items())]),
        "canonical": _json_bytes([[x, p, a] for x, (p, a) in sorted(canonical.items())]),
        "group_aware": _json_bytes([[x, p, a] for x, (p, a) in sorted(group_aware.items())]),
    }
    hits = {name: {} for name in serialized}
    totals = {name: _counter() for name in serialized}
    for name in totals:
        totals[name].update(prep[name])

    for query in queries:
        totals["raw"]["key_probes"] += 1
        if query in raw:
            hits["raw"][query] = raw[query]
        totals["augmented"]["key_probes"] += 1
        if query in augmented:
            hits["augmented"][query] = augmented[query]

        key, witness = _canonical_counted(query, totals["canonical"])
        totals["canonical"]["key_probes"] += 1
        if key in canonical:
            payload, action_c = canonical[key]
            action = d4.act(_inverse_counted(witness, totals["canonical"]), action_c)
            totals["canonical"]["action_transforms"] += 1
            hits["canonical"][query] = (payload, action)

        matches = []
        for representative, (payload, action) in group_aware.items():
            for element in GROUP:
                candidate = d4.act(element, representative)
                totals["group_aware"]["vector_transforms"] += 1
                totals["group_aware"]["key_comparisons"] += 1
                if candidate == query:
                    matches.append((payload, d4.act(element, action)))
                    totals["group_aware"]["action_transforms"] += 1
        if matches:
            if len(set(matches)) != 1:
                raise AssertionError("D4_GROUP_AWARE_STABILIZER_CONFLICT")
            hits["group_aware"][query] = matches[0]

    strategy_results = {
        name: _result(hits[name], expected, prep[name], totals[name], serialized[name], queries)
        for name in serialized
    }
    return {
        "group_order": len(GROUP),
        "orbit_sizes": {name: len(orbit(vector)) for vector, name in SOURCES},
        "source_association_count": len(sources),
        "fixture_sha256": fixture_digest,
        "queries_include_one_repeat_per_source_and_one_non_equivalent_miss": True,
        "serialized_format": "UTF-8 JSON, sorted keys, compact separators",
        "operation_counter_definitions": {
            "vector_transforms": "calls applying a W(D4) element to an input vector",
            "key_comparisons": "lexicographic minimum comparisons or group candidate equality checks",
            "witness_candidates": "orbit candidates scanned to select the first canonical witness",
            "inverse_candidates": "group descriptors tested to find a two-sided inverse",
            "action_transforms": "calls applying a W(D4) element to an action vector",
            "key_probes": "exact dictionary membership probes",
        },
        "strategies": strategy_results,
        "claim_scope": "finite exact workload; no learning, latency, hardware, or general advantage claim",
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
