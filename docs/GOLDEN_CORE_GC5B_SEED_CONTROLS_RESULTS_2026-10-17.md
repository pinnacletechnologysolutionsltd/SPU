# Golden Core GC-5B — bounded seed-control results

**Status:** Complete within the frozen finite scope

**Date:** 2026-10-17

**Specification:** [`GOLDEN_CORE_GC5B_SEED_CONTROLS_SPEC_2026-10-17.md`](GOLDEN_CORE_GC5B_SEED_CONTROLS_SPEC_2026-10-17.md)

**Evidence:** [`golden_core_gc5b_seed_controls.json`](../fixtures/golden_core_gc5b_seed_controls.json), checked by [`test_golden_core_gc5b.py`](../software/tests/test_golden_core_gc5b.py)

## Result

The four frozen seeds were evolved for 12 updates under each of the two
specified exact `Q(√5)` profiles. All eight trajectories match the fixture's
per-step hashes and exact measurements. For the frozen orientation-reversing
map, each independently evolved mirror trajectory equals the transported
original trajectory at all 13 states; the signed profile uses exchanged
weights as specified.

The uniform seed passes as a parity-neutral control: its parity-defect count
and left-minus-right probe remain zero under both profiles. The other seeds
produce different seed-relative responses. The impulse is invariant in this
reflection comparison under equal weights, while its signed-law defect reaches
44 of 60 edge coefficients at step 11 and remains there through step 12. The
face-cycle and dense-signed seeds each reach 56 differing coefficients by the
end of the run. These are observations about these fixed seeds, this one
reflection, and this 12-step horizon; they are not a general classification
of states or a claim that the law alone caused every observed asymmetry.

No exact state repeated within steps 0 through 12 in any of the eight runs.
The largest recorded coefficient bit length is 32 bits, for the dense-signed
seed under the signed profile. The seed-relative left-minus-right probe is
nonzero at step 12 for the face-cycle and dense-signed seeds under both laws,
and for the impulse under the signed law. The uniform control's zero probe
confirms that the observable is not forced nonzero by the substrate or update
mechanics.

| Seed | Profile | Final parity defect / 60 | Max coefficient bits | Final left-minus-right probe |
|---|---|---:|---:|---|
| impulse `(0,1)` | equal | 0 | 8 | `0` |
| impulse `(0,1)` | signed | 44 | 28 | `−360448 − 163840√5` |
| uniform | equal | 0 | 13 | `0` |
| uniform | signed | 0 | 25 | `0` |
| face cycle `(0,1),(1,2),(2,0)` | equal | 56 | 9 | `83` |
| face cycle `(0,1),(1,2),(2,0)` | signed | 56 | 28 | `280178688 + 124682240√5` |
| dense signed | equal | 56 | 11 | `−123 − 795√5` |
| dense signed | signed | 56 | 32 | `−3206103040 − 1441685504√5` |

## Reproduction and scope

Run:

```bash
python3 software/tests/test_golden_core_gc5b.py
```

The fixture pins the directed-edge basis, one reflection's vertex and edge
maps, the four seed definitions and hashes, both coefficient profiles, and
the exact per-step state hash, maximum coefficient bit length, coefficient
sum, channel probe, parity-defect count, and recurrence result. The test also
checks exact mirror covariance and the uniform-state control.

This is finite software evidence for four initial states, two laws, one
orientation-reversing map, and 12 updates. It does not establish long-term
dynamics, all-state symmetry, physical chirality, computational advantage,
or a reason to change the SPU ISA or RTL. The signed profile remains a signed
linear operator, not a probability or diffusion rule.

## Interpretation and next question

For each fixed profile the evolution is the same linear map applied to each
initial vector. The different trajectories are therefore seed-dependent
responses of one operator, not evidence that the operator changed between
seeds. The total-sum law follows directly because both constituent turns are
permutations. By contrast, the parity-defect count is a nonlinear Hamming
comparison with one reflection, so its seed dependence cannot be read as a
standalone measure of operator symmetry.

The most useful next question is exact reversibility: **is the frozen
60-dimensional update operator invertible over `Q(√5)` for each coefficient
profile, and, if not, can a minimal paired-state (Janus) extension restore
reversible evolution while preserving mirror covariance?** This is a proposed
question only; no rank, inverse, kernel, or Janus experiment is included in
GC-5B.
