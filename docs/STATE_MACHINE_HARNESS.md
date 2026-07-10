# State-Machine Harness — Categorical Correctness Framework for SPU

> The ROTC exponent-tagged deferred-reduction state machine (CLEAN/PENDING/FAULT)
> is the first application of a broader idea: every SPU subsystem carries its
> correctness state as part of the data, transitions are guarded by invariants,
> and failure is a terminal state — never silent drift.

## 1. Foundation — Yanenko's Evolving Categories

Evgeny Yanenko's "Evolving Categories" (2004, arXiv; `Theory/EvolvingCategories.pdf`)
proposes representing both data and algorithms uniformly as a categorical state
machine:

- **State as a tree.** Each state is a rooted tree where nodes are Finset objects
  (sets, natural numbers, Booleans) and edges carry two kinds of arrows: *address
  arrows* (Pos paths — unique physical location) and *data arrows* (Finset
  mappings — the value at that location). The root is the initial object 0; there
  is exactly one address arrow from the root to every node.

- **Transitions as categorical operations.** A transition `<node> = <tree>` builds
  a new subtree from the current state (using products, coproducts, term
  evaluation), then replaces the subtree rooted at `<node>`. Products (Cartesian
  pairs) model parallel computation; coproducts (tagged unions) model conditional
  branching. The instruction set *is* the categorical algebra.

- **Modularity.** Every subtree is its own independent category with its own
  initial object. A module connects to its parent by a single context arrow. This
  scales from a single ROTC state machine to the entire SPU stack — each subsystem
  is a self-contained category that the parent dispatches into.

- **Semantics from structure.** The machine's transitions are not "mystic" —
  they are categorical morphisms whose meaning is given by the Finset diagram.
  A state is *reachable* if there exists a composition of morphisms from the
  initial state. An invariant is a property that holds in every reachable state.

The key reframing Yanenko enables: **error is not drift — it's a terminal state in
the category.** A FAULT state has no outgoing morphisms (no composition defined).
This is exactly the discipline the ROTC harness already follows: MISALIGNED,
OVERFLOW, and INEXACT are terminal states — no rotor launch, no silent corruption.

## 2. Method — Categorical State-Machine Verification

For each SPU subsystem we define:

1. **State set S** — the Finset objects that represent computational states.
2. **Initial state s₀** — the state after reset / before first use.
3. **Transitions T ⊆ S × S** — guarded categorical morphisms. Each transition
   has a precondition (the guard) and a postcondition (the effect on the state
   tree). Transitions from FAULT states are *undefined*.
4. **Terminal states F ⊆ S** — states from which no transition is defined
   (FAULT, DONE).
5. **Invariants I(s)** — properties that must hold in state s, expressed as
   Finset-diagram conditions (set membership, inequality, zero-test).

Verification then reduces to:

- **Reachability.** Enumerate all states reachable from s₀ via T. For small
  state spaces (ROTC: 5 states; SOM: 5; Padé: 4; Lucas: 5; Batch: 6), this
  is exhaustive — every path is exercised.
- **Invariant preservation.** For each transition t: s₁ → s₂, prove
  I(s₁) ∧ guard(t) ⇒ I(s₂). For FAULT states, I(s) must be trivially true
  (no further computation depends on them).
- **Termination.** Every maximal path from s₀ ends in F. No livelock, no
  infinite recomposition without reaching a terminal state.

The ROTC harness already does all three (verified 2026-07-09, 8/8 acceptance
tests). The plan below applies the same discipline to every other SPU subsystem.

## 3. Subsystem State Machines

### 3.1 ROTC — Rotation with Exactness (DONE)

```
States:    CLEAN, PENDING, FAULT.{MISALIGNED, OVERFLOW, INEXACT}
Initial:   CLEAN
Terminal:  FAULT.*

Transitions:
  ROTATE:  CLEAN  → CLEAN    (guard: angle ≤ 23, apply F/G/H circulant)
  ALIGN:   CLEAN  → PENDING  (guard: axis has nonzero residue mod 3)
  REDUCE:  PENDING → CLEAN   (guard: residue ≡ 0 mod 3 after reduction)
  REDUCE:  PENDING → FAULT.MISALIGNED  (guard: residue ≠ 0 mod 3)
  REDUCE:  PENDING → FAULT.OVERFLOW    (guard: signed value out of range)
  REDUCE:  PENDING → FAULT.INEXACT     (guard: value changed but residue ≠ 0)

Invariants:
  I(CLEAN):   all four components ≡ 0 mod 3 on their invariant axis
  I(PENDING): explicit exponent-tag set, value is unreduced
  I(FAULT.*): true (terminal)
```

