"""Checked software AOR tuples. Unqualified research; no VM or RTL integration."""
from dataclasses import dataclass
from .accounting import Fault, Ledger, fits, guarded, temporary_bound
from .expansion import expand

OPS = frozenset(('STEP', 'MUL', 'ADD', 'SUB', 'CONJ', 'NORM', 'EXPAND'))


def valid_tuple(value):
    return (type(value) is tuple and len(value) == 3
            and all(type(x) is int for x in value)
            and fits(value[0], 64) and fits(value[1], 64) and fits(value[2], 32))


@dataclass(frozen=True)
class Result:
    status: str
    value: object
    attempted: int
    admitted: int
    committed: bool
    events: tuple


def validate(operation, left, right, increment, destination):
    if type(operation) is not str:
        raise Fault('INVALID_INPUT')
    if not valid_tuple(left) or (right is not None and not valid_tuple(right)):
        raise Fault('INVALID_INPUT')
    if increment is not None and (type(increment) is not int or not fits(increment, 32)):
        raise Fault('INVALID_INPUT')
    if operation == 'NORM':
        if type(destination) is not int or not fits(destination, 128):
            raise Fault('INVALID_INPUT')
    elif not valid_tuple(destination):
        raise Fault('INVALID_INPUT')
    if type(operation) is not str or operation not in OPS:
        raise Fault('UNSUPPORTED_OPERATION')
    if (operation in ('MUL', 'ADD', 'SUB')) != (right is not None):
        raise Fault('INVALID_INPUT')
    if (operation == 'STEP') != (increment is not None):
        raise Fault('INVALID_INPUT')


def perform(operation, left, right, increment, ledger):
    a, b, k = left
    if operation == 'EXPAND':
        return expand(left, ledger)
    if operation == 'STEP':
        if a == b == 0:
            return 0, 0, 0
        ledger.check('exponent-range', lambda: fits(k + increment, 32), 'EXPONENT_OVERFLOW')
        return a, b, k + increment
    if operation == 'CONJ':
        ledger.charge('SURD_CONJ')
        if not fits(-k, 32):
            raise Fault('EXPONENT_OVERFLOW')
        ledger.check('temporary-safety', lambda: temporary_bound('CONJ', (a, b)) <= 129,
                     ledger.resource())
        if not fits(-b, 64):
            raise Fault('MANTISSA_OVERFLOW')
        return (a, -b, -k) if a or b else (0, 0, 0)
    if operation == 'NORM':
        result = guarded('NORM', (a, b), ledger)
        ledger.check('norm-output-range', lambda: fits(result, 128), 'NORM_OVERFLOW')
        return result
    if operation == 'MUL':
        ledger.check('exponent-range', lambda: fits(k + right[2], 32), 'EXPONENT_OVERFLOW')
        exponent = k + right[2]
    else:
        ledger.check('equal-exponent', lambda: k == right[2], 'UNSUPPORTED_OPERATION')
        exponent = k
    result = guarded(operation, (a, b), ledger, right[:2])
    ledger.check('coefficient-range', lambda: all(fits(x, 64) for x in result),
                 'MANTISSA_OVERFLOW')
    return (*result, exponent) if any(result) else (0, 0, 0)


def execute(operation, left, right=None, *, increment=None, destination=None):
    """Immutable result; caller may commit only when committed is true."""
    if type(operation) is not str:
        return Result('INVALID_INPUT', destination if destination is not None else (17, -19, 23),
                      0, 0, False, ())
    if destination is None:
        destination = 17 if operation == 'NORM' else (17, -19, 23)
    ledger = Ledger(expansion=operation == 'EXPAND')
    try:
        validate(operation, left, right, increment, destination)
        value = perform(operation, left, right, increment, ledger)
        return Result('OK', value, ledger.attempted, ledger.admitted, True, tuple(ledger.events))
    except Fault as error:
        return Result(error.status, destination, ledger.attempted, ledger.admitted,
                      False, tuple(ledger.events))
