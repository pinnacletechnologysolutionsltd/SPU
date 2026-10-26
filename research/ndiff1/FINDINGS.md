# NDIFF-1 — Generalised PH composition cost

2026-10-25. Host-only stdlib Python on the NDIFF-0 base curve (generator degree 2, Q(√3)); no RTL/ISA/SIM-CAP1 change.
Software-only, single author, no independent acceptance. Builds on `research/ndiff0` (commit d0afaef).

```bash
python3 -I -B research/ndiff1/test_ndiff1.py   # controls
python3 -I -B research/ndiff1/ndiff1.py        # 11 chains x 6 strategies
```

## Strategies (cost model frozen in `rep.py`; units = rational mul+add; inv and sqrt charged 2 surd mul + 1 add, placeholders)

POLY (transform X,Y, maintain X′,Y′) · PRIM (POLY + primitive generators, where representable) · GEN (POLY + (h,a,b)) ·
GEN_REBUILD (GEN, but X,Y re-integrated from the hodograph every step: conversion charged) ·
COMP_POLY / COMP_PH (no maintenance: evaluate the base curve, apply the chain pointwise).
Every result is checked against an independent pointwise chain-rule oracle (`facts`) built from the NDIFF-0 Fraction oracle.

## Method note (control added after seeing results)

Gate as first frozen: "GEN total < materialised POLY total at N=100". It passed on the 4 chains containing t² (E,G,H,I)
and failed on the rest. That comparison was unfair: t² doubles the degree of the materialised polynomial, while the
composed-at-evaluation control evaluates the unchanged degree-5 base. I added COMP_* and the **revised gate: GEN must beat
every other strategy at N=100**. Both gates are reported; the revision was made after the first table, not before.

## Results (N = number of evaluations after the chain; full table in the script output)

| Best strategy over the 11 chains | N=1 | N=10 | N=100 |
|---|---|---|---|
| COMP_PH | 10 | 3 | 2 |
| COMP_POLY | 1 | 1 | 1 |
| POLY (materialised) | – | 5 | 4 |
| PRIM | – | 2 | 3 |
| **GEN** | **0** | **0** | **1** |

* GEN wins one chain (H: rot30, scale √3, t²) at N=100, by 3% (30,980 vs 32,000) — inside the model's placeholder error.
* Where primitive generators exist (rot60, scale 3, rot60+scale3 chains) PRIM beats POLY by ~9% at N=100 (e.g. 17,088 vs 18,768): the
  NDIFF-0 saving survives, because PRIM keeps h=1.
* GEN's per-evaluation cost equals POLY's for rotation/scale chains: the extra h multiplies (3 per evaluation) cancel the PH saving.
  It never has an evaluation advantage there, only the maintenance cost (≈ +80% over POLY for one rotation: 302 vs 168).
* GEN_REBUILD (re-integrating the position each step) costs 1.8–13× the maintenance of transforming X,Y; never best.
* For t² chains the composed evaluators win outright (E: 21,000 vs 30,600 for GEN at N=100).
* Coefficient growth: bounded here (≤9-bit numerators, 13-bit lcm denominators on these chains); 4 sequential 30° rotations take GEN
  generators to (9,2) bits. Degree growth under t² (5→10→20) dominates materialised cost.
* Representability (decision procedures, confirmed by `sympy_check.py` in NDIFF-0): PRIM fails on rot30, scale √3, every t²; GEN and the
  composed strategies never fail.

## Classification: **STOP for the generalised (h,a,b) form as a retained SPU geometry format**

Gate 0 (materialised baseline) is met on t² chains only; the revised gate (all strategies) is met on 1 of 11 chains by a margin below
the model's resolution. The format's one real merit — staying inside Q(√3) under every tested transform — is cheaper to obtain by
composing at evaluation time (no stored form at all) or by keeping plain polynomials. NDIFF-0's NARROW stands for **primitive** PH:
exact polynomial speed/arc length, ~11% tangent-path saving, only while the curve stays in primitive form.

## Not tested (limits)

Eager sequential application only: fused/lazy composition of consecutive similarities (one 2×2 similarity per run of rot/scale) would
lower every maintained strategy and the composed ones alike. One base curve (d=2) and one evaluation point; placeholder inv/sqrt charges;
t→1/t, jets of order 2, arc-length/offset outputs, wall-clock time, memory traffic and hardware not measured. PH-only exact speed σ is not
in the cost comparison.
