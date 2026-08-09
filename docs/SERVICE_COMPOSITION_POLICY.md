# Service composition and cross-domain adapter policy

**Status: adopted 2026-08-09**, with §7 settled by the project owner. Satisfies the first
of the two preconditions in `CURRENT_STATUS.md` § *Service Composition Boundary*;
the oracle-backed composition trace (§5) remains outstanding — so shared
datapaths stay deferred, exactly as that section requires.

Normative companions, unchanged by this document:
[`SOM1_RESULT_FRAME.md`](SOM1_RESULT_FRAME.md),
[`SOM_V1_PRODUCT_CONTRACT.md`](SOM_V1_PRODUCT_CONTRACT.md),
[`SPU13_IDENTITY_AND_BOUNDARIES.md`](SPU13_IDENTITY_AND_BOUNDARIES.md).

## 1. The central rule: compose verdicts, not values

**Cross-domain composition happens at the predicate level, not the numeric
level.** An algebra service emits a verdict — a bounded, dimensionless symbol —
and it is the *verdict* that composes with a decision. Its internal field
values never cross a domain boundary.

This is not a stylistic preference. The three domains are genuinely different
rings:

| Service | Domain | Representation |
|---|---|---|
| **SOM1** — decision | `Q(√3)` | quadrance packed `{P[31:0], Q[31:0]}`, exact ordering |
| **PHSLK / Lucas** — coherence | `Z[φ]/L_p` (p = 521) | phinary pair, cross-multiplication predicate |
| **RPLU / Padé** — approximant | `A₃₁` over M31 | basis `[1, √3, √5, √15]` |

A quadrance is not a phinary value and there is no meaning-preserving map
between them. Converting one to the other produces a number that is arithmetic
nonsense however carefully it is rounded — and since every field here is exact,
such a conversion would be the **only** lossy step in the entire pipeline. The
project's whole claim is exactness; an implicit adapter would quietly destroy
it at the one place nobody was looking.

**Consequence: for the compositions currently contemplated, no adapter is
needed at all.** A verdict crossing a boundary needs no encoding conversion,
no range analysis, no rounding policy. The adapter contract in §4 exists for
the case that is *not* yet contemplated, and binds if anyone reaches for it.

## 2. What each service may and may not assert

**SOM1 — the decision service.** Emits the winning node, runner-up, class
label, and exact `Q(√3)` quadrances with their component-wise gap, in the fixed
52-byte v1 frame. **SOM1 alone selects.** Its BMU evidence is the decision
record.

**PHSLK — a coherence predicate.** Answers one question: are two rational
phases equal by cross multiplication? It is **not** a total order, not a
distance, not a confidence, and not a substitute for BMU selection. It cannot
rank two candidates, because a predicate that returns coherent/incoherent has
no ordering to give. Any design that uses PHSLK output to *choose* between SOM
nodes is outside this policy.

**RPLU / Padé — an approximant service.** Evaluates Padé approximants over
`A₃₁` within its declared domain, with defined singularity behaviour. It
answers questions about functions, not about which cluster a sample belongs to.

## 3. The composition rule

In any composed decision:

1. **BMU evidence is unchanged.** The SOM1 frame is emitted exactly as the
   classifier produced it, byte for byte, CRC included. A composed pipeline may
   not edit, suppress, or recompute it.
2. **An algebra verdict may only annotate.** It travels *alongside* the SOM1
   frame, never inside it — the v1 layout is fixed at 52 bytes and adding a
   field would break the ABI every consumer is written against.
3. **The annotation drives an explicit policy**, and the policy is the only
   place the two are combined:

   | Outcome | Meaning |
   |---|---|
   | `accept` | BMU decision stands, algebra verdict concurs |
   | `hold` | BMU decision stands but is not acted on; annotation dissents |
   | `escalate` | referred outward; the coprocessor asserts nothing further |

4. **The incumbent controller retains authority.** `hold` and `escalate` are
   advisory outputs. This device supplies evidence; it does not actuate.