Status: Implemented in `spu13_rotor_core_tagged.v`, 8/8 acceptance tests,
Python oracle in `software/lib/rotc_thirds_native.py`. Not yet synthesised
or run on hardware (the TDM `div3` core remains the silicon baseline).

### 3.2 SOM/BMU — Kohonen Classification

```
States:    IDLE, CLASSIFYING, CONVERGED, DIVERGED, TRAINING
Initial:   IDLE
Terminal:  DIVERGED (ambiguous — no unique winner)

Transitions:
  CLASSIFY:      IDLE       → CLASSIFYING  (guard: feature vector loaded)
  WTA_SETTLE:    CLASSIFYING → CONVERGED   (guard: BMU quadrance < 2nd-best)
  WTA_SETTLE:    CLASSIFYING → DIVERGED    (guard: BMU = 2nd-best → tie)
  TRAIN_STEP:    CONVERGED   → TRAINING    (guard: learning rate > 0)
  TRAIN_COMMIT:  TRAINING    → IDLE        (guard: weight update applied)
  RESEED:        DIVERGED    → IDLE        (explicit reset, not automatic)

Invariants:
  I(CLASSIFYING): WTA tree is stable (no oscillation)
  I(CONVERGED):   BMU index is unique, quadrance(BMU) ≥ 0
  I(TRAINING):    weight deltas are bounded by learning rate × |feature − weight|
  I(DIVERGED):    true (terminal; user must reseed or adjust topology)
```

Implementation notes:
- The 7-node parallel SOM array (`spu_som_node_array.v`) has a combinational
  WTA tree. The DIVERGED state fires when `som_ambiguous` is asserted — two
  or more nodes claim exactly equal quadrance to the input.
- Training transitions are opcode-driven (SOM_CLASSIFY 0x2A, SOM_TRAIN 0x2B);
  the state machine lives in `spu13_core.v` alongside the ROTC FSM.
- The Nguyen cluster reduction (`knowledge/RATIONAL_SOM_NGUYEN_CLUSTER_NOTES.md`)
  can trigger RESEED programmatically when the DIVERGED count crosses a threshold.

### 3.3 BTU — Spatial-to-A₃₁ Transmutation

```
States:    IDLE, ARBITRATING, ROUTED, COLLISION
Initial:   IDLE
Terminal:  none (COLLISION is recoverable)

Transitions:
  LOAD:        IDLE        → ARBITRATING  (guard: 4-lane BRAM populated)
  RESOLVE:     ARBITRATING → ROUTED       (guard: all lanes to distinct slots)
  RESOLVE:     ARBITRATING → COLLISION    (guard: ≥2 lanes target same slot)
  DRAIN:       COLLISION   → ARBITRATING  (guard: priority encoder settled)
  COMMIT:      ROUTED      → IDLE         (guard: A₃₁ output latched)

Invariants:
  I(ARBITRATING): lane request vector ∈ {0,1}⁶⁴, at most 6 bits set
  I(ROUTED):      output slots are pairwise distinct
  I(COLLISION):   backlog queue length < depth (no silent drop)
```

Implementation notes:
- The priority encoder (`spu_btu_collision_resolver.v`) reduces 64→6 lanes.
  COLLISION fires when the encoder sees contention; the bubble-stall mechanism
  in `spu13_btu_core_top.v` serializes the losers into the next cycle.
- The invariant check is structural: the resolver is a pure combinatorial
  priority encoder — it's correct by construction if the priority is total.

### 3.4 Padé Evaluator — Rational Approximant

```
States:    IDLE, EVALUATING, SINGULAR, DONE
Initial:   IDLE
Terminal:  SINGULAR (denominator zero — result undefined)

Transitions:
  EVAL:    IDLE       → EVALUATING  (guard: coefficient table hydrated)
  FINISH:  EVALUATING → DONE        (guard: denominator norm ≠ 0 in A₃₁)
  FINISH:  EVALUATING → SINGULAR    (guard: denominator norm = 0 → FLAGS.V)
  RESET:   SINGULAR   → IDLE        (guard: explicit clear, never automatic)
  RESET:   DONE       → IDLE        (guard: result consumed)

Invariants:
  I(EVALUATING): Horner accumulator is valid A₃₁ element (all 4 limbs in [0, M31))
  I(DONE):       denominator⁻¹ × denominator ≡ 1 (mod M31) — inversion identity
  I(SINGULAR):   FLAGS.V = 1, output latch holds zero (safe default)
```

