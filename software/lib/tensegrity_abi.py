"""Versioned binary table/status ABI for the tensegrity balancer.

This is deliberately a host/sidecar ABI, not an SPU instruction encoding.
It supplies one exact byte representation for the Python oracle, future RTL
BRAM initialisation, and a future southbridge transport command.
"""

from __future__ import annotations

import struct
import zlib

from .tensegrity_balancer import (
    Edge,
    EdgeType,
    Fraction,
    GridState,
    Phi,
    TensegrityFault,
    TensegrityState,
    TensegritySystem,
    Vec3Phi,
)


MAGIC = b"TGR1"
VERSION = 1
HEADER = struct.Struct(">4sBBBBI")
NODE = struct.Struct(">iiiiiiB3x")
EDGE = struct.Struct(">BBBB")
STATUS = struct.Struct(">BBBBI")
LOAD_PREFIX = struct.Struct(">HI")
TRANSPORT_DIAG = struct.Struct(">BBBBHH")

CMD_TGR_LOAD = 0xB2
CMD_TGR_STATUS = 0xB3


class TensegrityAbiError(ValueError):
    """The table/status record cannot be represented or is corrupt."""


def crc8_ccitt(data: bytes) -> int:
    """CRC-8-CCITT used by the Sovereign SPI write envelope (poly 0x07)."""

    crc = 0
    for value in data:
        for bit in range(8):
            feedback = ((crc >> 7) & 1) ^ ((value >> (7 - bit)) & 1)
            crc = (crc << 1) & 0xFF
            if feedback:
                crc ^= 0x07
    return crc


def _integer(value: Fraction, field: str) -> int:
    if value.den != 1:
        raise TensegrityAbiError(
            f"{field}={value!r} is fractional; TGR1 accepts Z[phi] coefficients only"
        )
    if not -(1 << 31) <= value.num < (1 << 31):
        raise TensegrityAbiError(f"{field}={value!r} exceeds signed 32-bit TGR1 range")
    return value.num


def _phi_words(value: Phi, field: str) -> tuple[int, int]:
    return _integer(value.a, field + ".a"), _integer(value.b, field + ".b")


def _phi(a: int, b: int) -> Phi:
    return Phi(Fraction(a), Fraction(b))


def encode_table(system: TensegritySystem) -> bytes:
    """Encode nodes, grid tags, and edges into a checksummed TGR1 record."""

    if len(system.nodes) > 255 or len(system.edges) > 255:
        raise TensegrityAbiError("TGR1 limits node and edge counts to 255")

    payload = bytearray()
    for index, (node, grid) in enumerate(zip(system.nodes, system.grid_states)):
        if grid not in GridState:
            raise TensegrityAbiError(f"node {index} has invalid grid tag {grid}")
        words = (*_phi_words(node.x, f"node[{index}].x"),
                 *_phi_words(node.y, f"node[{index}].y"),
                 *_phi_words(node.z, f"node[{index}].z"), int(grid))
        payload.extend(NODE.pack(*words))
    if len(system.grid_states) != len(system.nodes):
        raise TensegrityAbiError("node/grid-state count mismatch")

    for index, edge in enumerate(system.edges):
        if not (0 <= edge.node_a < len(system.nodes) and
                0 <= edge.node_b < len(system.nodes)):
            raise TensegrityAbiError(f"edge {index} references a node outside the table")
        payload.extend(EDGE.pack(edge.node_a, edge.node_b, int(edge.edge_type), 0))

    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    return HEADER.pack(MAGIC, VERSION, len(system.nodes), len(system.edges), 0, checksum) + payload


