# Karatsuba production-swap criteria — pre-registered

**Written 2026-08-08 at 17/40 builds complete**, with the whole LINK arm and
four PROBE candidate builds still unseen. Recorded before the data exists so
the bar cannot be fitted to the result. Same principle as the capture
contract's `gates.failure_policy`.

Decision this governs: whether `USE_ZPHI_KARATSUBA` may become the production
default in the tensegrity consumers, currently plumbed but default-off.

## Correction to this document's premise — 2026-08-09

**The swap already happened.** This document was written believing the
candidate was "plumbed but default-off" and that the criteria governed a future
decision. They do not. `c1fe58f` (2026-07-23, *"switch tensegrity production
default to Karatsuba candidate"*) set `USE_ZPHI_KARATSUBA = 1` as the parameter
default in all three consumers, and `build_a7.sh:167` defaults
`ZPHI_KARATSUBA=1`, passing `-chparam` at synthesis — which overrides the board
tops' `parameter USE_ZPHI_KARATSUBA = 0`. **Any ordinary build has shipped the
candidate for the last sixteen days.**

**The criteria below are unchanged** — amending them after seeing results is
prohibited by this document's own failure policy, and nothing here is amended.
What changes is their function: they are no longer a gate on a future swap,
they are the **evidence standard for an already-shipped default**. That makes
an unmet criterion more urgent, not less.

## Status against the criteria — 2026-08-09

| # | Criterion | Status |
|---|---|---|
| 1 | Timing: every candidate build meets 25 MHz | **MET** — 40-run sweep, worst LINK candidate 31.46 MHz (+6.46) |
| 2 | Routing reliability within +1 of reference | **MET at the limit** — PROBE 1 non-convergence vs 0; LINK 0 vs 0 |
| 3 | Area: LUTX ≤ +1 %, FFX ≤ ref, DSP equal | **MET** — LINK +32 (+0.13 %), PROBE −44, both −176 FFX, DSP ±0 |
| 4 | Formal + regression at the swap commit | **MET 2026-08-09** at `a6e462d` — the swap tree is master. All three SymbiYosys tasks PASS, `spu13_zphi` 46/46, tensegrity 48/48 |
| 5 | Four-act bench, N ≥ 10 + positive control | **MET 2026-08-09** — 10/10 runs, zero deviations, `hardware_evidence.md` §3.2l.1 |

Criterion 4's clause *"passing today does not count"* assumed the flipped tree
did not yet exist. It has existed since 07-23, so HEAD **is** the swap tree and
the re-run is valid.

## All five criteria are now met — 2026-08-09

**The Karatsuba candidate, shipping as the production default since
2026-07-23, has a complete evidence chain as of 2026-08-09.** Nothing in this
document was amended after seeing results; criteria 1-3 were met by the
2026-08-08 P&R sweep, 4 by the formal/regression re-run at `a6e462d`, and 5 by
the four-act bench recorded in `hardware_evidence.md` §3.2l.1.

The history below is retained because it explains why criterion 5 sat unmet for
sixteen days.

## Criterion 5 — the blocker was removed five days ago and nobody noticed

`hardware_evidence.md` §3.2l already carries a **Karatsuba-candidate-as-default
silicon confirmation** dated 2026-07-24, one day after the flip: build
`8aaaeaa`, `ZPHI_KARATSUBA=1 A7_SEED=2 A7_FREQ=25`, bitstream SHA-256
`07c979da…`, UART returning `TGR:P V:7 E:00` 200 times over 15 s with zero
variance. That closes the **standalone `TENSEGRITYPROBE`** half.

The same entry states the `TENSEGRITYLINK` half — full transactional
admission, mechanical-negative, corrupt-payload rollback, recovery, i.e.
exactly criterion 5's four acts — **"remains open, gated on the power-ready
interlock."**

**That gate no longer exists.** The interlock was superseded on 2026-08-04 and
reaffirmed on 2026-08-07: the backfeed damage class is mitigated by the 100 Ω
series resistors on all four SPI lines plus power-sequencing discipline, and
the interlock is explicitly *"not a current purchase and does not gate
anything"* (`BENCH_BOM.md` §2).

So the four-act bench is **unblocked and has been since 2026-08-04**. It is not
future work for a hypothetical swap; it is the missing evidence for the
configuration already shipping. Note also that §3.2l's standalone confirmation
is a **single build at one seed** — sound for what it claims, but below the
N ≥ 10 plus positive-control standard adopted after the 2026-08-04/05
retractions, which criterion 5 requires.

## What this sweep can and cannot decide

**Can:** whether the candidate holds the 25 MHz `guard_clk` constraint across
seeds on both spins; what it costs in LUTX/FFX/DSP; whether it routes as
reliably as the reference.

**Cannot:** whether the candidate is faster. Seed spread is ~9 MHz against an
arm median difference of ~1.6 MHz. No n we can afford resolves that, and no
Fmax superiority claim may be made from this sweep in either direction. This
is stated *before* the numbers, not as an excuse afterwards.

## Criteria — all must hold

1. **Timing.** Every candidate build that routes meets the 25 MHz constraint
   with `status: PASS`, on both spins, at every seed. A single candidate build
   below constraint fails the gate outright.

2. **Routing reliability.** Non-converging or failed builds in the candidate
   arm exceed the reference arm by **at most 1** per spin. Rationale: the
   reference arm is already producing 60+ minute routes and at least one
   apparent non-convergence, so routing difficulty is a property of this design
   under nextpnr, not of the multiplier. The gate is *relative*, not absolute.

   **Settled 2026-08-08 (John): a non-converging seed does not block the swap.**
   It is recorded as what it is — a seed that did not route within the sweep —
   and the cell reports the n that did. It does not become a hidden pass
   either: any non-convergence is stated wherever the distributions are
   quoted, because silently dropping the hard cases is how a sweep flatters
   itself.

3. **Area.** Candidate LUTX ≤ reference + 1 %; candidate FFX ≤ reference;
   DSP48E1 exactly equal. The 8-DSP standalone result means any DSP delta at
   top level indicates something other than the intended substitution.

4. **Equivalence unchanged.** At the swap commit, re-run and pass: all three
   SymbiYosys tasks (`small`, `width_plumbing`, `reset_semantics`) and the
   `spu13_zphi` regression. Passing today does not count; they are re-run
   against the tree that flips the default.

5. **Board evidence before the default flips — the full four-act bar.**
   *Settled 2026-08-08 (John).* Simulation and P&R are not sufficient. Required:
   a Wukong bench run with the candidate default-on reproducing the
   TENSEGRITYLINK four-act sequence — admission, mechanical negative,
   corrupt-payload rollback, recovery — bit-identically, to the standard set by
   the 2026-07-19 closure (`a930326`). Per bench-evidence discipline:
   **N ≥ 10 runs and a positive control**, not a single pass.

   The lighter liveness probe was considered and rejected. The formal proof
   covers the multiplier in isolation; it says nothing about the sidecar around
   it, which is exactly where an integration defect would live. This costs a
   bench session and is worth it.

## Failure policy

If any criterion fails, the swap does not happen and the criteria are **not**
amended to accommodate the result. A criterion may only be corrected if it is
shown to be internally unsatisfiable — the standard the v2 capture contract
met — and any such correction is recorded with its rationale before rerunning.

## Explicitly out of scope

- Any claim that the candidate is faster or slower in Fmax.
- Any claim about 50 MHz operation; the constraint under test is 25 MHz.
- Extending the result to non-tensegrity consumers. Only the tensegrity
  consumers and the sidecar are plumbed and measured.

## Open — none

Both judgement calls were settled by John on 2026-08-08, **before any of the
LINK data was seen**: the full four-act bench bar stands (criterion 5), and a
non-converging seed does not block (criterion 2). Nothing in this document is
now awaiting a decision, which is the point — the gate is complete and fixed
before the result exists.
