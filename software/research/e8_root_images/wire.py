"""Explicit schema/root/basis identities: 64-bit payload, 76-byte full record."""
from .tables import context
from .descriptor import admit

HEADER = bytes((1,0xE8,8,0))


def encode(images, ctx=None):
    ctx = context() if ctx is None else ctx
    images = admit(images,ctx)
    return HEADER+bytes.fromhex(ctx.root_hash)+bytes.fromhex(ctx.basis_hash)+bytes(images)


def decode(packet, ctx=None):
    ctx = context() if ctx is None else ctx
    if type(packet) is not bytes or len(packet) != 76:
        raise ValueError('WIRE_LENGTH')
    if packet[:4] != HEADER:
        raise ValueError('WIRE_SCHEMA')
    if packet[4:36] != bytes.fromhex(ctx.root_hash):
        raise ValueError('WIRE_ROOT_IDENTITY')
    if packet[36:68] != bytes.fromhex(ctx.basis_hash):
        raise ValueError('WIRE_BASIS_IDENTITY')
    return admit(tuple(packet[68:]),ctx)
