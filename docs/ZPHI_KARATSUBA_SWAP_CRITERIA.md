# Karatsuba production-swap criteria — pre-registered

**Written 2026-08-08 at 17/40 builds complete**, with the whole LINK arm and
four PROBE candidate builds still unseen. Recorded before the data exists so
the bar cannot be fitted to the result. Same principle as the capture
contract's `gates.failure_policy`.

Decision this governs: whether `USE_ZPHI_KARATSUBA` may become the production
default in the tensegrity consumers, currently plumbed but default-off.

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
