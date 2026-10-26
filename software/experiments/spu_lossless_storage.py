"""R1 tagged host coefficient blocks; fixed int64/16-16-32 or R0 codecs."""
from software.experiments import spu_lossless_reduction as r0

MODE_NAMES = {0: "fixed_i64", 1: "fixed_renderer_fields", 2: "packed", 3: "factored"}
FIELD_BYTES = (2, 2, 4)
MAX_BLOCK = 32


def checked(values):
    values = tuple(values)
    if len(values) > MAX_BLOCK or any(type(v) is not int or not r0.MIN_I64 <= v <= r0.MAX_I64 for v in values):
        raise ValueError("expected at most 32 signed int64 values, excluding booleans")
    return values


def encode(values, mode):
    values = checked(values)
    if type(mode) is not int or mode not in MODE_NAMES:
        raise ValueError("unknown mode")
    if mode == 2:
        body = r0.pack(values)
    elif mode == 3:
        body = r0.factor_pack(values)
    else:
        body = bytearray(len(values).to_bytes(4, "little"))
        for i, value in enumerate(values):
            width = 8 if mode == 0 else FIELD_BYTES[i % 3]
            try:
                body.extend(value.to_bytes(width, "little", signed=True))
            except OverflowError as error:
                raise ValueError("coefficient exceeds renderer field width") from error
    return bytes([mode])+body


def decode(stream):
    if not isinstance(stream, bytes) or len(stream) < 5 or stream[0] not in MODE_NAMES:
        raise ValueError("invalid tagged stream")
    mode, body = stream[0], stream[1:]
    offset = 8 if mode == 3 else 0
    if len(body) < offset+4:
        raise ValueError("truncated factor/count")
    count = int.from_bytes(body[offset:offset+4], "little")
    if count > MAX_BLOCK:
        raise ValueError("excessive block count")
    if mode in (0, 1):
        widths = [8 if mode == 0 else FIELD_BYTES[i % 3] for i in range(count)]
        if len(body) != 4+sum(widths):
            raise ValueError("truncated or trailing fixed payload")
        cursor, values = 4, []
        for width in widths:
            values.append(int.from_bytes(body[cursor:cursor+width], "little", signed=True))
            cursor += width
    else:
        values = r0.unpack(body[offset:])
        if mode == 3:
            g = int.from_bytes(body[:8], "little")
            if not g:
                raise ValueError("zero factor")
            values = [g*v for v in values]
            checked(values)
            if r0.factor(values)[0] != g:
                raise ValueError("noncanonical factor")
    return list(checked(values))


def alternatives(values):
    values = checked(values)
    streams = {mode: encode(values, mode) for mode in (0, 2, 3)}
    try:
        streams[1] = encode(values, 1)
    except ValueError:
        pass
    return streams


def select(values):
    streams = alternatives(values)
    mode = min(streams, key=lambda m: (len(streams[m]), m))
    return streams[mode]


def raw_renderer_bytes(values):
    encode(values, 1)  # range validation before reporting the raw-field size
    return sum(FIELD_BYTES[i % 3] for i in range(len(values)))
