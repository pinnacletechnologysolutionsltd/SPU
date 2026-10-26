"""Small exact-integer models for the Soul-0 bounded experiment."""

from __future__ import annotations

from dataclasses import dataclass
import json


SCHEMA_VERSION = 1
STATE_BUDGET_BYTES = 64


@dataclass(frozen=True)
class DeviceCalibration:
    """Device-specific raw-to-normalized integer conversion."""

    gain: int
    offset: int

    def __post_init__(self) -> None:
        if self.gain <= 0:
            raise ValueError("gain must be positive")

    def encode(self, normalized: int) -> int:
        return self.gain * normalized + self.offset

    def normalize(self, raw: int) -> int:
        delta = raw - self.offset
        quotient, remainder = divmod(delta, self.gain)
        if remainder:
            raise ValueError("raw value is not exactly representable by calibration")
        return quotient


@dataclass
class _Profile:
    center: int
    count: int

    def observe(self, value: int) -> int:
        """Update an integer running mean and return model-level op count."""
        self.center = (self.center * self.count + value) // (self.count + 1)
        self.count += 1
        return 4  # multiply, add, floor-divide, count increment


class StatelessBaseline:
    def __init__(self, center: int, threshold: int) -> None:
        self.center = center
        self.threshold = threshold

    def observe(self, value: int) -> tuple[bool, int]:
        return abs(value - self.center) > self.threshold, 3

    @property
    def logical_state_bytes(self) -> int:
        return 4


class RollingMeanBaseline:
    """Conventional finite-window adaptive baseline."""

    def __init__(self, initial_values: list[int], threshold: int, window: int = 8) -> None:
        if len(initial_values) != window:
            raise ValueError("initial_values must fill the configured window")
        self.values = list(initial_values)
        self.threshold = threshold
        self.window = window

    def observe(self, value: int) -> tuple[bool, int]:
        mean = sum(self.values) // len(self.values)
        alert = abs(value - mean) > self.threshold
        self.values.pop(0)
        self.values.append(value)
        # Sum additions, floor division, subtraction, absolute value, comparison.
        return alert, len(self.values) + 3

    @property
    def logical_state_bytes(self) -> int:
        return 4 * self.window


class Soul0:
    """Two-regime prototype memory with confirmation before regime creation."""

    def __init__(
        self,
        profiles: list[tuple[int, int]],
        threshold: int = 20,
        capacity: int = 2,
        confirm_count: int = 3,
        candidate: tuple[int, int] | None = None,
    ) -> None:
        if not profiles or len(profiles) > capacity:
            raise ValueError("profile count must be in 1..capacity")
        if threshold < 0 or capacity < 1 or confirm_count < 2:
            raise ValueError("invalid Soul-0 parameters")
        if any(count < 1 for _, count in profiles):
            raise ValueError("profile counts must be positive")
        if candidate is not None and (candidate[1] < 1 or candidate[1] >= confirm_count):
            raise ValueError("candidate count must be below confirmation threshold")
        self.profiles = [_Profile(center, count) for center, count in profiles]
        self.threshold = threshold
        self.capacity = capacity
        self.confirm_count = confirm_count
        self.candidate = candidate

    @classmethod
    def seeded(cls, values: list[int], threshold: int = 20) -> "Soul0":
        if not values:
            raise ValueError("seed values cannot be empty")
        return cls([(sum(values) // len(values), len(values))], threshold=threshold)

    def observe(self, value: int) -> tuple[bool, int]:
        distances = [abs(value - profile.center) for profile in self.profiles]
        best_index = min(range(len(distances)), key=lambda index: (distances[index], index))
        best_distance = distances[best_index]
        operations = 3 * len(self.profiles) + 1

        if best_distance <= self.threshold:
            operations += self.profiles[best_index].observe(value)
            self.candidate = None
            return False, operations

        if self.candidate is None:
            self.candidate = (value, 1)
            operations += 1
        else:
            candidate_center, candidate_count = self.candidate
            candidate_distance = abs(value - candidate_center)
            operations += 3
            if candidate_distance <= self.threshold:
                updated_count = candidate_count + 1
                candidate_center = (candidate_center * candidate_count + value) // updated_count
                operations += 4
                self.candidate = (candidate_center, updated_count)
            else:
                self.candidate = (value, 1)
                operations += 1

        if self.candidate is not None and self.candidate[1] >= self.confirm_count:
            if len(self.profiles) < self.capacity:
                self.profiles.append(_Profile(*self.candidate))
                operations += 1
            self.candidate = None
        return True, operations

    @property
    def logical_state_bytes(self) -> int:
        profile_bytes = 8 * len(self.profiles)  # signed 32-bit center + count
        candidate_bytes = 8 if self.candidate is not None else 0
        return profile_bytes + candidate_bytes

    def to_bytes(self) -> bytes:
        document = {
            "schema_version": SCHEMA_VERSION,
            "threshold": self.threshold,
            "capacity": self.capacity,
            "confirm_count": self.confirm_count,
            "profiles": [{"center": p.center, "count": p.count} for p in self.profiles],
            "candidate": None if self.candidate is None else {
                "center": self.candidate[0], "count": self.candidate[1]
            },
        }
        return json.dumps(document, sort_keys=True, separators=(",", ":")).encode("ascii")

    @classmethod
    def from_bytes(cls, encoded: bytes) -> "Soul0":
        try:
            document = json.loads(encoded.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid Soul-0 checkpoint encoding") from exc
        expected = {
            "schema_version", "threshold", "capacity", "confirm_count", "profiles", "candidate"
        }
        if not isinstance(document, dict) or set(document) != expected:
            raise ValueError("Soul-0 checkpoint fields do not match schema")
        if document["schema_version"] != SCHEMA_VERSION:
            raise ValueError("unsupported Soul-0 schema version")
        if not all(type(document[key]) is int for key in ("threshold", "capacity", "confirm_count")):
            raise ValueError("Soul-0 parameters must be integers")
        profile_rows = document["profiles"]
        if not isinstance(profile_rows, list):
            raise ValueError("profiles must be a list")
        profiles: list[tuple[int, int]] = []
        for row in profile_rows:
            if not isinstance(row, dict) or set(row) != {"center", "count"}:
                raise ValueError("invalid profile record")
            if type(row["center"]) is not int or type(row["count"]) is not int:
                raise ValueError("profile values must be integers")
            profiles.append((row["center"], row["count"]))
        candidate_row = document["candidate"]
        candidate = None
        if candidate_row is not None:
            if not isinstance(candidate_row, dict) or set(candidate_row) != {"center", "count"}:
                raise ValueError("invalid candidate record")
            if type(candidate_row["center"]) is not int or type(candidate_row["count"]) is not int:
                raise ValueError("candidate values must be integers")
            candidate = (candidate_row["center"], candidate_row["count"])
        return cls(
            profiles,
            threshold=document["threshold"],
            capacity=document["capacity"],
            confirm_count=document["confirm_count"],
            candidate=candidate,
        )
