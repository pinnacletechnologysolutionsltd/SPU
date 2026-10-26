"""Contract §§4–5 certified-row checks. Oracle Fraction math is uncounted.

Loading checks identity/shape only. Numerical checks run only on supplied issued
rows, never execute an arm, and never supply values for refused/unissued rows.
"""
from fractions import Fraction as F
import json
from pathlib import Path
from w31_verify import digest, require

REFERENCE_NAME = 'QUINTIC_FIXTURE_VALUES.json'


def load_reference(path, expected_hash):
    path = Path(path)
    require(path.is_file(), 'HOLD: missing certified reference: '+str(path))
    require(digest(path) == expected_hash, 'HOLD: certified reference hash: '+str(path))
    ref = json.loads(path.read_text())
    for curve in ('PH3', 'PH5'):
        require(len(ref['sequential'][curve]) == 17, 'HOLD: missing sequential rows: '+curve)
        require('S' in ref[curve], 'HOLD: missing certified S polynomial: '+curve)
        for row in ref['sequential'][curve]:
            require(all(k in row for k in ('t','S1','S2_add','S3_kappa','S3_arc_increment_to_next')),
                    'HOLD: incomplete certified sequential row: '+curve)
    require(len(ref['cell_B']['rows']) == 16, 'HOLD: missing certified Cell B rows')
    require(all('t' in r and len(r['values']) == 7 for r in ref['cell_B']['rows']),
            'HOLD: incomplete certified Cell B row')
    return ref


def rational(pair):
    require(isinstance(pair, list) and len(pair) == 2 and
            all(type(x) is int for x in pair) and pair[1] > 0, 'invalid rational pair')
    q = F(*pair)
    require([q.numerator, q.denominator] == pair, 'noncanonical rational pair')
    return q


def equal(actual, expected, context):
    require(rational(actual) == expected, 'certified mismatch: '+context)


def polynomial(coefficients, t):
    acc = F(0)
    for pair in reversed(coefficients):
        acc = acc*t + rational(pair)
    return acc


def check_route(route, ref):
    if route.get('preparation_outcome'):
        return
    tape, curve = route['tape'], route['curve']
    certified = ref['cell_B']['rows'] if tape == 'CellB' else ref['sequential'][curve]
    require(len(route['rows']) == len(certified), 'certified row count mismatch')
    for k, (row, expected) in enumerate(zip(route['rows'], certified)):
        context = f'{curve}/{route["arm"]}/{tape}/q{k:02d}'
        equal(row['parameter'], rational(expected['t']), context+'/parameter')
        if tape != 'CellB':
            equal(row['parameter'], F(k,16), context+'/grid')
        if row.get('status') != 'OK':
            continue  # A reference value can never substitute for a missing arm value.
        values = row['values']
        if tape == 'CellB':
            for name, value in zip(('x','y','dx','dy','s_signed','s_nonneg','S_inc'), expected['values']):
                equal(values[name], rational(value), context+'/'+name)
            require(values['ok'] is True, 'certified mismatch: '+context+'/ok')
            continue
        for name, value in zip(('x','y'), expected['S1']):
            equal(values[name], rational(value), context+'/'+name)
        if tape == 'S1':
            continue
        for name, value in zip(('dx','dy','sg','Tx','Ty'), expected['S2_add']):
            equal(values[name], rational(value), context+'/'+name)
        sigma = rational(expected['S2_add'][2])
        require(values['ok'] is (sigma != 0), 'certified mismatch: '+context+'/ok')
        if tape != 'S3':
            continue
        denominator = sigma*sigma
        equal(values['Dk'], denominator, context+'/Dk')
        equal(values['Nk'], rational(expected['S3_kappa'])*denominator, context+'/Nk')
        equal(values['S'], polynomial(ref[curve]['S'], F(k,16)), context+'/S')
        available = k == 16 or route['rows'][k+1].get('status') == 'OK'
        require(row['increment_available'] is available, 'increment availability mismatch: '+context)
        if not available:
            require('increment_to_next' not in values, 'fabricated increment: '+context)
        elif k == 16:
            require(values['increment_to_next'] is None and expected['S3_arc_increment_to_next'] is None,
                    'terminal increment must be null: '+context)
        else:
            equal(values['increment_to_next'], rational(expected['S3_arc_increment_to_next']),
                  context+'/increment_to_next')


def check_certified(table, ref):
    for route in table['routes']:
        check_route(route, ref)
    return True
