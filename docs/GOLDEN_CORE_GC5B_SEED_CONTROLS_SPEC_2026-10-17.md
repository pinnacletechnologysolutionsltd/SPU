# Golden Core GC-5B — bounded initial-state controls

**Status:** Executed bounded software experiment; see
[`GOLDEN_CORE_GC5B_SEED_CONTROLS_RESULTS_2026-10-17.md`](GOLDEN_CORE_GC5B_SEED_CONTROLS_RESULTS_2026-10-17.md)

**Date:** 2026-10-17

**Dependencies:** GC-4 exact symmetry catalog; GC-5 oriented-edge operator;
GC-5A trajectory implementation

**Scope:** Four exact seeds, two coefficient profiles, 12 updates, one frozen
orientation-reversing map

**Hardware / ISA:** No RTL, ISA, device, or SPU-13 profile changes

## Question

How do selected initial states affect exact trajectories and a seed-relative
parity defect under the already-qualified neutral and signed laws? This tranche
holds the substrate and operator fixed; it does not infer an effect from one
seed as a property of the rule.

## Frozen initial states

Use the lexicographic 60 directed-edge basis from GC-5 and exact coefficients
in `Q(√5)`:

1. `impulse_01`: coefficient 1 on `(0,1)`, zero elsewhere (GC-5A seed).
2. `uniform`: coefficient 1 on every directed edge.
3. `face_cycle_012`: coefficient 1 on `(0,1)`, `(1,2)`, and `(2,0)`, zero
   elsewhere.
4. `dense_signed`: on directed edge index `i`, set
   `(i mod 3 − 1) + ((7i mod 5) − 2)√5`.

Run each seed for 12 updates under `(1,1)` and `(3+√5,1−√5)`. The latter is
signed linear arithmetic; the negative coefficient is not a probability.

## Mirror comparison and observables

Use the lexicographically first orientation-reversing GC-4 symmetry as the
single frozen mirror map. Transport the seed through its directed-edge map;
for the signed profile, exchange the two coefficients. At every step compare
the transported original state with the independently evolved mirrored state
by exact vector equality.

Record per step: state hash, maximum coefficient bit length, total coefficient
sum, the existing `(0,1)` left-minus-right channel probe, and the count of edge
coefficients differing from the state transported through the mirror map.
Also report the first repeated exact state within steps 0 through 12, if any.

The parity-defect count measures state asymmetry relative to one specified
reflection. A nonzero value under a parity-neutral law is a state-level effect;
it does not indicate broken symmetry of the law. The uniform state is the
parity-neutral negative control and must retain zero defect. The mirror pair
must still satisfy covariance for every seed and profile.

Freeze all seeds, the mirror permutation, profiles, horizon and per-step
measurements in a fixture. This is a bounded seed-sensitivity sample, not a
general classification of initial conditions or long-term recurrence.
