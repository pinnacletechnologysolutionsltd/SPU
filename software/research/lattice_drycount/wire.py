"""Version1 little-endian wire schema; independent structural/canonical decoder."""
from math import gcd
from ..lattice_comparison.d4 import pack as d4_pack, unpack as d4_unpack

KINDS = {'vector': 1, 'rational': 2, 'matrix': 3, 'word': 4, 'signed': 5, 'surd': 6}


def encode(kind, system, values):
    tag = KINDS[kind]
    header = bytes((1, tag, {'D4': 4, 'E8': 8}[system], 0))
    if kind == 'signed':
        assert system == 'D4'
        return header+d4_pack(values).to_bytes(2, 'little')
    count = len(values)**2 if kind == 'matrix' else len(values)
    header += count.to_bytes(4, 'little')
    if kind == 'matrix':
        header += len(values).to_bytes(4, 'little')*2
        source = (v for row in values for v in row)
    else:
        source = iter(values)
    if kind == 'word':
        width = 2 if system == 'D4' else 3
        tokens = list(source)
        assert all(type(v) is int and 0 <= v < (4 if width == 2 else 8) for v in tokens)
        payload = sum(v << (i*width) for i, v in enumerate(tokens))
        return header+payload.to_bytes((count*width+7)//8, 'little')
    body = bytearray()
    for value in source:
        row = (value,) if kind == 'vector' else value
        for scalar in row:
            body.extend(scalar.to_bytes(8, 'little', signed=True))
    return header+body


def decode(data):
    def require(ok, reason):
        if not ok:
            raise ValueError(reason)
    require(type(data) is bytes and len(data) >= 4, 'WIRE_HEADER')
    version, kind, n, flags = data[:4]
    require(version == 1 and kind in KINDS.values() and n in (4, 8) and flags == 0, 'WIRE_TAG')
    if kind == KINDS['signed']:
        require(n == 4 and len(data) == 6, 'WIRE_LENGTH')
        require(data[5] < 16, 'WIRE_PADDING')
        return d4_unpack(int.from_bytes(data[4:], 'little'))
    require(len(data) >= 8, 'WIRE_LENGTH')
    count = int.from_bytes(data[4:8], 'little')
    offset = 8
    if kind == KINDS['matrix']:
        require(len(data) >= 16, 'WIRE_LENGTH')
        rows, cols = int.from_bytes(data[8:12], 'little'), int.from_bytes(data[12:16], 'little')
        require(rows == cols == n and count == n*n, 'WIRE_SHAPE')
        offset = 16
    elif kind == KINDS['word']:
        require(count <= 256, 'WIRE_WORD_LIMIT')
    else:
        require(count == n, 'WIRE_SHAPE')
    if kind == KINDS['word']:
        width = 2 if n == 4 else 3
        require(len(data) == 8+(count*width+7)//8, 'WIRE_LENGTH')
        payload = int.from_bytes(data[8:], 'little')
        require(payload >> (count*width) == 0, 'WIRE_PADDING')
        return tuple((payload >> (i*width)) & ((1 << width)-1) for i in range(count))
    fields = 1 if kind == KINDS['vector'] else 3 if kind == KINDS['surd'] else 2
    require(len(data) == offset+count*fields*8, 'WIRE_LENGTH')
    result = []
    for i in range(count):
        row = tuple(int.from_bytes(data[offset+8*(i*fields+j):offset+8*(i*fields+j+1)],
                                   'little', signed=True) for j in range(fields))
        if fields > 1:
            require(row[-1] > 0, 'WIRE_DENOMINATOR')
            common = abs(row[0])
            for value in row[1:]:
                common = gcd(common, abs(value))
            require(common == 1, 'WIRE_CANONICAL')
        result.append(row[0] if fields == 1 else row)
    if kind == KINDS['matrix']:
        return tuple(tuple(result[i*n:(i+1)*n]) for i in range(n))
    return tuple(result)


def measure(m, kind, system, values, name):
    from .wirecost import measure as counted
    return counted(m, kind, system, values, name)
