"""Ratified bounded expansion schedule; internal guard harness is not public API."""
from .accounting import Fault, fits, guarded


def enter_iteration(ledger, entered):
    ledger.check('iteration-limit', lambda: entered < 128, 'EXPANSION_RESOURCE_LIMIT')


def expand(value, ledger):
    a, b, k = value
    if a == b == 0:
        return 0, 0, 0
    if k == 0:
        ledger.check('final-output-range', lambda: fits(a, 64) and fits(b, 64),
                     'EXPANSION_OVERFLOW')
        return a, b, 0
    result, power, remaining = (1, 0), (2, 1 if k > 0 else -1), abs(k)
    entered = 0
    while remaining:
        enter_iteration(ledger, entered)
        entered += 1
        if remaining & 1:
            result = guarded('MUL', result, ledger, power)
        remaining >>= 1
        if remaining:
            power = guarded('MUL', power, ledger, power)
    result = guarded('MUL', (a, b), ledger, result)
    ledger.check('final-output-range', lambda: all(fits(x, 64) for x in result),
                 'EXPANSION_OVERFLOW')
    return *result, 0
