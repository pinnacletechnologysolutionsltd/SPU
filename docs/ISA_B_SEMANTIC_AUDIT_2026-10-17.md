# ISA-B temporal opcode semantic audit

**Date:** 2026-10-17
**Status:** Historical, read-only audit
**Profile:** Experimental ISA-B adapter; not ISA-A and not a silicon-qualified profile
**Scope:** `OFFR`, `CNFM`, `PHSLK`, and `INVJ`

This audit records the June 22, 2026 ISA-B experiment without changing its
source or implying that it is part of the production SPU-13 execution profile.
The source lineage begins at commit
`41027afbec5c7e1955f6fd2f9397bda727dad53d`, which introduced the separate
decoder, twin-register file, RAU, pipeline controller, software models, tests,
and architecture study. The later same-day commits `a460844` and `3309d96`
added temporal/SOM and full-stack simulation work. The historical commit
message reports focused test counts; this audit does not rerun or upgrade
those results to hardware qualification.

The reconciled profile record identifies ISA-A as the current SPU-13 profile
and ISA-B as a separate encoding and adapter family. Its ROTC/IROTC board
evidence does not establish execution of the ISA-B table. See the [profile
provenance record](isa/ISA_PROFILE_PROVENANCE.md) and [implementation
matrix](isa/ISA_IMPLEMENTATION_MATRIX.md).

## Outcome vocabulary

| Outcome | Meaning |
|---|---|
| **Specified** | A source specification assigns the operation a meaning. This alone does not prove implementation or cross-layer agreement. |
| **Convergent** | The specified meaning and the compared implementations agree on the declared test domain, with evidence identified. This is bounded evidence, not universal proof. |
| **Divergent** | Source evidence shows materially different operation or result semantics between layers. |
| **Unverified** | The available source does not establish whether implementations agree, or the relevant end-to-end path was not qualified. |
| **Absent** | The audited operation or implementation is not present in the named artifact. Absence is scoped to that artifact, not inferred from a search failure alone. |

An opcode may be **Specified** at the contract level while its RTL execution
remains **Unverified**. The overall outcome below refers to the strongest
cross-layer classification supported by the inspected artifacts.

## Audit matrix

| Opcode | Specification | Python/C++ model | RTL evidence | Overall outcome |
|---|---|---|---|---|
| `OFFR` (`0x40`) | Load a stored/material parameter record into destination `.O`, described as the Offer or past-boundary slot. | Python and C++ read RPLU parameters selected by material and address and write `.O`. | Decoder emits RPLU configuration/material/address controls and selects `.O`; decoder tests check those controls. The inspected evidence does not qualify an end-to-end RPLU read-to-register transaction against the software result. | **Unverified** — intent is specified and modeled, but full execution equivalence is not established. |
| `CNFM` (`0x41`) | Corresponding load into destination `.C`, described as the Confirmation or future-boundary slot. | Python and C++ read the selected RPLU parameters and write `.C`. | Decoder emits corresponding RPLU controls and selects `.C`; decoder tests check those controls. End-to-end transaction equivalence is not established by the inspected evidence. | **Unverified** — intent is specified and modeled, but full execution equivalence is not established. |
| `PHSLK` (`0x42`) | The ISA table calls this a phase-lock/intersection operation. The mechanics subsection describes a ratio-to-unity check. For nonzero confirmation quadrance, this predicate is equivalent to equality of the quadrances; a zero confirmation value needs explicit semantics because its inverse is undefined. | Python and C++ compare the two Quadray quadrances directly, so the zero/zero case is accepted as coherent. On equality they write the component-wise sum to destination `.O`. | The RAU compares the quadrances, but its PHSLK result is `q_offer`; the pipeline writes the RAU result. This is not the software model's summed Quadray. | **Divergent** — the result written by RTL differs from the software model, and the zero-denominator case is not aligned with the ratio-based specification. |
| `INVJ` (`0x43`) | Negate each Quadray component, described as inversion through a Janus point. | Python and C++ negate each of the four components. This map is an algebraic involution on that state representation. | The pipeline computes two's-complement negation of the entire packed 64-bit word, not independent 16-bit component negations. | **Divergent** — the packed RTL transform is not the specified component-wise transform in general. |

No opcode in this four-operation audit is classified **Convergent**: the
available evidence does not demonstrate end-to-end cross-layer equality for
OFFR/CNFM, while PHSLK/INVJ have identified divergences. **Absent** is not
assigned because all four names occur in the inspected ISA-B sources; it would
apply only to a separately named artifact that lacks an operation.

## Mathematical boundary

`INVJ` being an involution means only that its abstract map (J) satisfies
\(J^2=I\). Time reversal of a discrete evolution operator (U\) requires the
stronger relation \(J U J^{-1}=U^{-1}\), on a specified state space and for an
invertible evolution. The ISA-B name and a coordinate negation do not establish
that relation.

Likewise, paired `.O` and `.C` storage does not by itself implement a
two-boundary solver. The inspected PHSLK comparison is a finite arithmetic
predicate, not a demonstrated solution of Wheeler–Feynman absorber equations
or of a general initial/final boundary-value problem. “Offer,” “Confirmation,”
“Janus,” and “Wheeler–Feynman” are retained as historical architecture
vocabulary, not physical claims.

## Disposition

- Preserve the June 22 source and Git history as historical evidence; do not
  rebase, rewrite, or silently merge ISA-B into ISA-A.
- Keep production-facing work on ISA-A and the separately qualified
  simulator/RTL profiles.
- Any revival of ISA-B requires a new, explicitly named profile with one
  normative semantic contract, independent conformance vectors, and separate
  authorization for implementation or hardware work.
- This document is a source audit, not a correction to ISA-B source, a test
  result, an ISA ratification, or hardware authorization.

## Inspected source anchors

- `docs/spu13_isa_spec.md`, especially §§1, 5.5, and 5.5.1.
- `software/spu13_arch_sim.py`, temporal opcode handlers.
- `software/common/include/spu13_arch.h`, temporal opcode handlers.
- `hardware/rtl/core/shared/spu_isa_decoder.v`, temporal decode controls.
- `hardware/rtl/core/shared/spu_rau.v`, PHSLK comparison/result mux.
- `hardware/rtl/core/shared/spu_pipeline_ctrl.v`, writeback and INVJ path.
- `hardware/tests/common/spu_isa_decoder_tb.v`, decoder-control checks.
- `hardware/tests/common/spu_full_stack_tb.v`, historical composed simulation.
- `docs/isa/ISA_PROFILE_PROVENANCE.md` and `docs/isa/ISA_IMPLEMENTATION_MATRIX.md`.

No tests or hardware commands were executed while preparing this read-only
matrix.
