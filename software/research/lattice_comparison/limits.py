"""Proposed host resource profile and atomic D4 result, not CPU overflow semantics."""
from collections import Counter
from dataclasses import dataclass


class Refusal(ValueError):
    pass


@dataclass(frozen=True)
class Profile:
    scalar_bits: int = 64
    temporary_bits: int = 256
    max_tokens: int = 256
    max_operations: int = 2000000
    max_live_bits: int = 1048576

    def __post_init__(self):
        for v in (self.scalar_bits, self.temporary_bits, self.max_tokens,
                  self.max_operations, self.max_live_bits):
            if type(v) is not int or v <= 0:
                raise Refusal('PROFILE_INVALID')


class Meter:
    def __init__(self, profile=Profile()):
        self.profile, self.counts, self.total = profile, Counter(), 0
        self.peak_bits, self.peak_live_bits, self.live = 0, 0, {}

    def charge(self, name, count=1):
        if type(count) is not int or count < 0:
            raise Refusal('COUNT_INVALID')
        if self.total + count > self.profile.max_operations:
            raise Refusal('WORK_LIMIT')
        self.counts[name] += count
        self.total += count

    def integer(self, value, committed=False):
        self.charge('integer_type_check')
        if type(value) is not int:
            raise Refusal('INTEGER_TYPE')
        width = self.profile.scalar_bits if committed else self.profile.temporary_bits
        self.charge('range_compare', 2)
        if not -(1 << (width - 1)) <= value < 1 << (width - 1):
            raise Refusal('SCALAR_RANGE' if committed else 'TEMPORARY_RANGE')
        self.peak_bits = max(self.peak_bits, (value if value >= 0 else ~value).bit_length() + 1)
        return value

    def acquire(self, name, size):
        self.charge('allocate')
        if name in self.live or type(size) is not int or size < 0:
            raise Refusal('STORAGE_INVALID')
        total = sum(self.live.values()) + size
        if total > self.profile.max_live_bits:
            raise Refusal('STORAGE_LIMIT')
        self.live[name] = size
        self.peak_live_bits = max(self.peak_live_bits, total)

    def release(self, name):
        self.charge('release')
        if name not in self.live:
            raise Refusal('STORAGE_INVALID')
        del self.live[name]


def atomic_d4(word, vector, profile=Profile()):
    """Publish a complete tuple only after every output component passes."""
    from .d4 import descriptor, act
    if type(word) not in (tuple, list) or len(word) > profile.max_tokens:
        raise Refusal('WORD_LIMIT')
    if type(vector) not in (tuple, list) or len(vector) != 4:
        raise Refusal('VECTOR_SHAPE')
    meter = Meter(profile)
    for value in vector:
        meter.integer(value, committed=True)
    # A boundary witness, not yet a fully metered signed-permutation comparator.
    result = act(descriptor(word), vector)
    for value in result:
        meter.integer(value, committed=True)
    return result
