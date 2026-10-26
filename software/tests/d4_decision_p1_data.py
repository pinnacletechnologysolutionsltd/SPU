"""Frozen orbit-aware exact dataset and folds for D4 decision P1."""

from __future__ import annotations

from collections import Counter

from d4_canonical_exact import GROUP, STATES, act, chamber, norm


def task_label(x):
    value = norm(x)
    return 0 if value <= 12 else 1 if value <= 30 else 2


def dataset():
    orbit_by_rep = {}
    canon = {}
    transform = {}
    for x in STATES:
        matches = [(w, act(w, x)) for w in GROUP if chamber(act(w, x))]
        distinct = {image for _, image in matches}
        assert len(distinct) == 1
        representative = next(iter(distinct))
        canon[x] = representative
        transform[x] = matches[0][0]
        if representative not in orbit_by_rep:
            orbit_by_rep[representative] = tuple(sorted({act(w, x) for w in GROUP}))
    reps = tuple(sorted(orbit_by_rep))
    assert len(reps) == 57
    assert tuple(Counter(task_label(c) for c in reps)[i] for i in range(3)) == (13, 24, 20)
    folds = [[] for _ in range(5)]
    for label in range(3):
        for position, rep in enumerate(c for c in reps if task_label(c) == label):
            folds[position % 5].append(rep)
    folds = tuple(tuple(sorted(fold)) for fold in folds)
    assert set().union(*(set(fold) for fold in folds)) == set(reps)
    assert sum(map(len, folds)) == len(reps)
    assert all({task_label(c) for c in fold} == {0, 1, 2} for fold in folds)
    assert sum(len(orbit) for orbit in orbit_by_rep.values()) == len(STATES)
    return reps, folds, orbit_by_rep, canon, transform


def samples(arm, train_reps, all_reps, orbit_by_rep):
    records = []
    for rep in train_reps:
        label = task_label(rep)
        if arm.startswith("canonical"):
            points = (rep,)
        elif "augmented" in arm:
            points = orbit_by_rep[rep]
        else:
            rank = all_reps.index(rep)
            points = (act(GROUP[(37 * rank + 11) % 192], rep),)
        assert 192 % len(points) == 0
        weight = 192 // len(points)
        records.extend((point, label, weight) for point in points)
    return tuple(sorted(records))
