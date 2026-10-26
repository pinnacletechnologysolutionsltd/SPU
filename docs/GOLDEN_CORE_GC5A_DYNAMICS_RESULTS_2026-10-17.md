# Golden Core GC-5A — bounded exact edge dynamics

**Status:** PASS within the frozen 12-step finite experiment

**Date:** 2026-10-17

**Hardware / ISA:** unchanged; no hardware qualification

## Result

Starting from the unit basis state on directed edge `(0,1)`, both the neutral
profile `(1,1)` and signed profile `(3+√5, 1−√5)` were iterated for 12 exact
updates. The run records all 13 states, including the initial state, using
canonical state hashes and coefficient-growth measurements.

For each of the 60 proper maps, the transported trajectory agrees exactly
with the same-coefficient run. For each of the 60 orientation-reversing maps,
the neutral run agrees with unchanged coefficients, and the signed run agrees
with the mirrored seed evolved under exchanged coefficients. This was checked
at every step, with exact state-vector equality. The seed-relative
left-minus-right probe changes sign under each orientation-reversing map.

The measured maximum coefficient bit length at step 12 was 8 bits for the
neutral run and 28 bits for the signed run. These values are for the frozen
seed, coefficients, representation, and 12-step horizon; they do not estimate
unbounded growth. Total coefficient sums were exactly `2^n` and `4^n`,
respectively, as expected from permutation turns and coefficient sums 2 and 4.

The signed directional probe is not persistent or monotone: it is zero at
several steps, first becomes `2+2√5` at step 1, and reaches
`−360448−163840√5` at step 12. This is evidence about the selected seed and
probe in this finite rule. It is not a probability, diffusion rule, generic
transport rate, or general claim about chiral dynamics.

The signed rule's “60 internal symmetries” means exactly 60 commuting maps
among the 120 GC-4 spatial symmetries tested. This experiment does not classify
all possible linear symmetries of the operator.

## Controls and frozen evidence

The negative control corrupts one orientation-reversing edge transport by
swapping two edge-image targets; exact trajectory comparison rejects it at
step 0. A second control fails when the signed coefficients are not exchanged
under mirror transport, at step 1.

`software/golden_core/dynamics.py` implements exact bounded iteration,
canonical state hashing, coefficient bit-length measurement, total sum, and
the seed-relative turn-channel observable. The test suite checks all 120
transported trajectories at all 13 recorded states. Per-step measurements,
profiles, controls, and the fixed horizon are frozen in
`fixtures/golden_core_gc5a_edge_dynamics.json`, SHA-256
`09c5af3a2f3d72447ee9bf3adfa8dc37e641e0de9d6608178f73720bc4b22fa4`.

## Reproduction

```sh
python3 software/tests/test_golden_core_gc5a.py
python3 software/tests/test_golden_core_gc5.py
```

This bounded edge-state experiment does not establish long-term behavior,
emergence, computational advantage, physical chirality, or hardware value.
