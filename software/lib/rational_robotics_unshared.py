"""Explicit opt-in unshared-scale integer kernels for robotics transforms."""
import math
from fractions import Fraction
from . import rational_robotics as reference


def _encode(value):
    denominator = math.lcm(value.p.denominator, value.q.denominator)
    return (value.p.numerator * (denominator // value.p.denominator),
            value.q.numerator * (denominator // value.q.denominator), denominator)


def _width(value):
    return (value.bit_length() if value >= 0 else (~value).bit_length()) + 1


def _observe(trace, role, *values):
    if trace is not None:
        trace[role] = max(trace.get(role, 1), *(_width(value) for value in values))
        if role in ('product', 'accumulator'):
            counts = trace.setdefault('wide_fallback_events', {16: 0, 32: 0, 64: 0})
            for bits in counts:
                counts[bits] += int(any(_width(value) > bits for value in values))


def _add(left, right, trace=None):
    a, b, d = left
    c, e, f = right
    scale = math.lcm(d, f)
    u, v = scale // d, scale // f
    if trace is None:
        return a * u + c * v, b * u + e * v, scale
    _observe(trace, 'product', a*u, c*v, b*u, e*v, scale)
    result = a * u + c * v, b * u + e * v, scale
    _observe(trace, 'accumulator', *result)
    return result


def _neg(value):
    return -value[0], -value[1], value[2]


def _multiply(left, right, trace=None):
    a, b, d = left
    c, e, f = right
    if trace is None:
        return a*c + 3*b*e, a*e + b*c, d*f
    products = a*c, 3*b*e, a*e, b*c, d*f
    result = products[0] + products[1], products[2] + products[3], products[4]
    _observe(trace, 'product', *products)
    _observe(trace, 'accumulator', *result)
    return result


def _rotate(values, joint, trace=None):
    a, b, c, d = values
    f, g, h = joint
    if trace is None:
        return (a,
                _add(_add(_multiply(f, b), _multiply(h, c)), _multiply(g, d)),
                _add(_add(_multiply(g, b), _multiply(f, c)), _multiply(h, d)),
                _add(_add(_multiply(h, b), _multiply(g, c)), _multiply(f, d)))
    return (a,
            _add(_add(_multiply(f, b, trace), _multiply(h, c, trace), trace),
                 _multiply(g, d, trace), trace),
            _add(_add(_multiply(g, b, trace), _multiply(f, c, trace), trace),
                 _multiply(h, d, trace), trace),
            _add(_add(_multiply(h, b, trace), _multiply(g, c, trace), trace),
                 _multiply(f, d, trace), trace))


def _subtract(left, right, trace=None):
    return _add(left, _neg(right), trace)


def _materialize(values):
    return reference.QuadrayQ(*(reference.Q3(Fraction(a, d), Fraction(b, d))
                                for a, b, d in values))


def apply_joint_pair(vector, joint):
    """Return `(forward, recovered)` using independent coefficient scales.

    `recovered` applies the maintained determinant-one adjugate coefficients;
    like the reference API, this does not divide by or validate the determinant.
    """
    source = tuple(_encode(value) for value in vector.components())
    f, g, h = (_encode(value) for value in (joint.f, joint.g, joint.h))
    forward = _rotate(source, (f, g, h))
    inverse = (_subtract(_multiply(f, f), _multiply(g, h)),
               _subtract(_multiply(h, h), _multiply(f, g)),
               _subtract(_multiply(g, g), _multiply(f, h)))
    recovered = _rotate(forward, inverse)
    return _materialize(forward), _materialize(recovered)


def _inverse_joint(joint, trace=None):
    f, g, h = joint
    if trace is None:
        return (_subtract(_multiply(f, f), _multiply(g, h)),
                _subtract(_multiply(h, h), _multiply(f, g)),
                _subtract(_multiply(g, g), _multiply(f, h)))
    return (_subtract(_multiply(f, f, trace), _multiply(g, h, trace), trace),
            _subtract(_multiply(h, h, trace), _multiply(f, g, trace), trace),
            _subtract(_multiply(g, g, trace), _multiply(f, h, trace), trace))


def _run_chain(vector, joints, trace=None):
    state = tuple(_encode(value) for value in vector.components())
    prepared = tuple(tuple(_encode(value) for value in (joint.f, joint.g, joint.h))
                     for joint in joints)
    _observe(trace, 'input', *(part for value in state for part in value),
             *(part for joint in prepared for value in joint for part in value))
    inverses = tuple(_inverse_joint(joint, trace) for joint in prepared)
    forward = state
    steps = []
    for index, joint in enumerate(prepared):
        forward = _rotate(forward, joint, trace)
        widths = tuple(_width(part) for value in forward for part in value)
        _observe(trace, 'state', *(part for value in forward for part in value))
        steps.append({'phase': 'forward', 'joint_index': index,
                      'state_max_signed_bits': max(widths)})
    recovered = forward
    for index in range(len(inverses)-1, -1, -1):
        recovered = _rotate(recovered, inverses[index], trace)
        widths = tuple(_width(part) for value in recovered for part in value)
        _observe(trace, 'state', *(part for value in recovered for part in value))
        steps.append({'phase': 'recovery', 'joint_index': index,
                      'state_max_signed_bits': max(widths)})
    _observe(trace, 'output', *(part for value in (*forward, *recovered) for part in value))
    if trace is not None:
        trace['steps'] = steps
    return _materialize(forward), _materialize(recovered)


def apply_joint_chain(vector, joints):
    """Apply a forward chain and reverse adjugate recovery, materializing once.

    Matches `fk_chain` followed by `inverse_fk_chain`, including the reference
    determinant-one assumption and behavior for singular or non-unit joints.
    """
    return _run_chain(vector, tuple(joints))


def trace_joint_chain(vector, joints):
    """Return chain outputs and signed-width observations; never use for timing."""
    trace = {}
    result = _run_chain(vector, tuple(joints), trace)
    return result, trace
