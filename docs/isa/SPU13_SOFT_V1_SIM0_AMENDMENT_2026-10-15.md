# SPU13 Soft v1 SIM-0 Fixture Amendment

**Date:** 2026-10-15
**Status:** OWNER-APPROVED AMENDMENT — replayed and repinned
**Profile:** `spu13-soft-v1`, specification version 1
**Affected artifact:** `fixtures/spu13_soft_v1_sim0_vectors.json`

## Approved changes

The owner approved two corrections to the vector
`overflow_preserves_nontrivial_full_state`:

1. Word 0 changes from `2000000004000000` (`CALL 4`) to
   `2000000001000000` (`CALL 1`). This allows the program to execute its
   register-initialization words before reaching the faulting instruction.
2. The pre-fault and post-fault architectural PC values change from `7` to
   `4`, the word index of the faulting `MUL`.

No ISA semantics, other vector fields, other fixtures, or source-pin contents
were changed.

## Replayed execution and atomicity

The corrected five-word program executes as follows:

| Word | Instruction | Result |
|---:|---|---|
| 0 | `CALL 1` | Pushes return address 1 and transfers to word 1; retires once. |
| 1 | `LD R0, 32767, 32767` | Initializes `R0`; retires. |
| 2 | `LD R1, 32767, 32767` | Initializes `R1`; retires. |
| 3 | `QLDI QR2, 1, 2, 3, 4` | Initializes `QR2`; retires. |
| 4 | `MUL R0, R1` | Exact result exceeds signed32; faults atomically without retirement. |

Immediately before and after the fault, the complete architectural state is
identical:

```json
{
  "pc": 4,
  "retired": 4,
  "stack": [1],
  "scalar_nonzero": {
    "0": [32767, 32767],
    "1": [32767, 32767]
  },
  "quadray_nonzero": {
    "2": [[1, 0], [2, 0], [3, 0], [4, 0]]
  },
  "flags": null,
  "memory": null,
  "device_state": null
}
```

An independent literal trace of the five instructions confirmed the encoded
CALL target, setup state, and exact multiply result `(4294705156,
2147352578)`. Both coefficients exceed signed32. The host reports `OVERFLOW`;
the instruction changes no architectural state. The test faults before `RET`
and therefore does not demonstrate a successful subroutine return.

## Preserved artifact history

| Artifact | Prior identity | Amended identity |
|---|---|---|
| SIM-0 vector file SHA-256 | `65dc479c506dd04a48e49f9ead0aa66b3d1f71c6b531a23680ce58183990dd02` | `1037be65943162411dbadbd992aa18fa4481954d20d4924a508e67e4703c4fd6` |
| SIM-0 artifact manifest SHA-256 | `2d1dd26007bcf0c5b9dc1b223d76021a8cb01f3cfb2fcc2ab9edb2cc19ba432e` | `c2830c21d70f18db90bbfce13877745b00a5cce60ac6d0ccd8431a138fb3b14a` |

The artifact manifest now pins the amended vector hash. Its other pinned
artifacts were verified unchanged:

| Unchanged input | Verified SHA-256 |
|---|---|
| SIM-0 accepted review | `5269e9c22f750ee3c95a3dba25240dd8929575fbb4f3d598b9a02b71707f8422` |
| ISA source-pin manifest | `d5fbd01467b53b03343c5ec74e0fdebdf39829ba62db8d21452e9918411867e5` |
| ISA source-pin patch | `5adef291f2a678da3f7993788c64a717024aacba2dc90948e3722632f1c75737` |
| T1d packet | `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` |
| T1d reference pixels | `7c48bdeffac97bba871e5c92663168900cb617f8586976e66f09077e11b7f138` |
| T1d reciprocal table | `a64327c1bc0c8c74a4fb8c849a922a1f8b3d6a6e2e3bb58951d11f2012bb5248` |

## SIM-1 gate

The amended vector and artifact manifest passed hash verification and the
corrected semantic trace. This amendment resolves the fixture inconsistency;
it does not change the accepted instruction semantics. The previously
owner-authorized bounded SIM-1 implementation may resume under its separate
contract. No RTL or hardware work is authorized by this amendment.
