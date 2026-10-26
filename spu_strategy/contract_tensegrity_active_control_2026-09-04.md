# Engineering Contract: Tensegrity Active Proposal/Actuation Controller (v1)

**Date:** 2026-09-04
**Contract ID:** `contract_tensegrity_active_control_2026-09-04.md`
**Status:** **BLOCKED — §7 gate run 2026-09-04 and the primitive is FALSIFIED as a balancing controller.** See §11. No RTL authorised.

**Roles:**
- **Spec Author:** Claude (Opus 5)
- **Halt-and-Flag Implementer:** unassigned
- **Integration Auditor:** `bash tools/verify_repo.sh`

---

## 0. Why this contract exists

`docs/TENSEGRITY_BALANCER_HANDOVER_2026-07-15.md` §"After the componentized
link proof" gates this work explicitly:

> The next major balancer task is the active proposal/actuation controller.
> **Do not infer its semantics from the admission guard.** First specify: [five items]

This document supplies those five items. It is a specification only. **No RTL
is authorised by this contract** — §7 gates RTL behind a Python falsification
result that may kill the chosen primitive outright.

### What is already closed (do not redo)

- TGR1 transport (B2) and status (B3): silicon-proven, `docs/hardware_evidence.md` §3.2l.
- Bounded admission guard (topology, strut separation, contact, GAP collapse,
  MAIN/CONJ consistency, type-uniform Z[φ] force-density equilibrium):
  silicon-proven §3.2l, and re-proven on the Karatsuba candidate §3.2l.1.
- Four-act transactional behaviour (admit / mechanical-negative / corrupt-payload
  rollback / recovery), reproduced bit-for-bit ×3.
- Python oracles green as of 2026-09-04: `test_tensegrity_balancer`,
  `test_tensegrity_abi`, `test_tensegrity_vectors`, `test_tensegrity_demo`.

The frontier is **active control only**.

---

## 1. Controlled coordinates and physical actuator mapping

**Controlled quantity:** the twelve node positions of the active TGR1 table, as
exact `Z[φ]` triples — the `cfg_x_a/x_b, cfg_y_a/y_b, cfg_z_a/z_b` signed-32-bit
pairs already accepted by `spu13_tensegrity_guard.v`. No new coordinate type.

**Actuator mapping:** one rotary actuator per strut, six total, each rotating
its strut as a rigid body. This is asserted as the *intended* mapping and is
**not hardware-verified** — no actuator exists on the bench. Every claim in this
contract is therefore `simulation-only` until a physical rig exists.

**Explicitly rejected alternative — direct node-coordinate updates.** Rejected
because it maps to no physical actuator: a tensegrity has no mechanism that
commands a node to a position. Adopting it would build a controller whose
primitive can never be actuated, and would silently redefine "actuation" as
"edit the table" — the exact inference the handover forbids.

**Explicitly deferred — cable-rest-length (tendon) control.** The physically
conventional actuation. Deferred because commanding a rest length requires
solving for node positions, i.e. a nonuniform self-stress solver, which
`docs/TENSEGRITY_BALANCER_FEASIBILITY.md` item 5 places outside the current
type-uniform admission contract. Reopening it requires its own contract.

---

## 2. Reuse rule (the load-bearing simplification)

**The controller introduces no new notion of "balanced."** A proposal is
accepted if and only if the existing `spu13_tensegrity_guard.v` returns
`ST_BALANCED` on the proposed table. The controller is a *proposal generator*
wrapped around the already-proven verifier.

Consequence: the active-control layer is the same transactional shape as B2,
one level up — propose into the staging bank, verify, commit or roll back.
The double-buffered bank in `spu13_tensegrity_sidecar.v` is reused as-is.

---

## 3. Candidate-motion primitive

**One proposal = one exact rotation of one strut.**

```
proposal := (strut_index, rotc_angle_index, axis_selector)
             3 bits        6 bits             2 bits
```

- `strut_index` ∈ [0,5] — which of the six struts moves.
- `rotc_angle_index` ∈ [0,35] — an entry in the existing exact rotation
  catalog, `knowledge/rotc_tables.md`. No new angle arithmetic.
- `axis_selector` ∈ {X, Y, Z} — rotation axis, about the strut's own midpoint.
- Rotating a strut moves exactly its two endpoint nodes. All other nodes are
  invariant under a proposal.

**Why this primitive:** a strut is rigid, so rotating it is the only motion
that is simultaneously (a) physically actuatable by a single rotary device,
(b) exactly representable in `Z[φ]` via machinery already verified in silicon,
and (c) bounded to a finite, enumerable candidate set.

**INVARIANT — lattice closure.** Every rotated coordinate MUST remain exactly
representable in the signed 32-bit `(a,b)` `Z[φ]` pair. The implementer MUST
add an overflow/representability check and treat violation as a hard fault
(new `ERR_ROTC_RANGE`), never as a silent truncation. This is untested and is
the single most likely place for the primitive to break.

