"""AOR-1 attempted/admitted abstract charges; no wall-clock arithmetic status."""
from dataclasses import dataclass, field


class Fault(Exception):
    def __init__(self, status):
        super().__init__(status)
        self.status = status


def fits(value, width):
    return -(1 << (width - 1)) <= value < (1 << (width - 1))


def bits(value):
    return abs(value).bit_length()


@dataclass
class Ledger:
    expansion: bool = False
    attempted: int = 0
    admitted: int = 0
    events: list = field(default_factory=list)
    stopped: bool = False

    def resource(self):
        return 'EXPANSION_RESOURCE_LIMIT' if self.expansion else 'RESOURCE_LIMIT'

    def charge(self, name):
        if self.stopped:
            raise RuntimeError('Work requested after budget exhaustion')
        self.attempted += 1
        if self.attempted > 100_000:
            self.stopped = True
            self.events.append((name, 'REJECTED_BUDGET'))
            raise Fault(self.resource())
        self.admitted += 1
        self.events.append((name, 'ADMITTED'))

    def check(self, name, predicate, failure):
        self.charge(name)
        if not predicate():
            self.events.append((name, 'FALSE'))
            raise Fault(failure)
        self.events.append((name, 'TRUE'))


def product_bound(x, y):
    return bits(x) + bits(y) if x and y else 0


def sum_bound(x, y):
    return max(x, y) + 1 if x and y else max(x, y)


def temporary_bound(operation, left, right=None):
    a, b = left
    if operation == 'MUL':
        c, e = right
        ac, be = product_bound(a, c), product_bound(b, e)
        ae, bc = product_bound(a, e), product_bound(b, c)
        triple = be + 2 if be else 0
        return max(ac, be, ae, bc, triple, sum_bound(ac, triple), sum_bound(ae, bc))
    if operation in ('ADD', 'SUB'):
        return max(sum_bound(bits(a), bits(right[0])), sum_bound(bits(b), bits(right[1])))
    if operation == 'NORM':
        aa, bb = product_bound(a, a), product_bound(b, b)
        triple = bb + 2 if bb else 0
        return max(aa, bb, triple, sum_bound(aa, triple))
    if operation == 'CONJ':
        return max(bits(a), bits(b))
    raise ValueError('No temporary bound for ' + operation)


def guarded(operation, left, ledger, right=None):
    """Private internal primitive: charge before guard, never calculate rejected work."""
    ledger.charge('SURD_' + operation)
    special = operation in ('MUL', 'NORM') and all(fits(x, 64) for x in left)
    if right is not None:
        special = special and all(fits(x, 64) for x in right)
    ledger.check('temporary-safety',
                 lambda: special or temporary_bound(operation, left, right) <= 129,
                 ledger.resource())
    return calculate(operation, left, right)


def calculate(operation, left, right=None):
    """Arithmetic after admission; private instrumentation point for refusal checks."""
    a, b = left
    if operation == 'MUL':
        c, e = right
        return a*c + 3*b*e, a*e + b*c
    if operation == 'ADD':
        return a + right[0], b + right[1]
    if operation == 'SUB':
        return a - right[0], b - right[1]
    if operation == 'NORM':
        return a*a - 3*b*b
    if operation == 'CONJ':
        return a, -b
    raise ValueError(operation)
