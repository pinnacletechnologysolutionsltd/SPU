"""Independent integer-polynomial oracle with recurrence-based expansion.

No bounded arithmetic imports. Exact mathematics has its own operation ledger;
resource refusal does not establish that a bounded answer is numerically wrong.
"""
from dataclasses import dataclass, field


class OracleLimit(Exception):
    pass


@dataclass
class Mathematics:
    attempted: int = 0
    admitted: int = 0
    history: list = field(default_factory=list)
    stopped: bool = False

    def charge(self, name):
        if self.stopped:
            raise RuntimeError('Oracle used after exhaustion')
        self.attempted += 1
        if self.attempted > 100_000:
            self.stopped = True
            raise OracleLimit('Operation budget exhausted')
        self.admitted += 1
        self.history.append(name)

    def guard(self, name, predicate):
        self.charge(name)
        if not predicate():
            self.stopped = True
            raise OracleLimit(name)

    def pair(self, operation, x, y=None):
        self.charge(operation)
        sizes = [abs(v).bit_length() for v in x + (() if y is None else y)]
        bound = 2 * max(sizes, default=0) + 4
        if operation in ('SURD_ADD', 'SURD_SUB', 'PELL_STEP'):
            bound = max(sizes, default=0) + 4
        self.guard('temporary-safety', lambda: bound <= 2_000_128)
        if operation == 'SURD_MUL':
            # Polynomial convolution then reduction by t^2=3.
            polynomial = [0, 0, 0]
            for i in range(2):
                for j in range(2):
                    polynomial[i+j] += x[i] * y[j]
            result = polynomial[0] + 3*polynomial[2], polynomial[1]
        elif operation == 'SURD_ADD':
            result = tuple(x[i]+y[i] for i in range(2))
        elif operation == 'SURD_SUB':
            result = tuple(x[i]-y[i] for i in range(2))
        elif operation == 'SURD_CONJ':
            result = x[0], -x[1]
        elif operation == 'SURD_NORM':
            result = (x[0]*x[0] - 3*x[1]*x[1],)
        elif operation == 'PELL_STEP':
            result = 2*x[0]+3*x[1], x[0]+2*x[1]
        else:
            raise ValueError(operation)
        self.guard('retained-size', lambda: all(abs(v).bit_length() <= 1_000_000
                                               for v in result))
        return result

    def evaluate(self, operation, left, right=None, increment=None):
        if type(operation) is not str:
            raise ValueError('Malformed oracle operation')
        for operand in (left,) if right is None else (left, right):
            if (type(operand) is not tuple or len(operand) != 3
                    or any(type(v) is not int for v in operand)):
                raise ValueError('Malformed oracle operand')
            if any(abs(v).bit_length() > 1_000_000 for v in operand[:2]):
                raise OracleLimit('Input retained-size ceiling')
            if not -(1 << 31) <= operand[2] < (1 << 31):
                raise ValueError('Input exponent domain')
        if operation not in ('STEP', 'MUL', 'ADD', 'SUB', 'CONJ', 'NORM', 'EXPAND'):
            raise ValueError('Unsupported oracle operation')
        if (operation in ('MUL', 'ADD', 'SUB')) != (right is not None):
            raise ValueError('Wrong oracle operand count')
        if operation == 'STEP':
            if type(increment) is not int or not -(1 << 31) <= increment < (1 << 31):
                raise ValueError('Invalid increment')
        elif increment is not None:
            raise ValueError('Extra increment')
        a, b, k = left
        if operation == 'STEP':
            if a == b == 0:
                return 0, 0, 0
            self.charge('exponent-range')
            return a, b, k + increment
        if operation == 'MUL':
            self.charge('exponent-range')
            result = self.pair('SURD_MUL', (a, b), right[:2])
            exponent = k + right[2]
        elif operation in ('ADD', 'SUB'):
            self.charge('equal-exponent')
            if k != right[2]:
                raise ValueError('Different-exponent alignment unsupported')
            result = self.pair('SURD_' + operation, (a, b), right[:2])
            exponent = k
        elif operation == 'CONJ':
            result = self.pair('SURD_CONJ', (a, b))
            exponent = -k
        elif operation == 'NORM':
            return self.pair('SURD_NORM', (a, b))[0]
        else:
            if a == b == 0:
                return 0, 0, 0
            result = self.pair('SURD_CONJ', (a, b)) if k < 0 else (a, b)
            for _ in range(abs(k)):
                result = self.pair('PELL_STEP', result)
            if k < 0:
                result = self.pair('SURD_CONJ', result)
            exponent = 0
        return (*result, exponent) if any(result) else (0, 0, 0)