**Why annotation rather than fusion.** Fusing a coherence verdict into the BMU
score would make the decision unreplayable: you could no longer reconstruct
what the classifier saw from what the device output. Replayability is the
product claim. Keeping them separable costs a few bytes of frame and preserves
the thing being sold.

## 4. Adapter contract — binds if anyone crosses domains numerically

Any adapter that converts values between `Q(√3)`, `Z[φ]/L_p` and `A₃₁` must
state, in its own document, before implementation:

1. **Encoding** — exact input and output representations, bit layouts included.
2. **Range** — the input domain over which the mapping is defined, and what
   happens outside it.
3. **Error and singularity behaviour** — exactly-representable cases,
   inexact cases (if any exist, the adapter is lossy and must say so in these
   words), poles, and zero divisors.
4. **Latency** — cycle cost, and whether it is fixed. A variable-latency
   adapter in a fixed-latency pipeline is a design change, not a detail.
5. **Oracle** — a software reference the RTL must match bit-exactly, with
   golden vectors, in the style of the existing `software/lib` oracles.

An adapter lacking any of the five is not approved, however obviously correct
it looks. **No implicit conversion is permitted anywhere** — an adapter is
always an explicit, named, separately-verified component.

## 5. Oracle-backed composition trace

The second precondition for shared datapaths. A trace is a recorded run
demonstrating that composition preserves both services' semantics:

- a sequence of inputs producing a known mix of `accept`, `hold` and
  `escalate` — all three must appear, or the policy is untested;
- for each step: the **verbatim** SOM1 frame, the algebra verdict, and the
  resulting outcome;
- a software oracle producing the same outcome sequence bit-exactly from the
  same inputs;
- explicit demonstration that the SOM1 frames are byte-identical to those the
  classifier emits when run **without** composition — this is the check that
  rule 3.1 actually holds;
- the negative case: an input where the algebra verdict dissents and the BMU
  decision is nonetheless preserved intact in the record.

Absent this trace, "composed decision" is a design intention, not a capability,
and must not appear in public material as the latter.

## 6. Shared datapaths — still deferred, and why

Sharing multipliers or storage between services is an *optimisation*. It can
only be evaluated once the policy above is implemented and traced, because
sharing changes failure modes: a fault in a shared unit becomes correlated
across services that the policy assumes are independent. Evaluate in this
order — policy, trace, then sharing — and never the reverse.

The SU3SHARE precedent is instructive: one M31 multiplier shared between the
SU3 sidecar and the RPLU2 config/QR path, proven on one bitstream with both
paths passing (`hardware_evidence.md` §3.2e.5). That is the standard — sharing
is legitimate when both sharers are independently proven **and** the shared
configuration is proven as its own artifact.

## 7. Settled decisions — 2026-08-09 (John)

**1. Annotation transport: a separate frame**, keyed on the SOM1
`result generation` field. Separate claims stay separate: two outputs derived
from different calculations over different scopes should not be conflated into
one framed assertion just because a host would find a single blob convenient.
The v1 SOM1 ABI is untouched, and each frame can be versioned on its own
schedule.

**2. Thresholds are FIXED IN RTL, not host-configurable.** *(This overrides the
draft's recommendation.)* The accept/hold/escalate boundaries are not
negotiable per deployment. Consequences, accepted deliberately:

- The policy is **auditable from the bitstream**. What a device does is a
  property of the artifact and its hash, not of whatever configuration a host
  happened to push — which is exactly the property that makes a replay claim
  meaningful.
- Threshold state stays **out of the replay contract**. Nothing needs recording
  in every trace, and two traces from the same bitstream are directly
  comparable with no configuration caveat.
- **Changing a threshold requires a rebuild and re-proof.** That is the real
  cost and it is accepted: a threshold change *is* a claim change, and it
  should cost what a claim change costs. A configurable threshold would let the
  device's behaviour drift without any evidence artifact recording that it had.

**3. `hold` and `escalate` remain distinct in v1.** Collapsing two outcomes
later is cheap; splitting an outcome that consumers have already been written
against is not.

## 8. What this policy does not do

It does not authorise a composed product claim. It defines how composition
*would* work and what evidence would license it. Until the §5 trace exists,
"composed decision" is a design intention, and public material must say so.
