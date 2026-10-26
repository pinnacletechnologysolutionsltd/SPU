"""Operation-counted integer models matching the Soul-0 reference semantics."""

from __future__ import annotations

from .model import _Profile, RollingMeanBaseline, Soul0, StatelessBaseline


def _profile_update(profile: _Profile, value: int) -> int:
    product = profile.center * profile.count
    numerator = product + value
    next_count = profile.count + 1
    profile.center = numerator // next_count
    profile.count = next_count
    return 4


class CountedStateless(StatelessBaseline):
    def observe(self, value: int) -> tuple[bool, int]:
        delta = value - self.center
        magnitude = abs(delta)
        return magnitude > self.threshold, 3


class CountedRollingMean(RollingMeanBaseline):
    def observe(self, value: int) -> tuple[bool, int]:
        total = self.values[0]
        operations = 0
        for previous in self.values[1:]:
            total = total + previous
            operations += 1
        mean = total // len(self.values)
        delta = value - mean
        magnitude = abs(delta)
        alert = magnitude > self.threshold
        operations += 4
        self.values.pop(0)
        self.values.append(value)
        return alert, operations


class CountedSoul0(Soul0):
    """Soul-0 state transitions with each executed primitive counted in place."""

    def observe(self, value: int) -> tuple[bool, int]:
        operations = 0
        distances: list[int] = []
        for profile in self.profiles:
            delta = value - profile.center
            distance = abs(delta)
            distances.append(distance)
            operations += 2

        best_index = 0
        best_distance = distances[0]
        for index in range(1, len(distances)):
            is_closer = distances[index] < best_distance
            operations += 1
            if is_closer:
                best_index = index
                best_distance = distances[index]

        within_profile = best_distance <= self.threshold
        operations += 1
        if within_profile:
            operations += _profile_update(self.profiles[best_index], value)
            self.candidate = None
            return False, operations

        if self.candidate is None:
            self.candidate = (value, 1)
        else:
            candidate_center, candidate_count = self.candidate
            delta = value - candidate_center
            candidate_distance = abs(delta)
            operations += 2
            within_candidate = candidate_distance <= self.threshold
            operations += 1
            if within_candidate:
                updated_count = candidate_count + 1
                product = candidate_center * candidate_count
                numerator = product + value
                candidate_center = numerator // updated_count
                operations += 4
                self.candidate = (candidate_center, updated_count)
            else:
                self.candidate = (value, 1)

        has_candidate = self.candidate is not None
        confirmed = has_candidate and self.candidate[1] >= self.confirm_count
        if has_candidate:
            operations += 1
        if confirmed:
            has_capacity = len(self.profiles) < self.capacity
            operations += 1
            if has_capacity:
                self.profiles.append(_Profile(*self.candidate))
            self.candidate = None
        return True, operations


def as_reference_soul(model: CountedSoul0) -> Soul0:
    """Return the canonical reference type with identical persistent state."""
    profiles = [(profile.center, profile.count) for profile in model.profiles]
    return Soul0(
        profiles,
        threshold=model.threshold,
        capacity=model.capacity,
        confirm_count=model.confirm_count,
        candidate=model.candidate,
    )
