"""General/certified-local normalization with the ratified checked 1*a."""
from .budget import InvariantError, Refusal
from .comparator import boundary


def normalize(state, meter, allowance=64, local=False):
    """Normalize a private nonzero mantissa, reading original a,b per step.

    Public zero operands take explicit dispatch paths before this function.
    General inputs use at most64 completed adjustments; local inputs use one.
    The local bound assumes canonical operands and the reviewed ratio proof.
    A requested second local adjustment is a defect, never ordinary refusal.
    Every loop first charges lower comparison, then upper only when needed.
    Allowance exhaustion still permits a final successful two-action Scan.
    Requesting another adjustment after exhaustion fails before its arithmetic.
    Exponent adjustment and signed32 check precede coefficient calculations.
    Each coefficient action and width check consumes its own logical unit.
    The checked 1*a action is a declared accounting convention.
    Its two units do not assert mathematical necessity or hardware cost.
    The two coefficient results stay private until all seven steps complete.
    The caller performs final storage checks and atomic tuple publication.
    A refused partial adjustment never increments the completed-step counter.
    Primitive kernel counters remain distinct from these logical charges.
    """
    a, b, k = state
    while True:
        lo = meter.action('scan.lower',
                          lambda: boundary(a, b, counters=meter.primitive_counts))
        direction = 1 if lo < 0 else 0
        if not direction:
            hi = meter.action('scan.upper',
                              lambda: boundary(a, b, True, meter.primitive_counts))
            if hi < 0:
                return a, b, k
            direction = -1
        if meter.adjustments == allowance:
            if local:
                raise InvariantError('second certified local adjustment requested')
            raise Refusal('WORK_LIMIT')
        exponent = meter.exponent('adjust.exponent', lambda: k - direction)
        twice_a = meter.scalar('adjust.2a', lambda: 2*a, kind='mul')
        triple_b = meter.scalar('adjust.3b', lambda: 3*b, kind='mul')
        first = meter.scalar('adjust.first',
                             lambda: twice_a + triple_b if direction == 1 else twice_a - triple_b)
        identity = meter.scalar('adjust.1a', lambda: 1*a, kind='mul')
        twice_b = meter.scalar('adjust.2b', lambda: 2*b, kind='mul')
        second = meter.scalar('adjust.second',
                              lambda: identity + twice_b if direction == 1 else twice_b - identity)
        a, b, k = first, second, exponent
        meter.adjustments += 1
