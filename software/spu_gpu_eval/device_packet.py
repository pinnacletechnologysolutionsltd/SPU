"""Independent decoder for the frozen T1d device packet."""

from __future__ import annotations

from dataclasses import dataclass


START_BYTE = 0xA5
PACKET_BYTES = 64
RECORD_BITS = 252


@dataclass(frozen=True)
class DeviceTriangle:
    edges: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]
    rgb: tuple[int, int, int]
    z: tuple[int, int, int]


@dataclass(frozen=True)
class DeviceScene:
    triangles: tuple[DeviceTriangle, DeviceTriangle]


def _signed(value: int, width: int) -> int:
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def _take(record: int, offset: int, width: int, signed: bool = False) -> tuple[int, int]:
    value = (record >> offset) & ((1 << width) - 1)
    return (_signed(value, width) if signed else value), offset + width


def _decode_record(record: int) -> DeviceTriangle:
    offset = 0
    edges = []
    for _ in range(3):
        a, offset = _take(record, offset, 16, True)
        b, offset = _take(record, offset, 16, True)
        c, offset = _take(record, offset, 32, True)
        edges.append((a, b, c))
    r, offset = _take(record, offset, 4)
    g, offset = _take(record, offset, 4)
    b, offset = _take(record, offset, 4)
    z0, offset = _take(record, offset, 16)
    z1, offset = _take(record, offset, 16)
    z2, offset = _take(record, offset, 16)
    if offset != RECORD_BITS:
        raise AssertionError("T1d decoder field widths do not total 252 bits")
    return DeviceTriangle(tuple(edges), (r, g, b), (z0, z1, z2))


def decode_packet(packet: bytes) -> DeviceScene:
    if not isinstance(packet, bytes) or len(packet) != PACKET_BYTES:
        raise ValueError("T1d packet must be exactly 64 bytes")
    if packet[0] != START_BYTE:
        raise ValueError("T1d packet must begin with 0xA5")
    payload = int.from_bytes(packet[1:], "little")
    mask = (1 << RECORD_BITS) - 1
    first = _decode_record(payload & mask)
    second = _decode_record((payload >> RECORD_BITS) & mask)
    return DeviceScene((first, second))
