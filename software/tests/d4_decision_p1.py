"""Deterministic integer SOM and codebook learners for D4 P1."""

from __future__ import annotations

from collections import defaultdict


CAPACITIES = (1, 2, 4, 8, 16, 32)
MULTIPLIERS = (1, 2, 3)


def squared(left, right):
    return sum((a - b) ** 2 for a, b in zip(left, right))


def winner(point, prototypes):
    distances = [squared(point, prototype) for prototype in prototypes]
    best = min(range(len(prototypes)), key=lambda i: (distances[i], i))
    runner = sorted(distances)[1] if len(distances) > 1 else None
    return best, distances[best], runner


def rounded(numerator, denominator):
    assert denominator > 0
    quotient, remainder = divmod(abs(numerator), denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2):
        quotient += 1
    return -quotient if numerator < 0 else quotient


def initial(samples, capacity):
    coordinates = sorted({point for point, _, _ in samples})
    assert len(coordinates) >= capacity
    selected = [coordinates[0]]
    while len(selected) < capacity:
        eligible = (point for point in coordinates if point not in selected)
        selected.append(min(eligible, key=lambda point: (
            -min(squared(point, chosen) for chosen in selected), point)))
    return selected


def neighborhood(capacity, radius):
    return tuple(tuple(i for i in range(capacity)
                       if min((i - winner_id) % capacity,
                              (winner_id - i) % capacity) <= radius)
                 for winner_id in range(capacity))


def train(samples, capacity, som, coordinate_bounds=(-4, 4), clamp=True):
    """Samples are (point, class, exact integer weight)."""
    assert samples and all(weight > 0 for _, _, weight in samples)
    low, high = coordinate_bounds
    assert low < high and all(low <= v <= high for p, _, _ in samples for v in p)
    prototypes = initial(samples, capacity)
    evaluations = 0
    updates = 0
    for epoch in range(12):
        radius = (2 if epoch < 4 else 1 if epoch < 8 else 0) if som else 0
        neighbors = neighborhood(capacity, radius)
        sums = [[0, 0, 0, 0] for _ in range(capacity)]
        weights = [0] * capacity
        for point, _, weight in samples:
            best, _, _ = winner(point, prototypes)
            evaluations += capacity
            for node in neighbors[best]:
                weights[node] += weight
                for axis in range(4):
                    sums[node][axis] += weight * point[axis]
        for node, denominator in enumerate(weights):
            if denominator:
                updated = tuple(rounded(value, denominator) for value in sums[node])
                prototypes[node] = tuple(max(low, min(high, v)) for v in updated) if clamp else updated
                assert all(low <= v <= high for v in prototypes[node])
                updates += 4

    classes = [defaultdict(int) for _ in range(capacity)]
    for point, label, weight in samples:
        best, _, _ = winner(point, prototypes)
        evaluations += capacity
        classes[best][label] += weight
    labels = []
    for node, totals in enumerate(classes):
        if totals:
            labels.append(min(totals, key=lambda label: (-totals[label], label)))
        else:
            nearest = min(samples, key=lambda sample: (
                squared(prototypes[node], sample[0]), sample[0], sample[1]))
            labels.append(nearest[1])
    return tuple(prototypes), tuple(labels), evaluations, updates
