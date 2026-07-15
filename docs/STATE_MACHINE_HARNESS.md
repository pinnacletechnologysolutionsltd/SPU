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
States:    IDLE, FRESH, MAIN, CONJ, SCALED, CHIRAL, MULTIPLIED, INVERTED,
           OVERFLOW
           (FRESH/MAIN/CONJ are the DOUBLED typestate of IROTC_SPEC v0.2 —
            the 1-bit DOUBLED of v0.1 was unsound across catalogs, found
            2026-07-10: mixed-catalog products leave ½Z[φ])
Initial:   IDLE
Terminal:  OVERFLOW (modulus exceeded)

Transitions:
  PSCALE:  IDLE       → SCALED      (guard: φ-scaling factor ∈ Z[φ])
  LOAD2X:  IDLE       → FRESH       (load-path conditioning, imm << 1)
  SCALE2:  any        → FRESH       (runtime conditioning, x + x —
                                     also the catalog-switch recovery)
  IROTC-main: FRESH|MAIN → MAIN     (guard at dispatch ONLY: state license
  IROTC-conj: FRESH|CONJ → CONJ      + index ≤ 59; the /2 inside the
                                     micro-program is unguarded — doubling
                                     theorem, see docs/IROTC_SPEC.md §3–4;
                                     wrong-catalog source = CATMIX fault)
  PCHIRAL: MAIN ↔ CONJ, FRESH → FRESH (ring automorphism carries license)
  ROTC-thirds: FRESH|MAIN|CONJ → IDLE (tag cleared — thirds output breaks
                                     A₅ divisibility safety)
  ROTC-octahedral: FRESH → FRESH; MAIN|CONJ → IDLE (integer but not A₅)
  PSCALE:  FRESH|MAIN|CONJ → SCALED (rotation micro-program interior)
  PCHIRAL: SCALED     → CHIRAL      (guard: chirality bit matches sequence parity)
  PMUL:    CHIRAL     → MULTIPLIED  (guard: Barrett reduction remainder < L_p)
  PINV:    MULTIPLIED → INVERTED    (guard: GCD complete, inverse verified)
  PINV:    MULTIPLIED → OVERFLOW    (guard: modulus overflow during GCD)
  COMMIT:  INVERTED   → IDLE        (guard: result latched)
  RESET:   OVERFLOW   → IDLE        (explicit clear)

Invariants:
  I(FRESH):      value componentwise even — N·w ≡ 0 (mod 2) for EVERY
                 integer matrix N (either catalog licensed)
  I(MAIN):       value = 2·(M_k…M₁·v) with all Mᵢ in the main A₅ —
                 next main-catalog pre-division sum is even (doubling
                 theorem); NOT licensed for the conjugate catalog
  I(CONJ):       mirror of I(MAIN) under φ → 1−φ
  I(SCALED):     value < L_p (post-scaling modulus check)
  I(CHIRAL):     parity(value) = chirality_config[1]
  I(MULTIPLIED): product < L_p² before reduction, < L_p after
  I(INVERTED):   value × inverse ≡ 1 (mod L_p)
  I(OVERFLOW):   true (terminal)
