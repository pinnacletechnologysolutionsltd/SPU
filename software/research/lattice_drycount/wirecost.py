"""Actual byte packing/unpacking primitive schedule; separate from wire oracle."""
from .exact import gcd
from .wire import encode, decode, KINDS


def field(m, value, byte_count, target, signed=False):
    emitted = []
    for i in m.loop(byte_count):
        shift = m.op('multiply', i, m.constant(8))
        byte = m.op('and', m.op('shift_right', value, shift), m.constant(255))
        m.charge('indexed_write')
        target.append(byte)
        emitted.append(byte)
    parsed = m.constant(0)
    for i in m.loop(byte_count):
        parsed = m.op('or', parsed, m.op('shift_left', m.read(emitted, i),
                                       m.op('multiply', i, m.constant(8))))
    if signed:
        m.charge('sign_compare')
        if parsed >= 1 << (byte_count*8-1):
            parsed = m.op('subtract', parsed, m.constant(1 << (byte_count*8)))
    m.test(parsed == value, 'WIRE_ROUNDTRIP')


def measure(m, kind, system, values, name):
    expected = encode(kind, system, values)
    decode(expected)  # independent observer, never a source of reported counters
    m.allocate(name, 64+8*len(expected))
    body = []
    with m.frame(16, 8):
        for v in (1, KINDS[kind], 4 if system == 'D4' else 8, 0):
            m.charge('loop_condition'); field(m, m.constant(v), 1, body)
            m.charge('loop_increment')
        m.charge('loop_condition')
        if kind == 'signed':
            p, b = values
            packed = m.constant(0)
            for i in m.loop(4):
                packed = m.op('or', packed, m.op('shift_left', m.read(p, i), m.op('multiply', i, 2)))
                packed = m.op('or', packed, m.op('shift_left', m.read(b, i), m.op('add', i, 8)))
            field(m, packed, 2, body)
            m.test(m.op('shift_right', packed, 12) == 0, 'WIRE_PADDING', 'zero_compare')
            for i in m.loop(4):
                m.test(m.read(b, i) in (0, 1), 'WIRE_SIGN', 'range_compare')
                for j in m.loop(i):
                    m.test(m.read(p, i) != m.read(p, j), 'WIRE_PERMUTATION')
            parity = m.constant(0)
            for i in m.loop(4):
                parity = m.op('add', parity, m.read(b, i))
            m.test(m.op('remainder', parity, 2) == 0, 'WIRE_SIGN_PARITY')
        else:
            count = len(values)**2 if kind == 'matrix' else len(values)
            field(m, m.constant(count), 4, body)
            if kind == 'matrix':
                field(m, m.constant(len(values)), 4, body)
                field(m, m.constant(len(values)), 4, body)
            if kind == 'word':
                width = 2 if system == 'D4' else 3
                buffer = m.constant(0)
                for i in m.loop(len(values)):
                    token = m.read(values, i)
                    m.test(0 <= token < 1 << width, 'WIRE_TOKEN', 'range_compare')
                    shift = m.op('remainder', m.op('multiply', i, width), 8)
                    buffer = m.op('or', buffer, m.op('shift_left', token, shift))
                    position = m.op('multiply', i, width)
                    end = m.op('add', position, width)
                    m.charge('shape_compare')
                    if m.op('quotient', end, 8) != m.op('quotient', position, 8):
                        body.append(m.op('and', buffer, 255)); m.charge('indexed_write')
                        buffer = m.op('shift_right', buffer, 8)
                remainder = m.op('remainder', m.op('multiply', len(values), width), 8)
                m.charge('shape_compare')
                if remainder:
                    body.append(buffer); m.charge('indexed_write')
                m.test(buffer < 256, 'WIRE_PADDING', 'range_compare')
                # Decode each emitted token with a bounded two-byte window.
                for i in m.loop(len(values)):
                    position = m.op('multiply', i, width)
                    start, shift = m.op('quotient', position, 8), m.op('remainder', position, 8)
                    x = m.read(body, m.op('add', 8, start))
                    m.charge('shape_compare')
                    if m.op('add', shift, width) > 8:
                        x = m.op('or', x, m.op('shift_left', m.read(body, m.op('add', 9, start)), 8))
                    token = m.op('and', m.op('shift_right', x, shift), (1 << width)-1)
                    m.test(token == m.read(values, i), 'WIRE_TOKEN_ROUNDTRIP')
            else:
                source = [v for row in values for v in row] if kind == 'matrix' else values
                if kind == 'matrix':
                    m.allocate(name+'/view', 64+len(source)*32)
                fields = 1 if kind == 'vector' else 3 if kind == 'surd' else 2
                for i in m.loop(len(source)):
                    value = m.read(source, i)
                    row = (value,) if fields == 1 else value
                    for j in m.loop(fields):
                        field(m, m.scalar(m.read(row, j), committed=True), 8, body, True)
                    if fields > 1:
                        m.test(row[-1] > 0, 'WIRE_DENOMINATOR', 'sign_compare')
                        common = m.read(row, 0)
                        for j in m.loop(fields-1):
                            common = gcd(m, common, m.read(row, j+1))
                        m.test(common == 1, 'WIRE_CANONICAL')
                if kind == 'matrix':
                    m.release(name+'/view')
        m.charge('type_check')
        m.charge('shape_compare')
        m.test(bytes(body) == expected, 'WIRE_BYTES')
    return expected
