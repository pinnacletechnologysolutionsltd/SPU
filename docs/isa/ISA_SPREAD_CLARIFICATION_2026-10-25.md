# ISA clarification: SPREAD (0x15), versioned 2026-10-25

Status: clarification of a specification discrepancy. The original text is retained, not edited.

## Original description (provenance)
`knowledge/isa_reference.md`, "Geometry Output" table, introduced in commit `5e41ed6`
(2026-05-26, "SPU-13 ISA reference"):

    | 0x15 | SPREAD | QRd, Q1,Q2,Q3 | Spread from three quadrances |

## What the implementations do
Python VM (`software/spu_vm.py`), C++ VM (`software/vm/spu_vm.cpp`), the assembler operand class
`RQQ` (`software/lib/assembly_operands.py`) and C++ `L_SPREAD(rd, qra, qrb)` agree:

    SPREAD Rd, QRa, QRb    ; R[d] = numerator, R[(d+1) % 26] = denominator, unreduced

The three-quadrance computation is a different operation (`spread_from_quadrances`, `DELTA`).
`docs/isa/ISA_CONFORMANCE_2026-10-10.md` already recorded the conflict ("SPREAD/JINV reference
operands: Conflicting"). Canonical form from `metric_semantics`-versioned semantics onward:
`SPREAD Rd, QRa, QRb`. The older table row is a historical description, not the implemented ISA.

## Mathematics is selected by the manifest, not the encoding
Opcode, fields and binary encoding are unchanged. `metric_semantics` (fixed at VM construction;
Python `metric_semantics=`, C++ `MetricSemantics`, CLI `--metric-semantics=`) selects:

* `legacy_dot` (default): historical result `N = Q(a)Q(b) - (sum a_i b_i)^2`, `D = Q(a)Q(b)`.
  Implemented, **mathematically unqualified**: spread(A,A) != 0 (8/9 for (1,0,0,0)).
* `gram_v1`: `B(a,b) = 4 sum a_i b_i - (sum a_i)(sum b_i)`, `N = B(a,a)B(b,b) - B(a,b)^2`,
  `D = B(a,a)B(b,b)`. Exact wide intermediates, final int32 range check in C++, unbounded in
  Python. Faults, in order: `INVALID_REGISTER`, `DEGENERATE_METRIC` (`B(v,v) = 0`), `OVERFLOW`
  (an oracle coefficient outside int32). A refusal changes no architectural state.

Contract: `research/sim_cap1_spread/GRAM_V1_CONTRACT.md`. Evidence: software conformance only
(`software/tests/test_gram_v1_spread.py`, `test_gram_v1_spread_cpp.py`). RTL SPREAD semantics
and any silicon claim are unmeasured and out of scope.