def decode_table(blob: bytes) -> TensegritySystem:
    """Decode a TGR1 record without claiming it is mechanically admissible."""

    if len(blob) < HEADER.size:
        raise TensegrityAbiError("TGR1 record is shorter than its header")
    magic, version, node_count, edge_count, flags, checksum = HEADER.unpack_from(blob)
    if magic != MAGIC or version != VERSION or flags != 0:
        raise TensegrityAbiError("unsupported TGR table magic, version, or flags")
    expected = HEADER.size + node_count * NODE.size + edge_count * EDGE.size
    if len(blob) != expected:
        raise TensegrityAbiError(f"TGR1 size {len(blob)} does not match header size {expected}")
    payload = blob[HEADER.size:]
    if (zlib.crc32(payload) & 0xFFFFFFFF) != checksum:
        raise TensegrityAbiError("TGR1 payload CRC-32 mismatch")

    nodes = []
    grids = []
    offset = 0
    for _ in range(node_count):
        xa, xb, ya, yb, za, zb, grid = NODE.unpack_from(payload, offset)
        offset += NODE.size
        try:
            grids.append(GridState(grid))
        except ValueError as exc:
            raise TensegrityAbiError(f"invalid TGR1 grid tag {grid}") from exc
        nodes.append(Vec3Phi(_phi(xa, xb), _phi(ya, yb), _phi(za, zb)))

    edges = []
    for _ in range(edge_count):
        node_a, node_b, edge_type, reserved = EDGE.unpack_from(payload, offset)
        offset += EDGE.size
        if reserved != 0:
            raise TensegrityAbiError("nonzero reserved TGR1 edge byte")
        try:
            kind = EdgeType(edge_type)
        except ValueError as exc:
            raise TensegrityAbiError(f"invalid TGR1 edge type {edge_type}") from exc
        edges.append(Edge(node_a, node_b, kind))
    return TensegritySystem(nodes=nodes, grid_states=grids, edges=edges)


def encode_status(state: TensegrityState, fault: TensegrityFault,
                  vector_id: int = 0) -> bytes:
    """Encode the fixed eight-byte status record for a future sidecar."""

    if not 0 <= vector_id <= 0xFFFFFFFF:
        raise TensegrityAbiError("vector_id is outside the uint32 range")
    return STATUS.pack(VERSION, int(state), int(fault), 0, vector_id)


def decode_status(blob: bytes) -> tuple[TensegrityState, TensegrityFault, int]:
    if len(blob) != STATUS.size:
        raise TensegrityAbiError("TGR1 status must be exactly eight bytes")
    version, state, fault, reserved, vector_id = STATUS.unpack(blob)
    if version != VERSION or reserved != 0:
        raise TensegrityAbiError("unsupported TGR1 status version or flags")
    try:
        return TensegrityState(state), TensegrityFault(fault), vector_id
    except ValueError as exc:
        raise TensegrityAbiError("invalid TGR1 state or fault code") from exc


def encode_load_transaction(system: TensegritySystem, vector_id: int = 0) -> bytes:
    """Encode one complete CMD 0xB2 SPI transaction, including transport CRC."""

    if not 0 <= vector_id <= 0xFFFFFFFF:
        raise TensegrityAbiError("vector_id is outside the uint32 range")
    table = encode_table(system)
    if len(table) > 0xFFFF:
        raise TensegrityAbiError("TGR1 table exceeds the B2 uint16 length field")
    body = bytes((CMD_TGR_LOAD,)) + LOAD_PREFIX.pack(len(table), vector_id) + table
    return body + bytes((crc8_ccitt(body),))


def decode_transport_status(blob: bytes) -> tuple[
        TensegrityState, TensegrityFault, int, int, int, int, int, int, int]:
    """Decode CMD 0xB3: frozen eight-byte TGR1 status plus loader diagnostics."""

    if len(blob) != STATUS.size + TRANSPORT_DIAG.size:
        raise TensegrityAbiError("TGR transport status must be exactly 16 bytes")
    state, fault, vector_id = decode_status(blob[:STATUS.size])
    flags, error, nodes, edges, received, expected = TRANSPORT_DIAG.unpack_from(
        blob, STATUS.size)
    return state, fault, vector_id, flags, error, nodes, edges, received, expected