```

FRESH/MAIN/CONJ are data-plane states deliberately ordered as a *prefix*
of the operation-trace states: the doubling is an intrinsic part of the
rotational operation itself (icosahedral matrices live in ½Z[φ]; the
doubled representation is what closes them over Z[φ]), so no rotation
micro-program PSCALE may fire from a register that has not passed
through one of them. The MAIN/CONJ split is the harness story in
miniature: the state is licensed by a theorem (doubling theorem, valid
within one A₅) and the state machine refuses exactly where the theorem's
hypothesis fails (catalog mixing — machine-checked necessary, not
paranoia). See `docs/IROTC_SPEC.md` §3 for the full transition algebra
and `software/tests/test_irotc_chains.py` for the executable proofs.

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
- `docs/TENSEGRITY_BALANCER_FEASIBILITY.md` — tensegrity balancer feasibility analysis
- `software/lib/tensegrity_balancer.py` — exact tensegrity oracle
- `software/tests/test_tensegrity_balancer.py` — suite-registered tensegrity tests (36 checks)
- `docs/BOOT_SEQUENCE_FSM.md` — canonical boot-sequence FSM specification
- `software/lib/boot_sequence_oracle.py` — exact boot FSM oracle
- `software/tests/test_boot_sequence.py` — suite-registered boot FSM tests

## 7. Subsystem 6 — Tensegrity Balancer (Prototype)

### 7.1 Fuller's Tensegrity Framework

From *Synergetics* (1997) §640-790: discontinuous compression islands in a
continuous tension network, the six-strut expanded octahedron (§724.30),
sphere-as-compression-island framing (§640.20), and transverse precession
under axial compression (§640.12). The canonical six-strut fixture is not the
regular icosahedron: the executable oracle checks that the regular vertex set
with the 24-cable net has no cable-positive/strut-negative self-stress.

The canonical fixture uses cyclic permutations of `(0, +/-1, +/-2)`, the
`t = 2` all-integer expanded octahedron. Its 24 cables have quadrance 6, its
six struts have quadrance 16, and the solver derives `q_cable:q_strut = 2:-3`
exactly.

Quadrance only proves separation or collapse: zero means a cable/GAP collapsed
or strut endpoints coincide. Tension versus compression is carried by the
equilibrium force-density signs: cable/GAP positive, strut negative.

### 7.2 SPU-13 Primitive Mapping

| Fuller concept | SPU-13 primitive | Status |
|---|---|---|
| Icosahedral A5 rotations | IROTC opcode (60-entry 1/2 Z[phi] catalog) | Tang 25K silicon for probe vectors idx 16, idx 36 main, and fault matrix; full surface testbench-verified |
| Tetrahedral rotations | ROTC opcode (36-angle Q(sqrt3) catalog) | 0-5 silicon-verified; 6-35 testbench-verified |
| Quadray coordinates | QR register file | QLDI/QSUB/readback silicon-verified |
| Exact quadrance | QSUB / Davis-style exact arithmetic | Existing arithmetic probes silicon-verified |
| MAIN/CONJ grid alternation | phi-plane 4-state typestate | Core integration testbench-verified |

The bounded admission guard now has RTL and Artix silicon proof for all six
guards. The final V:7 tranche adds exact type-uniform force-density
equilibrium and produced `TGR:P V:7 E:00` on the board. General nonuniform
equilibrium and active balancing remain outside the hardware subset.

### 7.3 States

```
IDLE → CONFIGURING → BALANCED ⇄ ROTATING
           ↓              ↓
        FAULT.TOPOLOGY   FAULT.CABLE_SLACK
                         FAULT.STRUT_COLLISION
                         FAULT.STRUT_INTERSECTION
                         FAULT.GRID_MISMATCH
                         FAULT.NOT_IN_EQUILIBRIUM
```

All FAULT states are terminal (no outgoing transitions).  Recovery is
explicit `reset()`.

### 7.4 Guards (Theorem-Licensed)

| Guard | Theorem | Check |
|---|---|---|
| `guard_valid_topology` | Fuller §724.30 | ≥6 structural edges (STRUT or GAP), connected |
| `guard_struts_separated` | Fuller §640.02 | Each node touches ≤1 strut |
| `guard_struts_disjoint_interior` | Fuller §640.02 | Exact segment test rejects interior strut crossings |
| `guard_cables_taut` | Continuous tension | Cable/GAP quadrance is exact nonzero positive |
| `guard_grid_consistency` | Conjugate grid model | Cross-grid edges must be GAP type |
| `guard_equilibrium` | Static self-stress | Exact type-uniform Z[phi] densities have cable/GAP-positive and strut-negative signs; the oracle's nonuniform fallback is broader |

### 7.5 Dual-Grid Interpenetration

The architectural insight: when IROTC rotates a node between MAIN and CONJ
grids, it lands on a deterministically shifted conjugate coordinate.  The
edge spanning the grid boundary is a "tensegrity gap" — a tension member
with exact rational quadrance.  This is a discrete state transition, not a
continuous tracking problem.

The φ-plane typestate lattice (FRESH/MAIN/CONJ/UNTAGGED) from
`THEOREM_LICENSED_TYPESTATE.md` §4 is the hardware encoding of this grid
alternation.

### 7.6 Status

Prototype oracle: `software/lib/tensegrity_balancer.py`;
suite-registered tests: `software/tests/test_tensegrity_balancer.py` (44
checks). RTL: `spu13_tensegrity_guard.v` plus the term-serial exact Z[phi]
`spu13_tensegrity_intersection.v`. The first V:6 image failed fixture 4 in
silicon (`TGR:F V:4 E:84`) after a route with only 51.89 MHz modeled Fmax. The
hardened V:6 route pipelined distributed-table predicates and 108-bit
arithmetic decisions, but its board run still returned `TGR:F V:4 E:90`
(`BALANCED/F_NONE`). The successful V:6 image advances the full guard domain at 25
MHz through a divided BUFG and adds an intersection-attempt count to failure
telemetry. It uses 13,895 `SLICE_LUTX`, 3,515 `SLICE_FFX`, 72 DSP48E1 and 0
BRAM; OpenXC7 conservatively closes that guard domain at 59.16 MHz while
checking it at 50 MHz. Behavioral and synthesized-cell intersection tests
pass. The divided-clock image produced `TGR:P V:6 E:00` in silicon on
2026-07-14, closing the six-fixture admission-guard proof. Silicon scope for
the intersection predicate is the antipodal origin-crossing fixture; the
complete contact matrix remains RTL-verified.

The final admission tranche accumulates cable/GAP and strut force rows for
every node/axis over Z[phi], derives one exact type-uniform density ratio, and
checks all rows by cross multiplication plus exact sign tests. The module TB
passes canonical integer and phi-scaled coordinates and rejects the perturbed
ID 6 fixture with `NOT_IN_EQUILIBRIUM`; the Artix wrapper TB emits
`TGR:P V:7 E:00`. The packed XC7A100T image uses 22,520 `SLICE_LUTX`, 6,373
`SLICE_FFX`, 108 DSP48E1, and 0 BRAM. Post-route Fmax is 106.72 MHz for the
50 MHz UART/system domain and 42.93 MHz for the actual 25 MHz guard domain.
SHA-256 is
`7859d0e7d78218fcf49d5b4cd091332f0f0b5d5c3641edbc8b0380caba592d3f`;
the Wukong board run produced `TGR:P V:7 E:00` on 2026-07-14, closing the
seven-fixture bounded-admission silicon proof.

The table-loader tranche adds a transaction machine around that proven guard:

```text
IDLE --B2 prefix--> RECEIVE --CRC8/CS abort--> REJECT (active bank held)
                         |
                         `--transport commit--> PARSE/CRC32
                                                   |
                       malformed ------------------+--> REJECT
                                                   |
                                                   `--> REPLAY_GUARD
                                                            |
                                               terminal verdict
                                                            v
                                                    COMMIT_BANK --> IDLE
