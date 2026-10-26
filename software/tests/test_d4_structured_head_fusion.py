#!/usr/bin/env python3
"""Frozen P0 D4 heads as bounded exact candidate generators."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess

from d4_head_exact import (SELECT, apply_map, pulled_mask, rank, rational,
                           signed_map, squared_distance, word_formula)
from test_d4_structured_head_retrieval import ASYMMETRIC, KEYS, QUERIES


BUDGETS = (1, 2, 5, 10, 20)
RULES = ("union", "vote", "rrf", "rank_sum")
SOURCES = ("d4", "signed_permutation", "mask")


def choose(rankings, budget, rule):
    contributors = {}
    for ordering in rankings:
        for position, key in enumerate(ordering[:budget]):
            contributors.setdefault(key, []).append(position)
    if rule == "union":
        selected = tuple(sorted(contributors))
    elif rule == "vote":
        selected = sorted(contributors,
                          key=lambda key: (-len(contributors[key]),
                                           sum(contributors[key]), key))[:2 * budget]
    elif rule == "rrf":
        selected = sorted(contributors,
                          key=lambda key: (-sum(Fraction(1, position + 1)
                                                for position in contributors[key]),
                                           key))[:2 * budget]
    elif rule == "rank_sum":
        selected = sorted(contributors,
                          key=lambda key: (sum(contributors[key]) +
                                           (4 - len(contributors[key])) * budget,
                                           key))[:2 * budget]
    else:
        raise AssertionError(f"unknown rule: {rule}")
    return tuple(selected)


def head_rankings(query, candidates):
    d4, signed, mask = [], [], []
    for query_word, key_word in ASYMMETRIC:
        query_map, key_map = signed_map(query_word), signed_map(key_word)
        transformed_query = word_formula(query, query_word)
        d4.append(rank(query, candidates, lambda q, k: squared_distance(
            transformed_query, word_formula(k, key_word), SELECT)))
        signed.append(rank(query, candidates, lambda q, k: squared_distance(
            apply_map(q, query_map), apply_map(k, key_map), SELECT)))
        mask.append(rank(query, candidates, lambda q, k: squared_distance(
            q, k, pulled_mask(query_map))))
    assert d4 == signed, (query, "D4 and signed-permutation rankings differ")
    return {"d4": d4, "signed_permutation": signed, "mask": mask}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite {args.output}")

    totals = {(source, budget, rule): {"candidates": [], "hits": 0}
              for source in SOURCES for budget in BUDGETS for rule in RULES}
    for query in QUERIES:
        candidates = tuple(key for key in KEYS if key != query)
        assert len(candidates) == 624
        reference = rank(query, candidates,
                         lambda q, k: squared_distance(q, k, range(4)))
        reference_top = set(reference[:5])
        rankings = head_rankings(query, candidates)
        for budget in BUDGETS:
            for rule in RULES:
                chosen = {source: choose(rankings[source], budget, rule)
                          for source in SOURCES}
                assert chosen["d4"] == chosen["signed_permutation"]
                for source, selected in chosen.items():
                    assert len(selected) <= 4 * budget
                    if rule != "union":
                        assert len(selected) <= 2 * budget
                    reranked = rank(query, selected,
                                    lambda q, k: squared_distance(q, k, range(4)))
                    hits = len(reference_top & set(selected))
                    assert hits == len(reference_top & set(reranked[:5]))
                    record = totals[(source, budget, rule)]
                    record["candidates"].append(len(selected))
                    record["hits"] += hits

    points = []
    for source in SOURCES:
        for budget in BUDGETS:
            for rule in RULES:
                record = totals[(source, budget, rule)]
                counts = record["candidates"]
                points.append({"source": source, "per_head_top_b": budget,
                               "rule": rule, "mean_candidates":
                                   rational(Fraction(sum(counts), len(counts))),
                               "min_candidates": min(counts),
                               "max_candidates": max(counts),
                               "reference_top5_hits": record["hits"],
                               "reference_top5_total": len(QUERIES) * 5,
                               "recall": rational(Fraction(record["hits"],
                                                           len(QUERIES) * 5))})

    for budget in BUDGETS:
        for rule in RULES:
            d4 = totals[("d4", budget, rule)]
            signed = totals[("signed_permutation", budget, rule)]
            assert d4 == signed
    comparisons = []
    mask_points = [point for point in points if point["source"] == "mask"]
    for point in (p for p in points if p["source"] == "d4"):
        budget, rule = point["per_head_top_b"], point["rule"]
        own = totals[("d4", budget, rule)]
        matched = totals[("mask", budget, rule)]
        d4_mean = Fraction(sum(own["candidates"]), len(QUERIES))
        mask_mean = Fraction(sum(matched["candidates"]), len(QUERIES))
        dominated = any(
            (other_hits := other["reference_top5_hits"]) >= own["hits"] and
            (other_mean := Fraction(other["mean_candidates"]["numerator"],
                                    other["mean_candidates"]["denominator"])) <= d4_mean
            and (other_hits > own["hits"] or other_mean < d4_mean)
            for other in mask_points)
        comparisons.append({"per_head_top_b": budget, "rule": rule,
                            "d4_minus_matched_mask_hits": own["hits"] - matched["hits"],
                            "d4_minus_matched_mask_mean_candidates":
                                rational(d4_mean - mask_mean),
                            "strictly_dominated_by_some_mask_point": dominated})

    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True))
    summary = {"format": "SPU_D4_STRUCTURED_HEAD_FUSION_P1_V1",
               "revision": revision, "dirty": dirty, "keys": len(KEYS),
               "queries": len(QUERIES), "top_k": 5, "budgets": BUDGETS,
               "rules": RULES, "points": points, "comparisons": comparisons,
               "signed_permutation_parity": "PASS", "algebraic_audit": "PASS"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"D4 fusion P1: PASS; {len(points)} points; "
          f"{sum(item['strictly_dominated_by_some_mask_point'] for item in comparisons)}"
          " of 20 D4 points dominated by a mask point")
    print(f"evidence: {args.output}")


if __name__ == "__main__":
    main()