Implementation notes:
- The A₃₁ inverter (`spu13_fp4_inverter.v`) already asserts FLAGS.V on zero
  norm. SINGULAR is the state-machine formalization of that flag.
- The singular absorber testbench (`singular_absorber_tb.v`) exercises the
  zero-norm path; this can be extended to verify that no downstream computation
  consumes a SINGULAR result.

### 3.5 Lucas Phinary MAC — Z[φ]/L_p Arithmetic

```
States:    IDLE, DOUBLED, SCALED, CHIRAL, MULTIPLIED, INVERTED, OVERFLOW
Initial:   IDLE
Terminal:  OVERFLOW (modulus exceeded)

Transitions:
  PSCALE:  IDLE       → SCALED      (guard: φ-scaling factor ∈ Z[φ])
  LOAD2X:  IDLE       → DOUBLED     (load-path conditioning, imm << 1)
  SCALE2:  IDLE       → DOUBLED     (runtime conditioning, x + x)
  IROTC:   DOUBLED    → DOUBLED     (guard: DOUBLED tag + index ≤ 59 at
                                     dispatch ONLY; the /2 inside the
                                     micro-program is unguarded — doubling
                                     theorem, see docs/IROTC_SPEC.md §3–4)
  ROTC-thirds: DOUBLED → IDLE       (tag cleared — thirds output breaks A₅
                                     divisibility safety)
  PSCALE:  DOUBLED    → SCALED      (rotation micro-program interior)
  PCHIRAL: SCALED     → CHIRAL      (guard: chirality bit matches sequence parity)
  PMUL:    CHIRAL     → MULTIPLIED  (guard: Barrett reduction remainder < L_p)
  PINV:    MULTIPLIED → INVERTED    (guard: GCD complete, inverse verified)
  PINV:    MULTIPLIED → OVERFLOW    (guard: modulus overflow during GCD)
  COMMIT:  INVERTED   → IDLE        (guard: result latched)
  RESET:   OVERFLOW   → IDLE        (explicit clear)

Invariants:
  I(DOUBLED):    value = 2·(integer Z[φ] load) evolved only by A₅
                 transitions — every IROTC pre-division sum is even
  I(SCALED):     value < L_p (post-scaling modulus check)
  I(CHIRAL):     parity(value) = chirality_config[1]
  I(MULTIPLIED): product < L_p² before reduction, < L_p after
  I(INVERTED):   value × inverse ≡ 1 (mod L_p)
  I(OVERFLOW):   true (terminal)
```

DOUBLED is a data-plane state deliberately ordered as a *prefix* of the
operation-trace states: the doubling is an intrinsic part of the
rotational operation itself (icosahedral matrices live in ½Z[φ]; the
doubled representation is what closes them over Z[φ]), so no rotation
micro-program PSCALE may fire from a register that has not passed
through DOUBLED. See `docs/IROTC_SPEC.md` for the full tag algebra.

Implementation notes:
- The Lucas MAC is small (~200 LUTs) and the state space is 6 states — exhaustive
  verification is cheap.
- The 1M-step zero-drift marathon (`test_lucas_mac_oracle.py`) already proves
  PSCALE→PCHIRAL→PMUL→PINV closure under repeated composition; what's missing
  is the OVERFLOW path test (deliberately feed a value that exceeds the modulus
  and verify the terminal state).

### 3.6 Batch Inverter — Montgomery k-inversion

```
States:    IDLE, BATCHING, INVERTING, SINGULAR_ISOLATED, REBATCHING, DONE
Initial:   IDLE
Terminal:  DONE, SINGULAR_ISOLATED (with empty remaining set)

Transitions:
  BUILD:      IDLE              → BATCHING          (guard: k ≤ 16 lanes loaded)
  INVERT:     BATCHING          → INVERTING         (guard: product tower built)
  FINISH:     INVERTING         → DONE              (guard: all k inverses valid)
  ISOLATE:    INVERTING         → SINGULAR_ISOLATED (guard: ≥1 zero divisor found)
  REBATCH:    SINGULAR_ISOLATED → REBATCHING        (guard: non-singular subset > 0)
  REBATCH:    SINGULAR_ISOLATED → DONE              (guard: non-singular subset = 0)
  FINISH_R:   REBATCHING        → DONE              (guard: unit-subset inverses valid)

Invariants:
  I(BATCHING):          k ≤ 16, all lanes are nonzero A₃₁ elements
  I(INVERTING):         product tower = ∏ᵢ aᵢ (the batch Montgomery product)
  I(SINGULAR_ISOLATED): singular_mask[i] = 1 iff lane i has zero norm
  I(REBATCHING):        all lanes in the subset are certified nonsingular
  I(DONE):              forall i: result[i] × input[i] ≡ 1 (mod M31) or result[i] = 0
                        with singular_mask[i] = 1
```

