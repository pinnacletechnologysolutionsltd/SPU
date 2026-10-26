"""Deterministic arithmetic and memory policies for the separate Soul-0 study."""

from __future__ import annotations

from collections import deque
import json
from typing import Any


SCALE = 256
THRESHOLD = 20
SCHEMA = 1
INPUT_MIN = -256
INPUT_MAX = 511
MAX_COUNT = 264
KINDS = ("A", "B", "C", "D", "E", "F")


def _floor_div(numerator: int, denominator: int) -> tuple[int, int]:
    return numerator // denominator, 1


class ArithmeticModel:
    """One of the six frozen policies; all observations update after alerting."""

    def __init__(self, kind: str, values: list[int], threshold: int = THRESHOLD) -> None:
        if kind not in KINDS or not values or threshold < 0:
            raise ValueError("invalid model initialization")
        if any(type(value) is not int or not INPUT_MIN <= value <= INPUT_MAX for value in values):
            raise ValueError("training value outside declared input domain")
        self.kind = kind
        self.threshold = threshold
        self.count = len(values)
        self.total = sum(values)
        self.center = self.total // self.count
        self.remainder = self.total - self.center * self.count
        self.qcenter = (SCALE * self.total) // self.count
        self.window = deque(values[-8:], maxlen=8)
        if kind == "E" and len(self.window) != 8:
            raise ValueError("rolling model requires eight training values")

    def observe(self, value: int) -> tuple[bool, int]:
        if type(value) is not int or not INPUT_MIN <= value <= INPUT_MAX:
            raise ValueError("observation outside declared input domain")
        if self.kind in ("A", "B", "C", "D") and self.count >= MAX_COUNT:
            raise OverflowError("cumulative observation count exceeds frozen bound")
        operations = 0
        if self.kind == "A":
            residual = value - self.center
            operations += 1
            magnitude = abs(residual)
            operations += 1
            alert = magnitude > self.threshold
            operations += 1
            product = self.center * self.count
            numerator = product + value
            next_count = self.count + 1
            self.center = numerator // next_count
            self.count = next_count
            operations += 4
        elif self.kind == "B":
            scaled_value = value * self.count
            residual = scaled_value - self.total
            magnitude = abs(residual)
            limit = self.threshold * self.count
            alert = magnitude > limit
            operations += 5
            self.total += value
            self.count += 1
            operations += 2
        elif self.kind == "C":
            represented_sum = self.center * self.count + self.remainder
            operations += 2
            scaled_value = value * self.count
            residual = scaled_value - represented_sum
            magnitude = abs(residual)
            limit = self.threshold * self.count
            alert = magnitude > limit
            operations += 5
            numerator = represented_sum + value
            next_count = self.count + 1
            self.center, self.remainder = divmod(numerator, next_count)
            self.count = next_count
            operations += 4
        elif self.kind == "D":
            scaled_value = value * SCALE
            residual = scaled_value - self.qcenter
            magnitude = abs(residual)
            alert = magnitude > self.threshold * SCALE
            operations += 5
            product = self.qcenter * self.count
            numerator = product + scaled_value
            next_count = self.count + 1
            self.qcenter = numerator // next_count
            self.count = next_count
            operations += 4
        elif self.kind == "E":
            total = sum(self.window)
            scaled_value = value * len(self.window)
            residual = scaled_value - total
            magnitude = abs(residual)
            limit = self.threshold * len(self.window)
            alert = magnitude > limit
            operations += len(self.window) + 4
            self.window.append(value)
        else:
            scaled_value = value * SCALE
            residual = scaled_value - self.qcenter
            magnitude = abs(residual)
            alert = magnitude > self.threshold * SCALE
            operations += 5
            weighted = self.qcenter * 7
            numerator = weighted + scaled_value
            self.qcenter = numerator // 8
            operations += 3
        return alert, operations

    def exact_center_pair(self) -> tuple[int, int]:
        """Return numerator, denominator for the represented center."""
        if self.kind == "A":
            return self.center, 1
        if self.kind == "B":
            return self.total, self.count
        if self.kind == "C":
            return self.center * self.count + self.remainder, self.count
        if self.kind == "D" or self.kind == "F":
            return self.qcenter, SCALE
        values = list(self.window)
        return sum(values), len(values)

    @property
    def logical_state_bytes(self) -> int:
        # Fixed-width state accounting from the contract, excluding config.
        if self.kind == "A":
            return 2 + 2  # signed-10 center + unsigned-9 count
        if self.kind == "B":
            return 3 + 2  # signed-19 sum + unsigned-9 count
        if self.kind == "C":
            return 2 + 2 + 2  # signed-10 center + unsigned-9 count + unsigned-9 remainder
        if self.kind in ("D", "F"):
            return (3 + 2) if self.kind == "D" else 3
        return 8 * 2  # eight signed-16 observations

    def state_document(self) -> dict[str, Any]:
        state: dict[str, Any] = {"kind": self.kind, "threshold": self.threshold}
        if self.kind == "A":
            state.update(center=self.center, count=self.count)
        elif self.kind == "B":
            state.update(total=self.total, count=self.count)
        elif self.kind == "C":
            state.update(center=self.center, remainder=self.remainder, count=self.count)
        elif self.kind == "D":
            state.update(qcenter=self.qcenter, count=self.count)
        elif self.kind == "E":
            state.update(window=list(self.window))
        else:
            state.update(qcenter=self.qcenter)
        return {"schema": SCHEMA, "state": state}

    def to_bytes(self) -> bytes:
        return json.dumps(self.state_document(), sort_keys=True, separators=(",", ":")).encode("ascii")

    @classmethod
    def from_bytes(cls, encoded: bytes) -> "ArithmeticModel":
        try:
            doc = json.loads(encoded.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid checkpoint") from exc
        if not isinstance(doc, dict) or set(doc) != {"schema", "state"} or doc["schema"] != SCHEMA:
            raise ValueError("unsupported checkpoint schema")
        state = doc["state"]
        if not isinstance(state, dict) or state.get("kind") not in KINDS:
            raise ValueError("invalid checkpoint state")
        kind = state["kind"]
        common = {"kind", "threshold"}
        fields = {
            "A": common | {"center", "count"}, "B": common | {"total", "count"},
            "C": common | {"center", "remainder", "count"},
            "D": common | {"qcenter", "count"}, "E": common | {"window"},
            "F": common | {"qcenter"},
        }[kind]
        if set(state) != fields or any(type(v) is not int for k, v in state.items() if k != "kind"):
            if kind != "E" or set(state) != fields or type(state.get("threshold")) is not int or not isinstance(state.get("window"), list):
                raise ValueError("invalid checkpoint fields")
        threshold = state["threshold"]
        if threshold < 0:
            raise ValueError("invalid threshold")
        if kind == "E":
            values = state["window"]
            if len(values) != 8 or any(type(v) is not int or not INPUT_MIN <= v <= INPUT_MAX for v in values):
                raise ValueError("invalid rolling window")
            model = cls(kind, values, threshold)
            model.window = deque(values, maxlen=8)
            return model
        count = state.get("count", 1)
        if type(count) is not int or count < 1:
            raise ValueError("invalid count")
        if kind in ("A", "B", "C", "D") and count > MAX_COUNT:
            raise ValueError("count exceeds declared cumulative bound")
        model = cls(kind, [0] * 8, threshold)
        model.count = count
        if kind == "A":
            model.center = state["center"]
            if not INPUT_MIN <= model.center <= INPUT_MAX:
                raise ValueError("center outside declared domain")
        elif kind == "B":
            model.total = state["total"]
            if not INPUT_MIN * count <= model.total <= INPUT_MAX * count:
                raise ValueError("sum outside declared domain")
        elif kind == "C":
            model.center = state["center"]
            model.remainder = state["remainder"]
            represented = model.center * count + model.remainder
            if (not 0 <= model.remainder < count or not INPUT_MIN <= model.center <= INPUT_MAX
                    or not INPUT_MIN * count <= represented <= INPUT_MAX * count):
                raise ValueError("invalid center/remainder state")
        else:
            model.qcenter = state["qcenter"]
            if not INPUT_MIN * SCALE <= model.qcenter <= INPUT_MAX * SCALE:
                raise ValueError("fixed-point center outside declared domain")
        return model


def make_models(training: list[int], threshold: int = THRESHOLD) -> dict[str, ArithmeticModel]:
    return {kind: ArithmeticModel(kind, training, threshold) for kind in KINDS}