**Candidate space:** 6 × 36 × 3 = 648 proposals, enumerated in a fixed
deterministic order (strut major, then angle, then axis). No randomness.

---

## 4. Step size, convergence, and deterministic cycle budget

- **Step size:** discrete. One catalog angle. There is no continuous step and
  no line search — the arithmetic field admits no "small" rotation.
- **Convergence (accept):** the guard returns `ST_BALANCED` on a proposal.
  Commit and stop.
- **No-progress:** the bounded proposal budget is exhausted without a
  `ST_BALANCED`. Preserve the previous active bank and verdict; surface
  no-progress distinctly from fault (see §5).
- **Proposal budget:** `MAX_PROPOSALS_PER_TXN = 8`, a parameter, default 8.

**Cycle-budget arithmetic — a real constraint, not a formality.** The guard's
existing `VERIFY_WATCHDOG_LIMIT` is 1,000,000 cycles. A controller that tries
N proposals *serially through the same guard* costs up to `N × 1e6` cycles:
at 8 proposals and the 25 MHz `TENSEGRITYLINK` cadence that is **0.32 s of
worst-case wall time per transaction**, and enumerating all 648 would be ~26 s.
Therefore:

- The full 648-candidate space MUST NOT be swept in hardware in one transaction.
- The host selects which ≤8 candidates to try; the FPGA verifies them.
  Search strategy lives on the RP2350, not in fabric.
- A controller-level watchdog `CTRL_WATCHDOG_LIMIT` bounds the whole
  transaction independently of the per-proposal guard watchdog, so a wedged
  guard cannot hang the controller.

---

## 5. Rollback and fault/no-progress surfacing

Reuse the B2 rollback discipline verbatim: malformed, aborted, faulted, or
timed-out proposals preserve the previous active bank and its verdict.

**Wire protocol — additive only.** The eight base-v1 opcodes and the B2/B3
tensegrity pair are frozen; this contract MUST NOT alter them. Add:

| Opcode | Name | Direction | Payload |
|---|---|---|---|
| `0xB4` | TGR1 Propose | write | proposal list (≤8 × 2 bytes) + CRC-8 |
| `0xB5` | TGR1 Controller Status | read | 16 bytes |

`0xB5` byte layout MUST distinguish these outcomes as separate codes — a
controller that cannot tell them apart is not acceptable:

| Code | Meaning |
|---|---|
| 0 | idle, never proposed |
| 1 | accepted — a proposal reached `ST_BALANCED` and committed |
| 2 | no-progress — budget exhausted, all proposals faulted, bank preserved |
| 3 | rejected — proposal list malformed or CRC failure |
| 4 | range fault — `ERR_ROTC_RANGE`, rotation left the representable lattice |
| 5 | controller watchdog timeout |

`0xB5` MUST also report the index of the accepted proposal and the fault code
of the last rejected one, so a host can reconstruct the trajectory.

---

## 6. Oracle fixtures defining successful balancing trajectories

All three MUST be added to `software/lib/tensegrity_balancer.py` +
`software/tests/test_tensegrity_balancer.py`, and MUST be falsifiable
(AGENTS.md §3.5 — no asserting against constants):

1. **Positive trajectory.** Start from `make_tensegrity_six_strut()`, apply a
   known catalog rotation to one strut to break equilibrium, then assert that
   a specific enumerated proposal restores `ST_BALANCED`, and that it is the
   *inverse* rotation. Falsifiable: assert the perturbed state is genuinely
   NOT balanced first, otherwise the test asserts nothing.
2. **No-progress negative.** A perturbation reachable by no single catalog
   rotation. Assert the full 648-candidate enumeration yields zero acceptances
   and the active verdict is preserved unchanged.
3. **Rollback.** A proposal that drives a coordinate out of the 32-bit `Z[φ]`
   range. Assert `ERR_ROTC_RANGE`, previous bank intact, previous verdict intact.

---

## 7. GATE — falsification before any RTL

**This contract authorises Python work only.** Implement §6 fixture 1 first
and answer one question:

> Does *any* single catalog rotation of one strut restore equilibrium from a
> perturbed six-strut state?

- **If yes** — the primitive is viable. Draft the RTL contract, citing the
  fixture.
- **If no** — the single-strut rotation primitive is **falsified**. HALT. Do
  not write RTL. Do not widen the search to multi-strut proposals to rescue it
  without a new contract; that is a different primitive with a different
  actuator count and a different cycle budget.

Committing the negative result is required either way
(`hypothesis-vs-cause-wording-discipline`).

**Cost of this gate:** hours of Python. **Cost of skipping it:** a synthesised
controller whose proposal space provably cannot reach a balanced state.

---

## 8. Invariants (the "Never" list)

