#!/usr/bin/env python3
"""Exact D4 retrieval audit with independent signed-permutation controls."""

from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import subprocess

from d4_head_exact import (SELECT, apply_map, compose, inverse_map,
                           pulled_mask, rank, rational, signed_map,
                           squared_distance, word_formula)


KEYS = tuple(product(range(-2, 3), repeat=4))
QUERIES = tuple(product((-2, 0, 2), repeat=4))
SYMMETRIC = ((), (1,), (2, 1), (0, 2, 1))
ASYMMETRIC = (((), (0,)), ((), (1,)), ((1,), ()), ((), (2, 1)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite {args.output}")

    words = set(SYMMETRIC)
    words.update(word for pair in ASYMMETRIC for word in pair)
    maps = {word: signed_map(word) for word in words}
    for word, mapping in maps.items():
        for vector in KEYS:
            assert word_formula(vector, word) == apply_map(vector, mapping), (word, vector)
        assert compose(inverse_map(mapping), mapping) == signed_map(())

    heads = []
    for name, (query_word, key_word) in enumerate(ASYMMETRIC):
        query_map, key_map = maps[query_word], maps[key_word]
        heads.append({"name": f"h{name}", "query_word": query_word,
                      "key_word": key_word, "query_map": query_map,
                      "key_map": key_map, "mask": pulled_mask(query_map),
                      "relative": compose(inverse_map(query_map), key_map),
                      "rankings": [], "mask_top5_changes": 0,
                      "reference_top5_hits": 0, "reference_top1_hits": 0})

    for query in QUERIES:
        candidates = tuple(key for key in KEYS if key != query)
        assert len(candidates) == 624
        reference_rank = rank(query, candidates,
                              lambda q, k: squared_distance(q, k, range(4)))

        for word in SYMMETRIC:
            transformed_query = word_formula(query, word)
            mapping = maps[word]
            mask = pulled_mask(mapping)
            full_scores = {}
            mask_scores = {}
            for key in candidates:
                transformed_key = word_formula(key, word)
                full_scores[key] = squared_distance(transformed_query,
                                                    transformed_key, range(4))
                mask_scores[key] = squared_distance(transformed_query,
                                                    transformed_key, SELECT)
                assert full_scores[key] == squared_distance(query, key, range(4))
                assert mask_scores[key] == squared_distance(query, key, mask)
            assert rank(query, candidates, lambda q, k: full_scores[k]) == reference_rank
            assert rank(query, candidates, lambda q, k: mask_scores[k]) == rank(
                query, candidates,
                lambda q, k: squared_distance(q, k, mask))

        for head in heads:
            query_word, key_word = head["query_word"], head["key_word"]
            transformed_query = word_formula(query, query_word)
            scores = {}
            for key in candidates:
                transformed_key = word_formula(key, key_word)
                score = squared_distance(transformed_query, transformed_key, SELECT)
                scores[key] = score
                assert score == squared_distance(
                    apply_map(query, head["query_map"]),
                    apply_map(key, head["key_map"]), SELECT)
                assert score == squared_distance(
                    query, apply_map(key, head["relative"]), head["mask"])
            ordering = rank(query, candidates, lambda q, k: scores[k])
            head["rankings"].append(ordering)
            mask_rank = rank(query, candidates, lambda q, k:
                             squared_distance(q, k, head["mask"]))
            head["mask_top5_changes"] += set(ordering[:5]) != set(mask_rank[:5])
            head["reference_top5_hits"] += len(set(ordering[:5]) &
                                                 set(reference_rank[:5]))
            head["reference_top1_hits"] += ordering[0] == reference_rank[0]
            head.setdefault("mask_reference_top5_hits", 0)
            head["mask_reference_top5_hits"] += len(set(mask_rank[:5]) &
                                                      set(reference_rank[:5]))
            head.setdefault("mask_reference_top1_hits", 0)
            head["mask_reference_top1_hits"] += mask_rank[0] == reference_rank[0]

    pairs = []
    count = len(QUERIES)
    n = len(KEYS) - 1
    for first in range(len(heads)):
        for second in range(first + 1, len(heads)):
            exact_equal = 0
            rho_sum = Fraction()
            jaccard_sum = Fraction()
            top5_changes = 0
            for left, right in zip(heads[first]["rankings"],
                                   heads[second]["rankings"]):
                exact_equal += left == right
                positions = {key: index for index, key in enumerate(right)}
                squared_delta = sum((index - positions[key]) ** 2
                                    for index, key in enumerate(left))
                rho_sum += 1 - Fraction(6 * squared_delta, n * (n * n - 1))
                left_top, right_top = set(left[:5]), set(right[:5])
                intersection = len(left_top & right_top)
                jaccard_sum += Fraction(intersection,
                                        len(left_top | right_top))
                top5_changes += left_top != right_top
            pairs.append({"heads": [heads[first]["name"], heads[second]["name"]],
                          "exact_ranking_equal_queries": exact_equal,
                          "top5_changed_queries": top5_changes,
                          "mean_spearman": rational(rho_sum / count),
                          "mean_top5_jaccard_similarity":
                              rational(jaccard_sum / count)})

    output_heads = []
    for head in heads:
        output_heads.append({key: value for key, value in head.items()
                             if key not in ("rankings", "query_map", "key_map")})
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True))
    summary = {"format": "SPU_D4_STRUCTURED_HEAD_RETRIEVAL_P0_V1",
               "revision": revision, "dirty": dirty, "keys": len(KEYS),
               "queries": count, "candidates_per_query": n, "top_k": 5,
               "selected_output_coordinates": SELECT, "symmetric_words": SYMMETRIC,
               "heads": output_heads, "head_pairs": pairs,
               "asymmetric_non_degenerate_on_domain": any(
                   head["mask_top5_changes"] for head in heads),
               "algebraic_audit": "PASS"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"D4 structured-head P0: PASS; keys={len(KEYS)} queries={count} "
          f"pairs={len(pairs)}; non_degenerate={summary['asymmetric_non_degenerate_on_domain']}")
    print(f"evidence: {args.output}")


if __name__ == "__main__":
    main()
