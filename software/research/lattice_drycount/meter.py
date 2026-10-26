"""Explicit host-model primitive schedule and simultaneous live-slot ledger."""
from collections import Counter, defaultdict
from contextlib import contextmanager
from ..lattice_comparison.limits import Refusal, Profile


class Meter:
    def __init__(self, trace=False):
        self.profile = Profile()
        self.counts, self.stages = Counter(), defaultdict(Counter)
        self.stage, self.live, self.serial = 'admission', {}, 0
        self.peak, self.raw_bits, self.normal_bits = 0, 0, 0
        self.events = [] if trace else None

    def record(self, event):
        if self.events is not None:
            self.events.append(event)

    def charge(self, name, count=1):
        assert type(count) is int and count >= 0
        self.counts[name] += count
        self.stages[self.stage][name] += count
        self.record(('charge', self.stage, name, count))

    def test(self, condition, reason, name='equality_compare'):
        self.charge(name)
        if not condition:
            raise Refusal(reason)

    def scalar(self, value, committed=False):
        self.test(type(value) is int, 'INTEGER_TYPE', 'type_check')
        width = self.profile.scalar_bits if committed else self.profile.temporary_bits
        self.charge('range_compare', 2)
        self.record(('range', value, width))
        if not -(1 << (width-1)) <= value < 1 << (width-1):
            raise Refusal('SCALAR_RANGE' if committed else 'TEMPORARY_RANGE')
        bits = (value if value >= 0 else ~value).bit_length()+1
        self.raw_bits = max(self.raw_bits, bits)
        if committed:
            self.normal_bits = max(self.normal_bits, bits)
        return value

    def op(self, name, a, b=None):
        self.scalar(a)
        if b is not None:
            self.scalar(b)
        self.charge('indexed_read', 1 if b is None else 2)
        self.charge(name)
        if name == 'add': value = a+b
        elif name == 'subtract': value = a-b
        elif name == 'multiply': value = a*b
        elif name == 'remainder': value = a % b
        elif name == 'quotient': value = a // b
        elif name == 'absolute': value = abs(a)
        elif name == 'negate': value = -a
        elif name == 'xor': value = a ^ b
        elif name == 'and': value = a & b
        elif name == 'or': value = a | b
        elif name == 'shift_left': value = a << b
        elif name == 'shift_right': value = a >> b
        else: raise Refusal('OPERATION_INVALID')
        self.record(('scalar', name, a, b, value))
        self.charge('indexed_write')
        return self.scalar(value)

    def constant(self, value):
        self.charge('move')
        return value

    def read(self, row, index):
        self.charge('indexed_read')
        return row[index]

    def write(self, row, index, value):
        self.charge('indexed_write')
        row[index] = value

    def allocate(self, name, size):
        self.test(name not in self.live, 'DUPLICATE_ALLOCATION')
        self.test(type(size) is int and size >= 0, 'STORAGE_SIZE', 'range_compare')
        self.charge('allocate')
        self.live[name] = size
        self.record(('allocate', name, size))
        self.peak = max(self.peak, sum(self.live.values()))

    def release(self, name):
        self.test(name in self.live, 'MISSING_ALLOCATION')
        self.charge('release')
        self.record(('release', name))
        del self.live[name]

    @contextmanager
    def frame(self, temporaries=8, controls=4):
        name = 'frame/'+str(self.serial)
        self.serial += 1
        self.allocate(name, 32+256*temporaries+32*controls)
        try:
            yield
        finally:
            self.release(name)

    def loop(self, count):
        with self.frame(0, 1):
            self.charge('move')
            for i in range(count):
                self.charge('loop_condition')
                yield i
                self.charge('loop_increment')
            self.charge('loop_condition')

    def report(self):
        return dict(work=sum(self.counts.values()), counts=dict(self.counts),
                    stages={k: dict(v) for k, v in self.stages.items()},
                    simultaneous_live_bits=self.peak, retained_live_bits=sum(self.live.values()),
                    raw_integer_bits=self.raw_bits, normalized_integer_bits=self.normal_bits)
