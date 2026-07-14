#!/usr/bin/env python3
"""Golden fixture contract for the first tensegrity sidecar probe."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.tensegrity_abi import decode_status, decode_table, encode_status, encode_table
from lib.tensegrity_vectors import golden_vectors, run_oracle


vectors = golden_vectors()
assert [vector.vector_id for vector in vectors] == list(range(7)), "vector IDs must stay contiguous"
assert [vector.name for vector in vectors] == [
    "canonical_balanced", "fault_topology", "fault_strut_collision",
    "fault_cable_slack", "fault_strut_intersection", "fault_grid_mismatch",
    "fault_not_in_equilibrium",
], "vector names/order are the hardware contract"

for vector in vectors:
    table = encode_table(vector.system)
    restored = decode_table(table)
    state, fault = run_oracle(restored)
    assert (state, fault) == (vector.expected_state, vector.expected_fault), (
        f"{vector.name}: got {state.name}/{fault.name}")
    status = encode_status(state, fault, vector.vector_id)
    assert decode_status(status) == (state, fault, vector.vector_id)
    print(f"PASS {vector.vector_id}: {vector.name} -> {state.name}/{fault.name} ({len(table)} bytes)")
