"""Private B01-B07 injections; never public arithmetic limit overrides."""
from .accounting import Fault, Ledger, guarded
from .expansion import enter_iteration


def capture(ledger, action, destination=(17, -19, 23)):
    try:
        action()
        status = 'OK'
    except Fault as error:
        status = error.status
    return dict(status=status, attempted=ledger.attempted, admitted=ledger.admitted,
                destination=destination, events=ledger.events)


def observations():
    rows = {}
    evaluated = []
    ledger = Ledger(attempted=99_999, admitted=99_999)
    rows['B01'] = capture(ledger, lambda: ledger.check('test', lambda: evaluated.append(1) or True,
                                                     'RESOURCE_LIMIT'))
    rows['B01']['evaluations'] = len(evaluated)
    evaluated = []
    ledger = Ledger(attempted=100_000, admitted=100_000)
    rows['B02'] = capture(ledger, lambda: ledger.check('test', lambda: evaluated.append(1) or True,
                                                     'RESOURCE_LIMIT'))
    rows['B02']['evaluations'] = len(evaluated)
    ledger = Ledger()
    rows['B03'] = capture(ledger, lambda: guarded('MUL', (1 << 100, 0), ledger, (1 << 100, 0)))
    ledger = Ledger(attempted=99_999, admitted=99_999)
    rows['B04'] = capture(ledger, lambda: guarded('MUL', (1 << 100, 0), ledger, (1 << 100, 0)))
    ledger = Ledger(expansion=True)
    rows['B05'] = capture(ledger, lambda: enter_iteration(ledger, 128))
    ledger = Ledger(expansion=True, attempted=100_000, admitted=100_000)
    rows['B06'] = capture(ledger, lambda: ledger.charge('SURD_MUL'))
    ledger = Ledger(expansion=True)
    rows['B07'] = capture(ledger, lambda: guarded('ADD', (1 << 128, 0), ledger, (-(1 << 128), 0)))
    return rows


EXPECTED = {
    'B01': ('OK',100_000,100_000),
    'B02': ('RESOURCE_LIMIT',100_001,100_000),
    'B03': ('RESOURCE_LIMIT',2,2),
    'B04': ('RESOURCE_LIMIT',100_001,100_000),
    'B05': ('EXPANSION_RESOURCE_LIMIT',1,1),
    'B06': ('EXPANSION_RESOURCE_LIMIT',100_001,100_000),
    'B07': ('EXPANSION_RESOURCE_LIMIT',2,2),
}


def check(rows):
    if set(rows) != set(EXPECTED):
        raise AssertionError('Boundary inventory mismatch')
    for name, expected in EXPECTED.items():
        row = rows[name]
        if (row['status'],row['attempted'],row['admitted']) != expected:
            raise AssertionError((name,row))
        if row['destination'] != (17,-19,23):
            raise AssertionError('Boundary destination changed')
    if rows['B01']['evaluations'] != 1 or rows['B02']['evaluations'] != 0:
        raise AssertionError('Budget boundary predicate evaluations')
