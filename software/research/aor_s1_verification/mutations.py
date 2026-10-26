"""Isolated changed observations; no fault flags enter clean checker predicates."""
from contextlib import ExitStack
from copy import deepcopy
from importlib import import_module
from unittest.mock import patch


def candidate(control, clean, observe):
    name = control['id']
    if name == 'DROPPED_3BD':
        arithmetic = import_module('software.research.aor_s1.arithmetic')
        execute_module = import_module('software.research.aor_s1.execute')
        original = arithmetic.products

        def dropped(a, b, c, d, meter):
            ac = meter.scalar('product.ac', lambda: a * c, kind='mul')
            bd = meter.scalar('product.bd', lambda: b * d, kind='mul')
            meter.scalar('product.3bd', lambda: 3 * bd, kind='mul')
            first = meter.scalar('product.first', lambda: ac + 0)
            ad = meter.scalar('product.ad', lambda: a * d, kind='mul')
            bc = meter.scalar('product.bc', lambda: b * c, kind='mul')
            second = meter.scalar('product.second', lambda: ad + bc)
            return first, second

        with ExitStack() as stack:
            stack.enter_context(patch.object(arithmetic, 'products', dropped))
            if getattr(execute_module, 'products', None) is original:
                stack.enter_context(patch.object(execute_module, 'products', dropped))
            return observe()
    changed = deepcopy(clean)
    if name == 'WRONG_UPPER_ENDPOINT':
        changed['balanced'] = True
    elif name == 'WRONG_LOWER_ENDPOINT':
        changed['balanced'] = False
    elif name == 'LOST_VALUE_SIGN':
        changed['embedding_sign'] = 1
    elif name == 'WRONG_EXPONENT_SIGN':
        changed['result'][2] = 1
        changed['destination'][2] = 1
    elif name == 'WRONG_EQUALITY':
        changed['result'] = False
    elif name == 'WRONG_CHARGE':
        changed['charged_units'] -= 1
    elif name == 'EARLY_COMMIT':
        changed['post_state']['R0'] = [1, 0, 1]
        changed['outcome']['destination'] = [1, 0, 1]
    elif name == 'EXTRA_LOCAL_ADJUSTMENT':
        changed['adjustments'] = 2
    elif name == 'WRONG_NORM_STATUS':
        exact = next(e['value'] for e in clean['events'] if e['action'] == 'norm.publication')
        narrowed = ((exact + (1 << 127)) & ((1 << 128) - 1)) - (1 << 127)
        changed['status'], changed['result'] = 'OK', narrowed
    elif name == 'UNCHARGED_TERMINAL_SCAN':
        changed['events'] = changed['events'][:-2]
        changed['charged_units'] -= 2
    else:
        raise ValueError('Unknown candidate control: ' + name)
    return changed


def oracle(control, clean):
    changed = deepcopy(clean)
    name = control['id']
    if name == 'ORACLE_BAD_SIGN':
        changed['result'] = 1
    elif name == 'ORACLE_BAD_EQUALITY':
        changed['result'] = True
    elif name == 'ORACLE_BAD_NORM':
        changed['result'] = 12
    elif name == 'ORACLE_BAD_PRODUCT':
        changed['expanded_value'] = [4, 9]
    else:
        raise ValueError('Unknown oracle control: ' + name)
    return changed


def checker_meta(labels, required):
    """Actually replace a checker result, then evaluate the outer named obligation."""
    broken = set(labels) - {required}
    outer = set()
    if required not in broken:
        outer.add('META_REJECT_CHECKER_MISSED_REQUIRED_LABEL')
    return broken, outer