Implementation notes:
- The batch inverter (`spu13_batch_inverter.v`) uses a shared multiplier muxed
  between tower and stream. The state machine formalizes the contract in
  `docs/MONTGOMERY_BATCH_INVERSION.md`.
- The golden-vector testbench (`spu13_batch_inverter_tb.v`) includes the
  ordering-adversarial unit-LAST case that caught a stale-read isolation bug
  (fixed 2d8658b). These orderings must stay in the test vectors when the
  state-machine verification is added.

## 4. Verification Plan

### Phase 1 — Formalize (this session)

Define the state machine for each subsystem as a concrete table (states,
transitions, guards, invariants) in this document. The ROTC harness is the
reference — every other subsystem follows the same template.

### Phase 2 — Python oracle per subsystem

For each subsystem, write a Python oracle that:
- Enumerates all reachable states
- Checks invariant preservation across every transition
- Verifies that FAULT/DIVERGED/SINGULAR states are terminal
- Verifies that every maximal path reaches a terminal state

This is the same pattern as `test_rotc_thirds_native.py` (69 checks) applied to
SOM, BTU, Padé, Lucas MAC, and Batch inverter. The state spaces are small
(4–6 states each) so exhaustive enumeration is feasible.

### Phase 3 — RTL testbench per subsystem

For each subsystem, add acceptance tests to the existing testbench that:
- Drive the subsystem into every reachable state
- Assert invariants in each state
- Assert that FAULT states prevent further transitions
- Cross-verify against the Python oracle

The ROTC tagged-core testbench (`spu13_rotor_core_tagged_tb.v`, 8/8) is the
template.

### Phase 4 — Integration

Wire the state signals into the southbridge SPI telemetry so the host can
read each subsystem's current state. This turns the categorical state machine
from a verification tool into a runtime observability contract: the host can
check that the FPGA is in the expected state before dispatching the next
operation.

### Implementation order (cheapest-first)

| Order | Subsystem | States | Effort | Rationale |
|:------|:----------|:-------|:-------|:----------|
| 1 | ROTC | 5 | **Done** | Reference implementation |
| 2 | Lucas MAC | 6 | Small | 200 LUTs, 6 states, 1M-step oracle exists |
| 3 | Padé evaluator | 4 | Small | SINGULAR path already testbenched (`singular_absorber_tb.v`) |
| 4 | Batch inverter | 6 | Medium | Complex re-batch logic, golden vectors exist |
| 5 | SOM/BMU | 5 | Medium | WTA tree is combinational — invariants are structural |
| 6 | BTU | 4 | Small | Priority encoder is correct-by-construction |
| 7 | Series stream | TBD | Future | Depends on sparse-jet MAC landing first |
| 8 | SU3 sidecar | TBD | Future | Shared multiplier handshake |

## 5. Relationship to Existing Testing

This is not a replacement for the existing test suite. It is an additional
layer:

- **Existing tests** verify functional correctness: given input X, output Y
  matches the oracle. They answer "does it compute the right answer?"
- **State-machine verification** answers "does it fail safely when it can't?"
  and "are the invariants preserved in every reachable state?"

Together they give the full correctness argument: correct answers in clean
states, safe failure in dirty states, and no path from a dirty state back to a
clean one without explicit reduction.

## 6. References

- Yanenko, E. "Evolving Categories: Consistent Framework for Representation
  of Data and Algorithms" (2004, arXiv). `Theory/EvolvingCategories.pdf`
- `docs/ROTC_EXPONENT_STATE_MACHINE.md` — the ROTC reference implementation
- `docs/MONTGOMERY_BATCH_INVERSION.md` — batch inverter RTL contract
- `knowledge/SPU_LEXICON.md` — Davis Gate entry (§ /3 divisibility)
- `docs/SERIES_STREAM_CONTROLLER.md` — series stream contract
