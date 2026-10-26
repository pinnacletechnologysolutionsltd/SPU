"""Independent scalar replay and storage reconstruction; no candidate meter imports."""
from collections import Counter, defaultdict
import operator

OPS = dict(add=operator.add, subtract=operator.sub, multiply=operator.mul,
           remainder=operator.mod, quotient=operator.floordiv, xor=operator.xor,
           and_=operator.and_, or_=operator.or_, shift_left=operator.lshift,
           shift_right=operator.rshift, absolute=abs, negate=operator.neg)
OPS['and'], OPS['or'] = OPS.pop('and_'), OPS.pop('or_')


def replay(events, report):
    counts, stages, live = Counter(), defaultdict(Counter), {}
    peak, scalars = 0, 0
    for event in events:
        kind = event[0]
        if kind == 'charge':
            _, phase, name, n = event
            assert type(n) is int and n >= 0, 'LEDGER_COUNT'
            counts[name] += n
            stages[phase][name] += n
        elif kind == 'scalar':
            _, name, a, b, result = event
            assert type(a) is int and (b is None or type(b) is int), 'LEDGER_TYPE'
            expected = OPS[name](a) if b is None else OPS[name](a, b)
            assert result == expected, 'LEDGER_SCALAR'
            scalars += 1
        elif kind == 'range':
            _, value, width = event
            assert -(2**(width-1)) <= value < 2**(width-1), 'LEDGER_RANGE'
        elif kind == 'allocate':
            _, name, size = event
            assert name not in live and type(size) is int and size >= 0, 'LEDGER_ALLOCATE'
            live[name] = size
            peak = max(peak, sum(live.values()))
        elif kind == 'release':
            assert event[1] in live, 'LEDGER_RELEASE'
            del live[event[1]]
        else:
            raise AssertionError('LEDGER_EVENT')
    assert dict(counts) == report['counts'], 'LEDGER_COUNTS'
    assert sum(counts.values()) == report['work'], 'LEDGER_WORK'
    assert {k: dict(v) for k, v in stages.items()} == report['stages'], 'LEDGER_STAGES'
    assert peak == report['simultaneous_live_bits'], 'LEDGER_PEAK'
    assert sum(live.values()) == report['retained_live_bits'], 'LEDGER_RETAINED'
    assert scalars == sum(counts[k] for k in OPS), 'LEDGER_SCALAR_COUNT'
    return dict(status='REPLAY_PASS', primitive_units=sum(counts.values()), peak_live_bits=peak)
