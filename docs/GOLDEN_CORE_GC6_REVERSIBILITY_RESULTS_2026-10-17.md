# Golden Core GC-6 — exact reversibility results

**Status:** Complete within the frozen finite scope

**Date:** 2026-10-17

**Specification:** [`GOLDEN_CORE_GC6_REVERSIBILITY_SPEC_2026-10-17.md`](GOLDEN_CORE_GC6_REVERSIBILITY_SPEC_2026-10-17.md)

**Evidence:** [`golden_core_gc6_reversibility.json`](../fixtures/golden_core_gc6_reversibility.json), checked by [`test_golden_core_gc6.py`](../software/tests/test_golden_core_gc6.py)

## Existing one-state operators

Both frozen 60-dimensional operators are invertible over `Q(√5)`:

| Profile | Exact rank | Nullity | Inverse check |
|---|---:|---:|---|
| Equal `(1,1)` | 60 | 0 | Both products equal identity on all 60 basis vectors |
| Signed `(3+√5,1−√5)` | 60 | 0 | Both products equal identity on all 60 basis vectors |

Exact Gaussian elimination agrees with the independent cycle calculation for
`U = T_L^−1 T_R`. This relative permutation has twelve cycles, each of length
5. On a cycle of length `m`, the relevant factor is
`a^m − (−b)^m`; it is nonzero for both frozen profiles at `m=5`. The fixture
pins hashes of the canonical exact inverse matrices. Since neither operator
is singular, this run produces no nonzero kernel witness.

## Paired-state construction

The separate rule

`J_(a,b)(x,y) = (F_(a,b)x − y, x)`

and inverse

`J_(a,b)^−1(u,v) = (v, F_(a,b)v − u)`

compose to identity on every basis vector of the 120-dimensional paired state
space for both profiles. Mirror covariance passes on the paired basis for all
120 frozen spatial maps. The same vertex-induced parity transport is applied
to both components, and orientation-reversing maps exchange the two weights.

This construction changes the dynamics by adding a second state component.
The result establishes reversibility and covariance for this finite linear
construction; it does not identify a distinguished Janus point, establish a
physical interpretation, or imply a hardware benefit.

## Reproduction

```bash
python3 software/tests/test_golden_core_gc6.py
```
