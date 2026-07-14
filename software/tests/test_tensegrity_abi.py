#!/usr/bin/env python3
"""TGR1 table/status ABI tests against the exact tensegrity oracle."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.tensegrity_abi import (
    EDGE,
    HEADER,
    NODE,
    STATUS,
    TensegrityAbiError,
    decode_status,
    decode_table,
    encode_status,
    encode_table,
)
from lib.tensegrity_balancer import (
    TensegrityFault,
    TensegrityState,
    make_tensegrity_six_strut,
)


def expect(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS", message)


canonical = make_tensegrity_six_strut()
blob = encode_table(canonical)
expect(len(blob) == HEADER.size + 12 * NODE.size + 30 * EDGE.size,
       "canonical TGR1 byte count is header + 12 nodes + 30 edges")

decoded = decode_table(blob)
expect(decoded.nodes == canonical.nodes and decoded.grid_states == canonical.grid_states and
       [(e.node_a, e.node_b, e.edge_type) for e in decoded.edges] ==
       [(e.node_a, e.node_b, e.edge_type) for e in canonical.edges],
       "TGR1 round trip preserves canonical topology and Z[phi] coordinates")
decoded.configure().verify_balance()
expect(decoded.state == TensegrityState.BALANCED,
       "TGR1 round-tripped canonical fixture remains exactly balanced")

corrupt = bytearray(blob)
corrupt[-1] ^= 1
try:
    decode_table(bytes(corrupt))
except TensegrityAbiError:
    print("PASS TGR1 rejects payload corruption by CRC-32")
else:
    raise AssertionError("TGR1 accepted corrupted payload")

status = encode_status(TensegrityState.FAULT_CABLE_SLACK,
                       TensegrityFault.CABLE_SLACK, 0x12345678)
expect(len(status) == STATUS.size and
       decode_status(status) == (TensegrityState.FAULT_CABLE_SLACK,
                                 TensegrityFault.CABLE_SLACK, 0x12345678),
       "TGR1 eight-byte status preserves terminal fault and vector id")