```

Its state invariant is stronger than “the bytes were valid”: the externally
visible table, vector ID, and mechanical verdict always refer to the same
committed bank. The inactive bank may be dirty while receiving or verifying,
but no failure path can select it. `0xB3` reports the committed eight-byte TGR1
status first, followed by staging diagnostics, so a rejected transaction is
observable without corrupting the last good state. Module and real-SPI
integration benches prove commit, CRC rejection, CS abort, guard replay, and
rollback, including a B3 hold across the guard's one-cycle done pulse. The
standalone Artix link closes seed-1 route/pack at 25 MHz with 24,675
`SLICE_LUTX`, 7,655 `SLICE_FFX`, 108 DSP48E1, one RAMB18E1, and 40.16 MHz
post-route guard Fmax. Its packed SHA-256 is
`a515381a8b90ceba836da83c7fe80bf719033717d72458cfb8297d7753d63463`;
board work on 2026-07-16 proves the remapped J11/SD/B2/B3 path and successful
canonical commits when either intersection or equilibrium is enabled alone.
The full combined image remains `verify_busy` after all 468 bytes are received,
so complete atomic admission/rollback are not yet silicon-proven. Refactor the
verifier into explicit transport, parser, guard-service, and coordinator FSMs
with watchdogs before adding the active propose/reverify/commit controller.

Bug-ledger case: the old regular-icosahedron antipodal fixture passes topology,
endpoint separation, tautness, grid consistency, and equilibrium, but all six
struts cross at the origin. `guard_struts_disjoint_interior` is the guard that
rejects it, proving endpoint separation alone under-approximates Fuller
§640.02.

## 8. Subsystem 7 — Canonical Boot Sequence FSM

Boot sequencing is specified as a four-state safety machine:

```
RESET → HYDRATING → READY
             ↓
        FAULT.HYDRATION_TIMEOUT
```

The load-bearing invariant is that no instruction is accepted outside READY.
The HYDRATING exit guard is the generate-conditional AND-join of existing or
proposed subsystem ready lines: VE QR init done, RPLU table loaded, and SOM
BRAM hydrated. See `docs/BOOT_SEQUENCE_FSM.md` for exact signal provenance,
watchdog-bound derivation, Pell-vault scope, and the status-polling contract.

Prototype oracle: `software/lib/boot_sequence_oracle.py`; suite-registered
tests: `software/tests/test_boot_sequence.py`. RTL is not started; the reserved
integration points are `spu13_core.v` instruction gating and `spu_spi_slave.v`
status exposure.