- [ ] **Exact arithmetic only.** No floating point; `Z[φ]` and `Q(√3)` only.
- [ ] **Frozen opcodes untouched.** Base-v1 eight, plus B2/B3, unchanged.
- [ ] **No new "balanced" semantics.** The guard is the sole arbiter (§2).
- [ ] **No silent truncation.** Lattice overflow is a fault, never a wrap.
- [ ] **No unbacked silicon claims.** Everything here is `simulation-only`
      until an entry exists in `docs/hardware_evidence.md`. No actuator hardware
      exists, so no actuation claim may be made at all.
- [ ] **Lithic modules.** Any future controller RTL is 50–150 lines; if it
      exceeds that, split proposal generation from transaction management.
- [ ] **No scratch clutter.** No `tmp_*`/`scratch_*`/root `.vcd`.

## 9. Verification commands

```bash
# Python oracle gate (this contract's only authorised work)
python3 software/tests/test_tensegrity_balancer.py

# Scoped regression
TB_FILTER=tensegrity python3 run_all_tests.py

# Full gate before any commit
bash tools/verify_repo.sh
```

## 10. Stop conditions

- §7 gate returns "no" → **HALT**, commit the negative, revise the primitive.
- Lattice overflow found unavoidable for useful rotations → **HALT**, the
  32-bit `(a,b)` ABI is too narrow and that is an ABI contract, not a bug fix.
- Any proposal path found that mutates the active bank before a `ST_BALANCED`
  verdict → **HALT**, transactional integrity is the whole point.


---

## 11. §7 GATE RESULT — 2026-09-04 — PRIMITIVE FALSIFIED

Run against `software/lib/tensegrity_balancer.py` with the **octahedral
rotation group** (24 signed axis permutations, det = +1) — the subset of exact
rotations that is unambiguously representable in the RTL's integer `Z[φ]` ABI.

### Controls (both required, both passed)

| Control | Result |
|---|---|
| Canonical six-strut fixture is `BALANCED` | PASS |
| Perturbations genuinely break balance (non-vacuous) | 20/24 rotations of strut 0 break it |

### The naive gate answer: VIABLE — and it is misleading

Sweeping **all 120 breaking perturbations** (20 per strut × 6 struts) against
the full 144-candidate proposal space (6 struts × 24 rotations):

- **120/120 (100%) recoverable** by a single rotation.
- Exactly **4 restorers** for every perturbation, with no variance.
- **Every restorer acts on the perturbed strut.** No cross-strut compensation
  exists at all.
- Faults seen: 96 `STRUT_INTERSECTION`, 24 `NOT_IN_EQUILIBRIUM`.

### The real answer: the reachable balanced set has exactly one element

"Exactly 4, always" is the order of the stabiliser subgroup of a strut axis,
which is what prompted the decisive test. Enumerating all 144 single rotations
**from the balanced canonical state**:

| Outcome | Count |
|---|---|
| Balanced results | 24 / 144 |
| — identical geometry AND identical node labels | **24** |
| — identical geometry, relabeled endpoints only | 0 |
| — **genuinely new geometry** | **0** |

All 24 balance-preserving rotations are the `C₄` stabiliser of each strut's own
axis — they map the strut onto itself pointwise. **They do not move the
structure at all.**

### Conclusion

The single-strut octahedral-rotation primitive **cannot reach any balanced
configuration other than the canonical one**. Its "100% recovery" is recovery
by not moving. A controller whose reachable set is a single point performs no
control.

- **As a balancing controller: FALSIFIED.** §7 HALT applies. No RTL.
- **As a fault-recovery mechanism: it works**, and that is a real if much
  narrower capability — it provably restores the canonical geometry from any
  single-rotation perturbation. It does not need a proposal search to do so.

### Scope limit — stated, not hidden

This tested the **24-element octahedral group**, not all 36 ROTC catalog
angles. ROTC angles 1–20 are Quadray/thirds operations (`2/3`, `-1/3`
circulant parameters) in tetrahedral coordinates, requiring the Cartesian
bridge. They are exact over `Q(φ)` but are **unlikely to be integral** in the
signed-32-bit `Z[φ]` ABI, i.e. they would likely fail this contract's own
lattice-closure invariant (§3). That is a hypothesis, **not demonstrated** —
it is the named next test if this primitive is to be revived.

Also noted: the Python oracle is built on unbounded exact `Fraction`s, so it
is a `Q(φ)` model and **structurally cannot detect the lattice-overflow
condition** that `ERR_ROTC_RANGE` exists to catch. Any future oracle work must
add an explicit integrality check — one was written for this run and found all
restoring proposals representable.

### What a revived contract would have to change

Do **not** patch this one. A viable primitive must move the structure. The
candidates, in order of how much they preserve of what is already proven:

1. **Multi-strut simultaneous rotation** — different actuator count, different
   cycle budget, different contract.
2. **The full ROTC/IROTC catalog via the Cartesian bridge** — test lattice
   closure *first*; that is the cheap falsification.
3. **Cable rest-length control** — the physically conventional answer, still
   gated on the nonuniform self-stress solver (feasibility item 5).
