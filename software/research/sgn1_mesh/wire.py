"""Prospective common 119-bit header, padded to 15 big-endian bytes."""
FIELDS = ('kind', 'source', 'sequence', 'payload', 'target', 'sender', 'egress')


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('WIRE_RANGE')
    return value


def validate(packet, port_count):
    if type(port_count) is not int or port_count not in (6, 12):
        raise ValueError('WIRE_PORT_PROFILE')
    kind = integer(packet['kind'], 0, 1)
    integer(packet['source'], 0, 62)
    integer(packet['sequence'], 0, (1 << 32) - 1)
    integer(packet['payload'], -(1 << 63), (1 << 63) - 1)
    if kind == 0:
        integer(packet['target'], 0, 62)
        integer(packet['sender'], 0, 0)
        integer(packet['egress'], 0, 0)
    else:
        if packet['target'] is not None:
            raise ValueError('WIRE_WAVE_TARGET')
        integer(packet['sender'], -1, 62)
        integer(packet['egress'], -1, port_count - 1)
        if (packet['sender'] == -1) != (packet['egress'] == -1):
            raise ValueError('WIRE_ABSENT_PAIR')


def encode(packet, port_count):
    validate(packet, port_count)
    values = (packet['kind'], packet['source'], packet['sequence'], packet['payload'] & ((1 << 64) - 1),
              63 if packet['target'] is None else packet['target'],
              63 if packet['sender'] == -1 else packet['sender'],
              15 if packet['egress'] == -1 else packet['egress'])
    word = 0
    for value, width in zip(values, (1, 6, 32, 64, 6, 6, 4)):
        word = (word << width) | value
    return word.to_bytes(15, 'big')


def decode(raw, port_count):
    if type(raw) is not bytes or len(raw) != 15:
        raise ValueError('WIRE_LENGTH')
    word = int.from_bytes(raw, 'big')
    if word >> 119:
        raise ValueError('WIRE_PADDING')
    payload = (word >> 16) & ((1 << 64) - 1)
    target, sender, egress = (word >> 10) & 63, (word >> 4) & 63, word & 15
    packet = dict(kind=(word >> 118) & 1, source=(word >> 112) & 63,
                  sequence=(word >> 80) & ((1 << 32) - 1),
                  payload=payload - (1 << 64) if payload >> 63 else payload,
                  target=None if target == 63 else target,
                  sender=-1 if sender == 63 else sender, egress=-1 if egress == 15 else egress)
    validate(packet, port_count)
    return packet
