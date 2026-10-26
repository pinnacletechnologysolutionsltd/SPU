"""Falsifiable preparation checks; preserve P1 defaults and exercise new widths."""

import copy
import importlib.util
from pathlib import Path

from d4_decision_p1 import train
from d4_decision_p1b_data import ARMS, samples
from d4_decision_p1b_metrics import evaluate, aggregate
from d4_decision_p1b_audit import check_row, check_aggregate


def check(prepared, old_learner):
    reps, folds, orbits, canon, transforms, inverses, observations, report = prepared
    spec = importlib.util.spec_from_file_location("d4_p1_before", old_learner)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    fixture = (((-4, 2, 0, 0), 0, 3), ((1, 1, 2, 4), 1, 2),
               ((0, 0, 0, 0), 2, 5), ((3, 2, 1, 0), 1, 1))
    comparisons = 0
    for som in (False, True):
        for capacity in (1, 2, 4):
            assert train(fixture, capacity, som) == original.train(fixture, capacity, som)
            comparisons += 1
    wide = (((100, -100, 75, -75), 1, 1),)
    assert train(wide, 1, False, (-128, 127), False)[0] == (wide[0][0],)
    try:
        train((((128, 0, 0, 0), 0, 1),), 1, False, (-128, 127), False)
    except AssertionError:
        pass
    else:
        raise AssertionError("out-of-range fixed-point input accepted")
    weight_checks = metric_checks = 0
    for held_out in folds:
        ranks = tuple((rank, rep) for rank, rep in enumerate(reps) if rep not in held_out)
        for arm in ARMS:
            training = samples(arm, ranks, observations, canon)
            assert sum(weight for _, _, weight in training) == len(ranks) * 384
            assert all(rep not in held_out for _, rep in ranks)
            weight_checks += 1
    ranks = tuple(enumerate(reps[:3]))
    for arm in ARMS:
        training = samples(arm, ranks, observations, canon)
        bounds = (-128, 127) if "noisy" in arm else (-4, 4)
        prototypes, labels, _, _ = train(training, 2, arm.endswith("som"), bounds, "noisy" not in arm)
        row = {"arm": arm, "capacity": 2, "prototypes": prototypes, "node_labels": labels,
               "profiles": evaluate(arm, prototypes, labels, ranks, orbits, canon, transforms, inverses, observations)}
        metric_checks += check_row(row, reps, observations, canon, orbits)
        corrupted = copy.deepcopy(row)
        corrupted["profiles"][0]["confusion"][0][0] += 1
        try:
            check_row(corrupted, reps, observations, canon, orbits)
        except AssertionError:
            pass
        else:
            raise AssertionError("independent audit accepted corrupted confusion")
    aggregate_fixture = []
    for fold, held_out in enumerate(folds):
        ranks = tuple((rank, rep) for rank, rep in enumerate(reps) if rep in held_out)
        aggregate_fixture.append({"fold": fold, "arm": "canonical_q_codebook", "capacity": 1,
            "prototypes": ((0, 0, 0, 0),), "node_labels": (0,), "training_records": 1,
            "training_distance_evaluations": 13, "coordinate_updates": 48,
            "profiles": evaluate("canonical_q_codebook", ((0, 0, 0, 0),), (0,), ranks,
                                 orbits, canon, transforms, inverses, observations)})
    totals = aggregate(aggregate_fixture, ("canonical_q_codebook",), (1,))
    aggregate_checks = check_aggregate(aggregate_fixture, totals)
    corrupted = copy.deepcopy(totals)
    corrupted[0]["equal_profile_mean"]["equal_base_error"]["numerator"] += 1
    try:
        check_aggregate(aggregate_fixture, corrupted)
    except AssertionError:
        pass
    else:
        raise AssertionError("independent audit accepted corrupted aggregate")
    return {"p1_default_preservation_cases": comparisons, "arm_fold_weight_checks": weight_checks,
            "aggregate_checks": aggregate_checks, "corrupted_aggregate_rejected": True,
            "independent_prediction_checks": metric_checks, "corrupted_metric_controls_rejected": len(ARMS),
            "fixed_point_overflow_rejected": True, "wide_prototype_not_clamped": True}
