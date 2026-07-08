# Photonic Jet-Ring Acceleration — Research Notes (Shelved)

**Status: shelved 2026-07-08.** Not on the roadmap. Current market focus is
deterministic compute / robotics / avionics, where the pure-RTL sparse jet
path already wins at the depths those applications need (ε³/ε⁵). These notes
preserve the analysis so the direction can be picked up without re-deriving it.

## What maps well to optics

The jet multiply is a truncated Cauchy product — a small 2D convolution:

```
(J*K)_k = Σ_{i=0}^{k} j_i · k_{k-i}
```

Free-space / integrated optical correlators compute all output orders of a
convolution simultaneously, in effectively O(1) latency, independent of N.
Each A₃₁ component could occupy a wavelength channel; at N=8 (ε⁹) that is a
9×9 multiply-accumulate fabric per operand pair. The electronic cost is
O(N²) per jet_mul, so the optical advantage *grows with jet depth* — it is
zero at N=2 where the whole product is 6 base multiplies.

## What stays electronic (hard constraints)

- **Mersenne reduction mod 2³¹−1** — nonlinear; needs an O-E-O boundary per
  product, which eats most of the optical latency win.
- **Tower inversion** (Fermat chain, ~76 cycles) — iterative and stateful.
- **Control** — type-lattice schedule, FSMs, tag logic.

Any realization is hybrid: photonic Cauchy kernel inside an electronic
reduction/control shell.

## The honest blocker: precision vs. the exactness thesis

Analog photonic MACs demonstrate ~6–8 bit precision today. The SPU value
proposition is *bit-exact* arithmetic — 32-bit exact residues. An
approximate optical kernel under an exact-arithmetic ISA is a category
error unless the optical stage is made exact (digital photonic logic, or
residue decompositions narrow enough that each optical channel is
error-free with margin). This tension, not integration difficulty, is the
reason to shelve: the roadmap markets buy determinism first.

## Scope discipline for any future claims

The jet-ring layer is field-agnostic *as structure*: `jet_ring_N.py`
delegates every base operation, and the RTL FSM/sequencing/tag algebra
carry over unchanged across base fields. But the current silicon is not
field-portable as-is — `P = 2³¹−1` and the `m31_add/sub/neg` helpers are
baked into the jet modules, the shared multiplier is A₃₁-specific, and the
tower is a field-specific exponent chain. Porting cost = one multiplier,
one reduction, one tower schedule, one width parameter. State it that way;
do not claim "the RTL does not change when you switch fields."

## Revisit triggers (all should hold before reopening)

1. An application actually needs ε⁷+ jet depths (where Newton currently
   wins electronically, 1.12×–1.50×, and the O(N²) Cauchy cost dominates).
2. Digital/exact photonic multiply demonstrations at ≥16-bit fixed point.
3. The sparse jet MAC + series stream RTL is mature silicon, so the
   electronic baseline for comparison is real measured cycles, not models.

Cost baselines to compare against live in `software/lib/digon_recursive.py`
(tables regenerate with one command; see AGENTS.md).
