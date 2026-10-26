# Scoping Note: Compile-Time Placement Implications (priority item #2)

**Date:** 2026-08-24
**Status:** SCOPED AND EVALUATED. **Nothing to authorize — the item's
own stated precondition is not met, and its core question is already
answered.** No simulation, analysis script, or code change was run to
produce this note; it is a review of what today's four documents already
established, checked against what this item asked for.

**Origin:** `docs/PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md`'s
post-synthesis priority order (2026-08-24): *"2. Compile-time placement
implications — potentially useful once architecture constraints are
clearer; secondary to #1."* Its precondition, stated then, was explicit:
this item becomes worth revisiting **once architecture constraints are
clearer** — not on a fixed schedule, not just because #1 finished.

## 1. The core question was already answered, three times, before today's other work

`greedy_place`/`optimal_placement` choose REGEN boundaries from the
**noiseless** `m0` trajectory — computed before any noise is drawn,
structurally before a stochastic per-trial `R_i` exists. This makes
E18–E21's correlation finding, and the corrected-reliability-model's
result, both **irrelevant to placement's own algorithm**, independent of
how interesting either finding is on its own terms:

- `PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md` §5.2 (2026-08-24, written
  before today's session): "no change needed."
- `PHOTONIC_REGEN_COMPILATION_CONTRACT.md` §2 (this session): restates
  it as the standing rule — "placement optimizes the existing
  conservative objective... not how placement chooses boundaries."
- `PHOTONIC_SPU13_ARCHITECTURE_SPEC.md` §2/§6 (this session): confirms
  again, and extends the non-goal explicitly to this document too ("no
  modification to... `spu13_regen.v`... this document describes a
  hypothetical occupant of an existing slot, it does not propose
  changing the slot").

**This is not this note discovering the answer — it's confirming the
same conclusion has now been independently reached three separate
times, by three documents with different scopes, and never once
contradicted.** That consistency is itself evidence the conclusion is
solid, not an accident of one document's framing.

## 2. Checking the item's actual precondition: did today's work make architecture constraints clearer *in the load-bearing sense*?

Today's session did produce two new documents
(`PHOTONIC_REGEN_COMPILATION_CONTRACT.md`,
`PHOTONIC_SPU13_ARCHITECTURE_SPEC.md`) that make the architecture
picture **clearer as documentation** — consolidating scattered facts,
adding the four-tier `[ESTABLISHED]`/`[SIM]`/`[UNRESOLVED]`/`[NOT
CLAIMED]` labeling, fixing the `knowledge/isa_reference.md` gap. But
checking specifically for **new decided physical parameters that a
placement algorithm could actually use** — the only kind of "clearer"
that would matter here — the answer is no:

- Physical channel count / multiplexing strategy: **[UNRESOLVED]**
  before today, **[UNRESOLVED]** after (architecture spec §4) —
  explicitly surfaced, not decided.
- Timing/latency: **[NOT CLAIMED]** before, **[NOT CLAIMED]** after —
  explicitly omitted rather than estimated.
- The RTL backend interface (`bk_qr*_meas`, etc.) is now documented
  clearly, but it was already real and already unchanged by any of
  today's work — documenting an existing interface isn't a new
  constraint.

**The precondition — "architecture constraints are clearer" — has been
met only in the documentation sense, not in the decided-parameter sense
the item actually needs.** There is no new number, no new physical
decision, nothing a placement algorithm could incorporate that didn't
already exist before today. Revisiting placement algorithm design now
would mean speculating about a physical architecture that's still
explicitly open (§4's channel-count question) — exactly the kind of
premature, evidence-free move this whole branch's discipline exists to
prevent.

## 3. The adjacent, genuinely distinct question — not this item's job

`PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md` §5.3 named a real, different
idea: a future op_i-aware compile-time scheduling heuristic (apply extra
caution before a REGEN boundary specifically following a `ROTC_thirds`
op, since E20/E21 found a small, real, but mechanistically unexplained
effect there). This is **priority item #3 territory** (the two parked
E18–E21 mechanism hypotheses), not item #2 — conflating them would blur
two separately-parked things into one. It stays parked for the same
reason it already was: "the mechanism is unexplained... not a safe basis
for a general design rule" (synthesis doc §5.3), and nothing produced
today changes that either.

## 4. Verdict

**Nothing to authorize under "compile-time placement implications."**
The item's core question was answered before today and reconfirmed
three times since; its stated precondition for revisiting isn't met in
the sense that matters (no new decided physical parameter exists to
derive an implication from); and the one adjacent idea that *would* be
a genuine placement change (op_i-aware scheduling) belongs to a
different, already-parked item. **This item is closed, not deferred** —
it doesn't need to stay on a "check again later" list; it needs the
physical architecture question (§4's channel/multiplexing decision,
itself unauthorized and unblocking) to actually get decided first, and
that's a precondition on a precondition, not a task.

## References

- `docs/PHOTONIC_REGEN_CORRELATION_SYNTHESIS.md` §5.2/§5.3 — origin of
  both the "no change needed" conclusion and the op_i-heuristic idea.
- `docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` §2 — the standing rule
  this note reconfirms rather than re-derives.
- `docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md` §4/§6 — confirms the
  physical-parameter precondition remains unmet.
