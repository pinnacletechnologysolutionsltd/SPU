# QCG-0 P0 execution contract (draft, revision 3.2.2, owner dispositions recorded, for independent review)

Date: 2026-10-23. Status: **DRAFT. Preparation only. Freeze, implementation and execution remain HOLD.**
Author: Claude. Revision 3 responds to the second independent review (`P0_CONTRACT_R2_REVIEW_CERTIFICATE.md`, REVISE).
Revision 2 had SHA-256 `4c95617479b858919c86ad5be3cedad37fb9e547f88b9c6d9a8764e8b083e54f`; revision 1 `21fb45af84d609c3c127010a10b0c2824aaac4772ab8d95a4abd9f5d8d2b8bfc`.
No fixture was regenerated, no model was run, no benchmark was performed; no unrelated campaign or hardware was touched.
**Revision 3.2.2 (2026-10-23) is a single narrow amendment to Revision 3.2.1 (SHA-256 `1f8aca9f088ffbaafb002ba5cffde7bdee7b33fdfcf18dcf20dec16202b8cf2f`,
independent PASS): §3 gains the paragraph "Dependent requests after a refusal", with consequential one-sentence edits to §2 (comparator eligibility), §5 (sequential
scheduling), §8 (X-15) and §9 (artifacts). No algorithm, reference, workload, comparator rule, cost definition, guard or threshold changed. It is not independently
reviewed until a reviewer accepts it.** **Revision 3.2.1 (2026-10-23) additionally closes the single defect the Revision 3.2 review left (finalization wrote the marker after a failed required
metadata write); Revision 3.2 (`94e6631a48f4f362c310e72954af66b2853d477fbff8674cf555ff9064e44602`) responded to the Revision 3.1 review (`P0_CONTRACT_R3_REVIEW_CERTIFICATE.md`, REVISE; B1–B4): C2 tape-specific read
steps and jet evolution, the FDINIT table traversal, mandatory OUTPUT_CAP attribution, and a bounded single finalization path; plus two
stale-text removals. Revision 3.1 (SHA-256 `2829a167eabb3bcc16a5beed35249ce91f5097de0f7934647e0f7676b474ee44`) recorded the owner's
dispositions of D-1…D-6 (§11): all ACCEPT, with the scopes stated there, and those dispositions are unchanged. No algorithm count, reference
or checklist item other than the four named corrections changed. Revision 3 had SHA-256
`d6f27aae3328814b67b8c10da2e916b2f3943dbffa9416f97aa4e629243e7989`.** Acceptance is not authorization: freeze, implementation and
execution remain HOLD.

## 0. Pins and precedence

    eade4b5f0957c3679c94b67d8f4b1f6b6d005d65316a5337e6c8dfb9370b98dd  research/qcg_0/QCG0_PREREGISTRATION.md (Revision 3.1)
    86f95968b76ff8fa00fd4a763759b876cb95348014e7fa292f5368c412329523  research/qcg_0/P0_CONTRACT_REVIEW_CERTIFICATE.md
    4ad13a33cc04d6277c61ca6897af4dd2933e1017e384e20b0814826919ecb8ca  research/qcg_0/P0_CONTRACT_REVIEW_EXPECTATIONS.json
    314318c9eb441762c0df323b95f09a64c99e696a6446944a5b9ca6198ef44c93  research/qcg_0/P0_CONTRACT_REVIEW_MANIFEST.json
    95ccad35939af6f01a00619aabe8f3f3d7da30a972985cd1db7a761f1058d946  research/qcg_0/P0_CONTRACT_REVIEW_AUTHORIZATION.md
    8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34  research/qcg_0/QUINTIC_FIXTURE_VALUES.json
    a66af3d68da5a7dba439818778af9e8fe70244e3dc2d8250ea891354124a0b46  research/qcg_0/REVISION2_FIXTURE_VALUES.json

    027f6a372d83a3bb1bb147dcf162f72e5b174eeeb6efb3a44d44c0bed5f9ecb8  research/qcg_0/P0_CONTRACT_R2_REVIEW_CERTIFICATE.md
    2b3d38fc91b053ba393b9e7ef547e9725f5ac6d3a74411a25de2e5f78d361ebe  research/qcg_0/P0_CONTRACT_R2_REVIEW_MANIFEST.json
    9422d7617c65a9a3fc2fa1ab19af7ce7ea634721cfeb251096cd3821534237a0  research/qcg_0/P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json
    093b006b4b11e289066265a9021fba92c28ec252b8df44eac06a48f8eeca75bb  research/qcg_0/P0_CONTRACT_R2_LEDGER_STAGE_EXPECTATIONS.json
    d231a81305f975727b82431bb04a51dff41fbc55a85708a8521c63c36edf6a0a  research/qcg_0/P0_CONTRACT_R2_REMAINING_CELL_A_STAGE_EXPECTATIONS.json
    995f9c76e4c542ed013920b0db69336e76718dc4bb1f76dbee4dfaa48da0ea24  research/qcg_0/P0_CONTRACT_R2_REVIEW_AUTHORIZATION.md

All earlier pins (certificates, manifests, packet, Revision 3 review) are in pre-registration §0.2 and unchanged. Where this
contract and the pre-registration differ, the contract governs **measurement procedure only**; mathematics stays with the
pre-registration. The reviewer's four query hand counts (28/27, 26/23, 21/18, 33/31) are accepted as correct for the displayed
routes.

## 1. Findings carried from preparing and reviewing the contract

1. The 28/27 count is B-Horner (all polynomials cached in power basis); the 26/23 count is the factored route of B-PH and C1.
2. Under the frozen algorithms C1 performs B-PH's operations in Cell A and PHFD's in the sequential control (**accepted
   as a conformance control, owner D-1**). P0 can then report equivalence there but not a candidate-specific arithmetic advantage;
   Cell B is where C1 differs.
3. FD is `NOT_APPLICABLE` in Cell A (**accepted P0 scope, owner D-2**; this is a chosen policy, not a claim that no
   random-access finite-difference method exists).
4. *Conditional prediction (not a result):* if the preparation program of §5 is adopted, B-PH's total-view shift count over a
   16-query tape exceeds B-Horner's (author's analytic P-phase cross-check in §7: B-Horner 8 shifts in P and 0 per query, B-PH
   5 in P and 2 per query), so B-PH could not be a strict Pareto win against B-Horner. This depends on §2's accepted accounting convention (owner D-3).
5. Revision 2's defects were accepted (division width, aggregation, status grammar, reference mapping): the reviewer certified the
   numerical model, the preparation counts and, for all six Cell A arithmetic arms, the first W31 refusal (§8 X-15). Revision 3
   closes the remaining blockers: sequential request subsets and nested-primitive event identities (§5), the administrative
   versus semantic K distinction (§2), a deadline protocol whose TIMEOUT is attested by the supervising `timeout` itself (§9),
   a checksum-only pins file with a separate tool manifest and an enforced output cap (§9), and the adoption of the P-1
   references (§4).

## 2. Operation ledger (accounting convention; accepted by the owner as D-3/D-4/D-5, scopes in §11)

All arithmetic is in one instrumented exact rational class `Q`: canonical form (reduced numerator `n`, positive denominator
`d`, zero as 0/1) after **every** operation. Every arm, phase and conformance test uses the same class and rules. No data-dependent
short-circuit exists: multiplying by 0 or 1, adding 0, or skipping zero coefficients all still count. `bn(x)` and `bd(x)` are
the bit-lengths of |numerator| and of the denominator, with `bn(0) = bd(0) = 1` everywhere (W, G, T).

**Raw products and the W proxy (one rule, no fallback).** Each operation forms the following integer values; "raw size" is the
bit-length of the largest of them. `W_bits` adds, per M/A/D/K operation, the schoolbook proxy of its integer products:

| Op | Integer products formed (raw values) | W_bits proxy |
|---|---|---|
| M a·b | n_a·n_b, d_a·d_b | bn(a)bn(b) + bd(a)bd(b) |
| A a±b | n_a·d_b, n_b·d_a, their sum or difference, d_a·d_b | bn(a)bd(b) + bn(b)bd(a) + bd(a)bd(b) |
| D a÷b (b≠0) | n_a·d_b, d_a·n_b (sign moved to the numerator) | bn(a)bd(b) + bd(a)bn(b) |
| K compare a?b (two rationals, semantic) | n_a·d_b, n_b·d_a | bn(a)bd(b) + bn(b)bd(a) |
| K sign or zero test against 0 (semantic) | none | 0 |
| S ×2 or ÷2 (literal) | none (parity normalization: if the relevant half is even halve it, otherwise double the other part) | 0 |

**Categories.**

| Category | Counts | Rule |
|---|---|---|
| **M** | multiplications | any multiplication that is not the literal ×2 or ×½ of the algorithm text (squares included) |
| **A** | additions and subtractions | a negation is free and uncounted in every arm |
| **S** | shifts | exactly the **literal constants 2 and ½ written in this contract's algorithm text**, cost 1, no gcd |
| **D** | divisions | any division other than literal ÷2; integer divisors (3, 4, 5, …) and values that happen to equal 2 are D |
| **K** | semantic comparisons | each comparison or sign/zero test **named in the algorithm text** (the `ok` flags, `φ′ ≥ 0`, join predicates, regularity tests) counts 1, whether or not it forms products. **Administrative checks are not K and are not counted anywhere:** the zero-divisor guard inside D, the parity test inside S, import and width/bound checks, declared-degree assertions and oracle-side assertions. They may raise a status (`INVALID`, `REFUSED`) but add no ledger entry. Hence preparation has K = 0 even though it performs divisions. |
| **G** | normalization | every M, A and D invokes exactly one gcd on the raw numerator and raw denominator (no integer shortcut). `G_calls` counts invocations; `G_bits` sums, per call, the larger raw bit-length of the two arguments. Shifts and K invoke none. |
| **W** | widths | `W_bits` (additive, above); `W_peak_raw` = largest raw size over all events; `W_peak_red` = largest reduced numerator or denominator stored or formed, **including imported inputs**. |
| **T** | storage | `T_ret_peak` = maximum, over the observation points "end of P" and "after each completed Q request", of the retained-state bits: Σ over distinct retained rational objects of (bn + bd + 1 sign bit). Scratch (per-query temporaries, TSHIFT copies, copies of coefficient lists) is **excluded**; an object counts once only where §5 declares an alias (for example D_κ is the σ² object), otherwise every stored rational counts separately. |
| **L** | live scalars | `L_peak` = largest number of simultaneously live rationals (retained + scratch). A rational is live from the step that creates it until the last step, in the written program order, that reads it; retained objects never die; an assignment ends the previous value's life. Reported, not guarded. |
| **M2** | informational | M operations whose multiplier *value* is a power of two (2, ½, 4, 1/16, …). Reported only. |

**Classification rule (do values equal to 2 or ½ qualify?)** No. S depends only on the literal constant in the algorithm text.
A multiplier that merely **evaluates** to 2 or ½ (the parameter t = ½, a coefficient equal to 2, the step 1/16) is M or D.
A constant that comes from an index, a binomial or the degree is M or D whatever its value (`÷(i+1)` is D, `i·a_i` is M).
Applied identically to every arm.

**Phases and aggregation.** Every operation carries a phase tag, **P** (preparation, before the first query) or **Q**. The
*total view* of an additive category is P + Q; of a peak category (`W_peak_*`, `T_ret_peak`, `L_peak`) it is the maximum over
P and Q (with imports counted in P); `T_ret_peak` already ranges over all observation points. The *query view* is Q only, per
request. Both are reported. Phase attribution reconciles by type (LU-P in §7).

**Guard set G\*** (all must be ≤ the comparator in the total view): M, A, S, D, K, G_calls, G_bits, W_bits, W_peak_red,
W_peak_raw, T_ret_peak. **Trigger set Tr** (a ≥ 20% reduction in one, with G\* satisfied, raises the exploratory signal): M, A,
D, K, T_ret_peak, W_peak_red. **S is guarded and not a trigger.** A lower T_ret_peak bought with higher M or A is a TRADE-OFF.

**Comparator (accepted deterministic ranking, owner D-4; not a claim that a componentwise best exists).** Eligible comparators are
conventional arms with status OK on every matched request (never `REFUSED`, `NOT_APPLICABLE`, `PREPARATION_REFUSED` or `NOT_ISSUED` (§3, Revision 3.2.2)). The
comparator is the eligible arm lexicographically smallest on (M, A, D, K, T_ret_peak, W_peak_red) in the total view; ties are
broken by arm id in ascending ASCII order. The per-category virtual best over eligible arms is the secondary view.
Categories are never summed.

**Sharing metric (registered in pre-registration §11).** `J_c/Σ_c` needs executable standalone routes and per-group
preparation dependencies that this contract does not define. **DEFERRED to a follow-on contract (owner D-6, accepted).** P0 then
reports the per-arm total-view ledgers only and makes no sharing claim. A later sharing experiment needs its own reviewed dependency table per arm and a separate authorization.

## 3. Arithmetic, width, refusal and attempt accounting

* **Profiles.** All bounds are on bit-length of the magnitude. P4096: reduced ≤ 4096 bits, raw ≤ 16384 bits. W31 (control):
  reduced ≤ 31 bits and raw ≤ 63 bits, which is exactly the pre-registration's "reduced ≤ 2³¹−1, raw ≤ 2⁶³−1" in magnitude.
* **Imports.** Before preparation each source or constant rational is checked against the reduced bound in the arm's import
  order (source U then V ascending coefficients, then φ for Cell B, then the constant weights of §5 in order of first use).
  A failure is `ARITH_LIMIT` at event `arm.P.import.<name>.<i>`.
* **Event id.** `arm.phase[.qNN].step.k[.sub]`: `qNN` the 0-based position in the frozen tape, `step` the named step of §5
  (P-steps `P1…`, Q-steps as labelled), `k` the 1-based index of the Q operation within that step's primitive in the frozen
  loop order, `sub` the sub-check below. This identifies repeated helper calls uniquely **within a declared route context**
  (profile, curve, tape or cell, arm, request or sample). An event string such as `q03.a8.1.e1` is never compared across contexts;
  every derived or reported stage carries its outer identifiers.
* **Sub-check order inside an operation** (the first failing one is the refusal point; "raw" compares against the raw bound,
  "red" against the reduced bound): M: r1 = n_a·n_b, r2 = d_a·d_b, gcd, e1 reduced n, e2 reduced d. A: r1 = n_a·d_b,
  r2 = n_b·d_a, r3 = r1 ± r2, r4 = d_a·d_b, gcd, e1, e2. D: zero test first (n_b = 0 → `INVALID(DIV_ZERO)`, no sizes
  examined), r1 = n_a·d_b, r2 = d_a·n_b, gcd, e1, e2. S: e1, e2 of the result. K (two rationals): r1 = n_a·d_b, r2 = n_b·d_a.
  Cancellation does not rescue an oversized product.
* **Request granularity.** A *request* is the atomic unit: Cell A one request per query; Cell B one per τ; sequential one per
  sample; S4 stationary controls three separate requests `DIRECTION`, `TANGENT`, `CURVATURE`; φ_bad three: `ORIENTED_LENGTH`
  (returns B(t), exact single polynomial), `ACCUMULATED_LENGTH` (single-polynomial class, refuses `OUT_OF_DOMAIN`),
  `PIECEWISE_LENGTH` (piecewise class, exact: B on [0,½], 8/3 − B on [½,1]); S5/S6 one per chain sample or per predicate.
* **Status grammar (exhaustive).** `status ∈ {OK, REFUSED, INVALID, NOT_APPLICABLE}`. REFUSED carries one code from
  {`ARITH_LIMIT`(event id), `NONMONOTONE`, `NONREGULAR`, `OUT_OF_DOMAIN`, `NOT_PRIMITIVE_RETIMING`, `APPROX_NOT_EXACT`}; INVALID
  one from {`DIV_ZERO`, `MALFORMED`}. A refusal in phase P marks the arm `PREPARATION_REFUSED(<REFUSED code and event id>)`: no
  request is issued to it. Every (arm, request) yields exactly one status. `NOT_APPLICABLE` is a status, never a refusal code.
  APPROX/E2 use (`REFUSED`, `APPROX_NOT_EXACT`) when an exactness-claiming request is made of an E2 object.
* **Atomicity and evidence.** *Committed state* (retained lists, caches, results) is changed only by an OK request or a
  completed preparation. A refused request returns no values and leaves committed state bit-identical (checked by a state
  hash before and after, then by a known admissible request whose output and ledger equal those of a fresh run, then by a
  repeat of the refused request giving the same refusal). *Diagnostic evidence* is append-only and never rolled back: the
  attempt ledger records the status, the event id and the operations the attempt consumed. Comparative ledgers (§2) count
  only OK requests and completed preparations; attempts are reported separately. Global resource counters (operations,
  wall time, output bytes) never reset on a refusal, a warm-up or a timed repeat.
* **Dependent requests after a refusal (Revision 3.2.2).** *Issued* requests receive exactly one status from the grammar above. A request that is
  **not issued** receives the *scheduling outcome* `NOT_ISSUED(STATE_DEPENDENT_AFTER_REFUSAL)`, which is **not** a status, not a refusal code and not an
  arithmetic outcome; it is never the `NOT_APPLICABLE` status. A request is issued once or not at all; nothing is retried.
  *State-dependent tapes.* Cell A and Cell B requests are random access: every request is issued. In the sequential tapes (positions q00…q16, §5) an
  (arm, tape) is **state-dependent** when a request reads state that an earlier request of the same tape advances: S1 and S2 for FD, TS, PHFD, C1 and
  C2 (stepped tables, retained Taylor-shifted lists, retained jets); S3 for every arm (it reads the previous sample's S for `inc_k`). It is
  **state-independent** for Horner, Bezier and PH on S1 and S2 (evaluation at t_k from retained preparation state only).
  *Rule.* In a state-dependent (arm, tape), if the request at position q is REFUSED or INVALID, every later position q+1…q16 is `NOT_ISSUED`. (A refusal
  at any q, including q00, ends the tape; no finer rule is defined.) In a state-independent (arm, tape), every position is issued and keeps its own
  status. No unissued position is reported as OK, no certified value stands in for it, and no state is fabricated or advanced for it.
  *Accounting and events.* An unissued position has no event id, consumes no counted operation (not M, A, S, D or K), adds nothing to any
  committed or attempt ledger, and is not counted against the operation budget. Positions keep their frozen numbers `qNN`; they are never renumbered.
  Each (arm, tape) therefore reports, per position, exactly one of: an issued status, or `NOT_ISSUED`; with issued + unissued = 17. The only event
  of a dependent tape's failure is its first refusal's event id. *Eligibility.* An arm with any unissued or non-OK position on a matched tape is not
  eligible as a comparator on that tape (§2). *W31 stage tables.* A table row for a position is one of OK, REFUSED with its event id, INVALID, or
  NOT_ISSUED; for a state-dependent (arm, tape) the positions after the first refusal are NOT_ISSUED by this rule and need no derivation. Cell A tables are
  unchanged.
* **Divisions in P0.** The only Q-phase divisions in P0 are `x′/σ` and `y′/σ` in S2/S3. Cell A and Cell B Q-phase D = 0
  for every arm. Preparation legitimately uses D (integration).

## 4. Output contracts and the reference mapping

* **Cell A (per query t):** `(x, y, x′, y′, σ², σ, S(t)−S(0), N_κ, D_κ)` plus `ok = (σ ≠ 0)` (one sign test, K). `N_κ = 2·N_raw`,
  `D_κ` aliases the σ² object. S(0)=0, so the arc output is S(t) with no subtraction. No arm forms a curvature quotient.
  **Reference mapping:** the primary reference is `REVISION2_FIXTURE_VALUES.json` → `CellA_adapted_true_curvature_pair`
  (index 7 already holds the true numerator 2·N_raw; **do not double it**); the original
  `QUINTIC_FIXTURE_VALUES.json` → `cell_A[*].values` stores raw N at index 7, which is doubled **exactly once** for the
  cross-check. The two must agree.
* **Cell B (per τ):** `(ψx, ψy, ψ′x, ψ′y, s_signed, s_nonneg, S_inc)` plus `ok = (φ′(τ) ≥ 0)` (one sign test, K). `s_nonneg =
  s_signed` when `ok`, else `REFUSED(NONMONOTONE)` for the whole query. `S_inc = S(φ(τ))` since φ(0) = 0 and S(0) = 0.
  Every arm evaluates φ′(τ) for the flag (an arm that already holds the value reuses it). Reference: `cell_B.rows`.
* **Sequential, t = k/16, k = 0..16:** sample 0 is produced from preparation (no step); samples 1..16 follow. The three tapes
  are separate request sets, each started from the post-preparation snapshot (the copy is not an operation; preparation is counted
  once and is independent of the request): S1 `(x,y)` only, with **no `ok` flag and no other step**; S2 adds
  `(x′, y′, σ)`, `ok = (σ ≠ 0)` and `T = (x′/σ, y′/σ)` (2 D per sample in every arm); S3 adds `(N_κ, D_κ)` per sample and, once sample k+1
  exists, the increment `S((k+1)/16) − S(k/16)` for k = 0..15 (1 A each; null at k = 16). **Reference mapping:** the file's
  sequential rows give x, y, x′, y′, σ, T, the true curvature quotient and the next increment, not literal (N_κ, D_κ). The
  harness derives the expected pair by exact **oracle-side** arithmetic (uncounted, not a charged output): `D_κ = σ_ref²`,
  `N_κ = κ_ref·D_κ`, and checks the arm's pair equals it. This derivation is subject to reviewer acceptance (§10).
* **S4–S6 capability tasks** (retimed traversal, chain CH1, joins b1–b9, loops L0/L1, gated predicates): outputs compared with
  the pinned references; costs recorded, not screened. Their exact rational query procedures are the S5/S6 procedures of §5; the
  oracle-side quotients in the references are never charged to any arm.
* **P-1 references (supplied; adopted here as acceptance data).** `P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json` (SHA-256 in §0):
  17 dyadic rows for each of four representations, 68 in all: PH3∘φ_rev in **h-form** (U=1, V=1−t, h=−1), the same traversal in
  **primitive reversal form** (U=t−1, V=1, h=1), PH3∘φ_ns in h-form (U=1, V=t², h=2t), and PH3h∘φ_sq in h-form
  (U=1, V=φ_sq, h=(1+φ_sq)φ_sq′), plus all 16 registered random-access parameters for the nonconstant-h case. Request and field
  mapping adopted: `position`, `timed derivative`, `actual speed`, `signed progression rate`, `continued direction`, `actual tangent`,
  `curvature pair`, `actual signed curvature` (only where regular), `representation-signed integral`, `base-oriented increment`,
  `accumulated length`, `status` per request. For the reversal, ψ(0) = r(1) = (2/3, 1); h-form and primitive reversal give
  identical positions, velocities, actual tangent, speed, curvature and accumulated length, while the *base-oriented* increment is
  negative in both and the representation-signed fields differ; no field is treated as a representation-independent invariant.
  At φ_ns, t = 0: position, speed and direction are OK, direction = (1,0), actual tangent and curvature are
  `REFUSED(NONREGULAR)`; the formal pair (0,0) is diagnostic algebra and never a returned payload. `φ = t²` in the primitive form is
  `REFUSED(NOT_PRIMITIVE_RETIMING)`. For X-3(h), the factor 1+φ_sq equals 1 at t = 0, so that point alone is vacuous; the other tape
  points exercise it.

## 5. Frozen preparation program and algorithms

**Declared degrees.** Every polynomial has a declared degree (its certified highest nonzero index). A primitive operates on the
*full lengths of its inputs*; its result is then truncated to the declared degree (free), with an uncounted oracle-side
assertion that the dropped coefficients are zero. PH5 declared degrees: U 2, V 2, UU 4, VV 4, UV 4, dx 3, dy 4, sg 4, X 4,
Y 5, SS 5, U1 1, V1 1, NP1 3, NP2 3, Np 2, Nk 2. (PH3 and the others: the highest nonzero index of the pinned values.)

**Primitives (loop order is the stage order; indices ascending unless stated).**
`HORNER(c,t)`: `acc ← c_d; for i = d−1..0: acc ← acc·t + c_i` (d M, d A).
`DECAS(b,t)`: `for r = 1..d: for j = 0..d−r: b_j ← b_j + t·(b_{j+1} − b_j)` (d(d+1)/2 M, d(d+1) A), on a scratch copy.
`TSHIFT(c,t)`: `for j = 0..d−1: for i = d−1 down to j: c_i ← c_i + t·c_{i+1}` (d(d+1)/2 M and A), on a scratch copy; value c_0.
`FDINIT(c,δ)`: for k = 0..d: `t_k = t_{k−1} + δ` (A, k ≥ 1) then `p_k = HORNER(c,t_k)`; then the difference table, with the initial parameter fixed at t_0 = 0 and the grid generated in the order k = 0..d: copy v ← (p_0..p_d)
(free); Δ_0 ← v_0 (free); `for r = 1..d: for j = 0..d−r ascending: v_j ← v_{j+1} − v_j (A); then Δ_r ← v_0` (free copy); d(d+1)/2 A in all. All of
FDINIT's events (the d grid additions, the d+1 HORNER evaluations in their order, then the table subtractions) share the single operation counter of
the call `FDINIT.<poly>`. `FDSTEP`: `for j = 0..d−1 ascending: Δ_j ← Δ_j + Δ_{j+1}` (d A; Δ_{j+1} is not yet updated when Δ_j is, so the old value is used).
`PMUL(a,b)`: `for i, for j: term = a_i·b_j (M); the first term landing on index i+j initialises it, later ones add (A)` → (|a|)(|b|) M and (|a||b| − (|a|+|b|−1)) A.
`PADD`/`PSUB`: result length = the longer operand; for each index present in **both** operands one A; indices present only in the longer operand copy (PSUB: negation if the subtrahend is longer), no counted operation, so the A count is the shorter length. The zero polynomial is the one-entry list `[0]` of declared degree 0; `HORNER` of a degree-0 list is 0 M, 0 A; `PDER` of a degree-0 list is `[0]` with no operation.
`PSCALE2(a)`: `r_i = a_i·2` (S each). `PDER(a)`: `r_{i−1} = a_i·i, i = 1..d` (M each; i is an index). `PINT(a)`: `r_{i+1} = a_i ÷ (i+1)` (D each), r_0 = 0.
`PCOMP(a,b)`: `acc ← a_d; for i = d−1..0: acc ← PMUL(acc,b); then acc_0 ← acc_0 + a_i (A)`.
`BERN(a)`: `b_j = Σ_{i≤j} w_{j,i}·a_i` with the imported constants `w_{j,i} = C(j,i)/C(d,i)`: the first term initialises, later terms add (M for every term, so (d+1)(d+2)/2 M and d(d+1)/2 A).

**Step names and event indices.** An event's `step` is the label given in this section when one exists, otherwise the generic
name `<PRIMITIVE>.<polynomial>` (for example `HORNER.X`, `PCOMP.cx`, `FDSTEP.dy`, `BERN.sg`). The index `k` counts the Q
operations of the whole primitive call in execution order, **including operations of primitives it invokes** (so a `PCOMP`'s nested
`PMUL` operations and its final scalar additions share one counter). BERN's imported weights are checked as
`arm.P.import.w.<polynomial>.<j>.<i>`.

**Preparation steps (P-steps).** Common derivation DERIVE from the source `(U, V)`, h = 1, r_0 = (0,0): P1 UU = PMUL(U,U); P2 VV = PMUL(V,V);
P3 UV = PMUL(U,V); P4 dx = PSUB(UU,VV); P5 dy = PSCALE2(UV); P6 sg = PADD(UU,VV); P7 X = PINT(dx); P8 Y = PINT(dy);
P9 SS = PINT(sg); P10 U1 = PDER(U); P11 V1 = PDER(V); P12 NP1 = PMUL(U,V1); P13 NP2 = PMUL(U1,V); P14 Np = PSUB(NP1,NP2);
P15 Nk = PSCALE2(Np). Retained state per arm:

| Arm | P-steps executed | Retained (T) |
|---|---|---|
| B-Horner, B-TS | P1–P15 | X, Y, dx, dy, sg, SS, Nk |
| B-Bezier | P1–P15, then BERN of each of those seven | their Bernstein lists |
| B-PH, C1 (Cell A) | P1–P11 | U, V, U1, V1, X, Y, SS (dx, dy, sg, UU, VV, UV are scratch) |
| C2 | P1–P9 | jets (coefficient lists, order = degree) of U, V, X, Y, SS |
| B-COMP (Cell B) | P1–P9 on PH3, then P16 | X, Y, dx, dy, sg, SS (original), φ, φ′ |
| E-COMP | P1–P9, P16, then P17–P25 | cx, cy, cdx, cdy, csg, cSS and φ′ |
| E-BEZ | as E-COMP, then P26–P31 | Bernstein lists of the six composites and φ′ (coefficients) |
| E-TS | as E-COMP | the six composite power lists and φ′ |
| C1 (Cell B) | P1–P9, P16, P17, P18, P22 | φ, φ′, x̃ = cx (9), ỹ = cy (6), S̃ = cSS (9) |

Cell B extension: P16 φ′ = PDER(φ); P17 cx = PCOMP(X,φ); P18 cy = PCOMP(Y,φ); P19 cdxp = PCOMP(dx,φ); P20 cdyp = PCOMP(dy,φ);
P21 csgp = PCOMP(sg,φ); P22 cSS = PCOMP(SS,φ); P23 cdx = PMUL(φ′,cdxp); P24 cdy = PMUL(φ′,cdyp); P25 csg = PMUL(φ′,csgp);
P26–P31 BERN of cx, cy, cdx, cdy, csg, cSS in that order.

**Q-steps (named; event ids use these).**
*B-Horner (steps a1–a9):* a1 x = HORNER(X,t); a2 y; a3 x′ = HORNER(dx,t); a4 y′ = HORNER(dy,t); a5 σ = HORNER(sg,t); a6 S = HORNER(SS,t);
a7 N_κ = HORNER(Nk,t); a8 σ² = σ·σ; a9 ok. *B-Bezier:* same steps with DECAS. *B-TS:* same with TSHIFT.
*B-PH = C1 (steps b1–b19):* b1 u = HORNER(U,t); b2 v = HORNER(V,t); b3 u₁ = HORNER(U1,t); b4 v₁ = HORNER(V1,t); b5 uu = u·u;
b6 vv = v·v; b7 uv = u·v; b8 x′ = uu − vv; b9 y′ = uv·2 (S); b10 σ = uu + vv; b11 σ² = σ·σ; b12 m₁ = u·v₁; b13 m₂ = u₁·v;
b14 Np = m₁ − m₂; b15 N_κ = Np·2 (S); b16 x = HORNER(X,t); b17 y = HORNER(Y,t); b18 S = HORNER(SS,t); b19 ok.
*C2 (steps c1–c12):* c1 jU = TSHIFT(U-jet,t); c2 jV; c3 jX; c4 jY; c5 jS (each on a fresh copy; the retained jets are never modified);
c6 read (no operation), **full** projection for Cell A and S3: x = jX₀, x′ = jX₁, y = jY₀, y′ = jY₁, S = jS₀, σ = jS₁, U = jU₀, U′ = jU₁, V = jV₀,
V′ = jV₁; the sequential tapes use the narrower projections **c6a** (S1: x = jX₀, y = jY₀ only) and **c6b** (S2: x = jX₀, x′ = jX₁, y = jY₀, y′ = jY₁,
σ = jS₁ only); c7 σ² = σ·σ; c8 m₁ = U·V′; c9 m₂ = U′·V; c10 Np = m₁ − m₂; c11 N_κ = Np·2 (S); c12 ok. *B-FD:* `NOT_APPLICABLE`.
*Cell B, B-COMP (e1–e12):* e1 f = HORNER(φ,τ); e2 g = HORNER(φ′,τ); e3 ok on g; e4 ψx = HORNER(X,f); e5 ψy = HORNER(Y,f);
e6 q₁ = HORNER(dx,f); e7 q₂ = HORNER(dy,f); e8 q₃ = HORNER(sg,f); e9 ψ′x = g·q₁; e10 ψ′y = g·q₂; e11 s = g·q₃; e12 S_inc = HORNER(SS,f).
*C1 stand-alone (h1–h13):* h1 f = HORNER(φ,τ); h2 g = HORNER(φ′,τ); h3 ok; h4 ff = f·f; h5 w₁ = 1 − ff; h6 ψ′x = g·w₁; h7 w₂ = g·f;
h8 ψ′y = w₂·2 (S); h9 w₃ = 1 + ff; h10 s = g·w₃; h11 ψx = HORNER(x̃,τ); h12 ψy = HORNER(ỹ,τ); h13 S_inc = HORNER(S̃,τ).
*E-COMP / E-BEZ / E-TS (steps k1–k8):* k1 g = HORNER(φ′,τ); k2 ok on g; k3 ψx = P(cx,τ); k4 ψy = P(cy,τ); k5 ψ′x = P(cdx,τ);
k6 ψ′y = P(cdy,τ); k7 s = P(csg,τ); k8 S_inc = P(cSS,τ), where P is HORNER (E-COMP), DECAS on the Bernstein list (E-BEZ) or TSHIFT
(E-TS); the derivative composites already contain the factor φ′, so there is no Q-phase product. g is always evaluated by HORNER
on the power list φ′ (a retained list in every E-arm).
**Sequential tape arms** (PH3 and PH5). Extra scalar steps: a10 `Tx = x′ ÷ σ` (D), a11 `Ty = y′ ÷ σ` (D), a12 `inc_k = S_{k+1} − S_k`
(A, k = 0..15, once sample k+1 exists); b20, b21, b22 and c13, c14, c15 are the same three steps in the b and c programs. Step
instances inside one sample carry the sample as `qNN` (NN = k). **Required steps per tape (all other steps are not executed):**

| Arm family | S1 | S2 | S3 |
|---|---|---|---|
| Horner, Bezier, TS, FD (a-steps) | a1, a2 | a1–a5, a9, a10, a11 | a1–a12 |
| PH, PHFD, C1 (b-steps) | b16, b17 | b1, b2, b5–b10, b16, b17, b19, b20, b21 | b1–b22 |
| C2 (c-steps) | c3, c4, c6a | c3, c4, c5, c6b, c12, c13, c14 | c1–c5, c6, c7–c15 |

Sequential preparation: Horner and TS run P1–P15; Bezier P1–P15 then BERN of the seven; FD P1–P15 then `FDINIT.<poly>` for
X, Y, dx, dy, sg, SS, Nk in that order; PH and C2 as in Cell A; PHFD P1–P11 then `FDINIT.<poly>` for U, V, U1, V1, X, Y, SS in that order.
Per-arm evolution rule (`HORNER`/`DECAS`/`TSHIFT`/`FDSTEP` below replace `HORNER` of the Cell A program): *Horner*: evaluate at
t_k = k/16. *Bezier*: DECAS at t_k. *FD*: FDINIT (δ = 1/16) for **all seven** polynomials in P (preparation does not depend on the
request); in Q, each sample k ≥ 1 applies `FDSTEP` to the tables of the polynomials the tape needs (S1: X, Y; S2: X, Y, dx, dy, sg;
S3: all seven); sample 0 is the table's first entry (no operation); the scalar steps then run on the entries. *TS*: `TSHIFT` by
h = 1/16 on the **retained** lists of the needed polynomials, replacing them (the multiplier is data, so M); sample 0 reads c_0.
*PHFD*: FD tables for U, V, U1, V1, X, Y, SS in P; per sample the needed tables are stepped (S1: X, Y; S2: U, V, X, Y; S3: all
seven), then the b-step arithmetic runs on the table entries. *C2*: only the jets the tape constructs are shifted by h each step, replacing the retained ones (S1: jX, jY; S2: jX, jY, jS;
S3: jU, jV, jX, jY, jS); jets not selected are neither shifted nor read; sample 0 applies the tape's read projection to the unshifted retained jets. *C1 = PHFD* (declared). Sample/increment scheduling: emit sample 0 after P; for k = 1..16 step then sample; inc_k as soon
as sample k+1 exists. If a request of a state-dependent (arm, tape) is refused, later positions are not issued (§3, Revision 3.2.2); in particular
`inc_k` is not formed because sample k+1 never exists. The wrong-grid defect is caught by an explicit assertion that sample k occurs at exactly k/16 and equals
the certified row.
**S5/S6 procedures** (capability): each segment's hodograph h·w² by PMUL; x, y, S by PINT; speed |h|g with a sign test K; predicates
per pre-registration §5 with exact K tests; no ledger gate.

## 6. Jet orders

Order = degree for every jet: PH3 position 3, PH3h position and S 4, PH5 x 4, y 5, S 5, U and V 2, composite x̃ 9, ỹ 6, S̃ 9. Order is
stored with the object; a construction check requires the highest retained coefficient to be the declared degree. A jet of lower
order is E2 and any exactness-claiming request returns `REFUSED(APPROX_NOT_EXACT)`. The harmonic E2 control is the operator
(−127/37748736)·I, not a trajectory.

## 7. Ledger conformance and equivalence gates

There are **14** rows. Expected counts are consequences of §2/§5 and are re-derived by the reviewer.

| Test | Case | Expected |
|---|---|---|
| LU-H | HORNER degree d | M = d, A = d, G_calls = 2d |
| LU-H0 | HORNER on `[0, −4, −2]` (zero constant), d = 2 | M = 2, A = 2, G_calls = 4 |
| LU-DC | DECAS degree d | M = d(d+1)/2, A = d(d+1), G_calls = 3d(d+1)/2 |
| LU-TS | TSHIFT degree d | M = A = d(d+1)/2, G_calls = d(d+1) |
| LU-FD | FDSTEP degree d; and FDINIT degree d | step: A = d, G = d; init: M = d(d+1), A = 3d(d+1)/2 + d, G = 5d(d+1)/2 + d |
| LU-S | `uv·2` | S = 1, M = 0, G_calls = 0 |
| LU-VAL | multiply by the value ½ as data | M = 1, S = 0, G_calls = 1 |
| LU-D | integration `÷(i+1)` at i + 1 = 2 | D = 1, S = 0, G_calls = 1 |
| LU-W | a = 2³⁰/3, b = 5/2¹⁰: bit-lengths a (31, 2), b (3, 11) | M: W_bits = 31·3 + 2·11 = **115**, raw product 5368709120/3072 (33/12 bits), reduced 5242880/3 (23/2 bits), W_peak_red ≥ 31 (inputs counted); D a÷b: W_bits = 31·11 + 2·3 = **347** |
| LU-G | an M, A or D whose result is an integer | G_calls + 1 (no shortcut) |
| LU-P | split of an arm's ledger into P and Q | additive categories: P + Q = total; peaks: total = max(P, Q); T_ret_peak: maximum over observation points |
| EQ-1 | Cell A: ledger(C1) = ledger(B-PH) in every category and phase | exact equality (**accepted as conformance control**, owner D-1; depends on the preparation and storage rules of §2/§5) |
| EQ-2 | sequential: ledger(C1) = ledger(PHFD) | same |
| EQ-3 | each arm's outputs vs the references of §4 | zero mismatches |

**Preparation-count cross-check (author's analytic values for the reviewer to verify; not authority).** PH5, the P-phase of
B-Horner (P1–P15): M = 27 (P1–P3) + 4 (P10, P11) + 12 (P12, P13) = **43**; A = 12 (P1–P3) + 5 (P4) + 5 (P6) + 2 + 2 (P12,
P13) + 4 (P14) = **30**; S = 5 (P5) + 3 (P15) = **8**; D = 4 + 5 + 5 = **14** (P7–P9); K = 0; G_calls = **87**. B-PH (P1–P11): M = 31, A = 22,
S = 5, D = 14. C2 (P1–P9): M = 27, A = 22, S = 5, D = 14. These give X-10 a nonzero, independently fixed target.

## 8. Semantic, negative-control and mutant fixtures

Each row names a fixture that exercises the changed path. A surviving mutant is a test-design failure.

| ID | Mutant / control | Fixture | Killed by |
|---|---|---|---|
| X-1 | the factor 2 dropped or applied twice | Cell A tape, index 7 | EQ-3 (adapted file; original doubled once) |
| X-2 | σ taken as h·g, or T without sign(h) | P-1 h-form reversal (h = −1) against the primitive reversal rows | EQ-3 against the supplemental references |
| X-3 | chain-rule slip: omit φ′; omit h∘φ | Cell B rows (φ′); P-1 nonconstant-h rows for PH3h∘φ_sq, all 16 tape points and the dyadic rows (the t = 0 point is vacuous for the h part) | EQ-3 |
| X-4 | oriented length reported as accumulated | φ_bad: `ORIENTED_LENGTH` = B(t), total 0; `PIECEWISE_LENGTH` total 8/3 | expected pair (0, 8/3) |
| X-5 | single polynomial reported for the accumulated length | φ_bad `ACCUMULATED_LENGTH` | `REFUSED(OUT_OF_DOMAIN)` |
| X-6 | raw equality reported as a geometric join | b7, b9 | the reviewer's gated table |
| X-7 | shift misclassified, or value-based classification | LU-S, LU-VAL, the t = ½ query | ledger conformance |
| X-8 | zero skipping in Horner | LU-H0 | ledger conformance |
| X-9 | gcd skipped on an integer result | LU-G: the M `3·5 = 15` (both inputs integers) | G_calls increments by 1 |
| X-10 | preparation uncharged, or charged to one arm | the §7 P-phase targets (B-Horner PH5: 43, 30, 8, 14) | ledger conformance (not the P+Q identity alone) |
| X-11 | a division in Q-phase Cell A or B | Cell A, Cell B | Q-phase D = 0 for every arm |
| X-12 | FDINIT uncharged, or wrong grid | LU-FD init formula; **and** the sequential assertion that sample k is at exactly k/16 and equals the certified row (a cost-identical wrong grid must fail the value check) | ledger conformance and EQ-3 |
| X-13 | TSHIFT or DECAS miscounted *or mis-valued* | LU-TS, LU-DC plus EQ-3 | both |
| X-14 | order-2 jet of the cubic PH3 position treated as exact | PH3 position at order 2 | `REFUSED(APPROX_NOT_EXACT)` |
| X-15 | wrap or truncation instead of refusal in W31 | W31 run of the Cell A tape; sequential S1 on PH5 and Cell B stay pending a new reviewer allowance now that §5 names their steps | the reviewer-certified Cell A events below |
| X-16 | poisoned cache or partial output after a refusal | W31 refusal: state hash before = after; then a known admissible request equals a fresh run; then the repeat refuses identically | full committed-state comparison |
| X-17 | harmonic E2 step reported exact | operator control | class gate |
| X-18 | stationary point returns a tangent or curvature | φ_ns at t = 0: DIRECTION = (1,0) OK, TANGENT and CURVATURE `REFUSED(NONREGULAR)` | the adopted P-1 φ_ns rows (§4) |
| X-19 | C1 deviates from B-PH | Cell A | EQ-1 |
| X-20 | FD silently run in Cell A | Cell A | status `NOT_APPLICABLE` |
| X-21 | perturbed σ cache with unchanged generator | copy of PH5's sg with index 2 changed from 2 to 3; oracle-side identity x′² + y′² = σ² | certificate failure |
| X-22 | reversal twice | symbolic check: generator negated, hodograph restored | oracle-side |
| X-23 | non-polynomial retiming; primitive retiming with φ′ = 2t | φ = t/(1+t); φ = t² (primitive form) | `OUT_OF_DOMAIN`; `NOT_PRIMITIVE_RETIMING` |
| X-24 | E1a (C4) and E1b (3-4-5) expectations | `controls.E1a_C4`, `controls.E1b` (k = 0..16) | reference match |

**Certified W31 first refusals, Cell A (reviewer; JSON files in §0).** Preparation P1–P15, P1–P11 and P1–P9 pass; the extra Bernstein
preparation passes (largest raw 8 bits, reduced 7). For each arithmetic arm only the query q03 (t = 8/9) refuses: σ = 55010/6561 and
σ² has reduced numerator 3026100100 (32 bits) exceeding 31. First events: `B-Horner.Q.q03.a8.1.e1`, `B-Bezier.Q.q03.a8.1.e1`,
`B-TS.Q.q03.a8.1.e1`, `B-PH.Q.q03.b11.1.e1`, `C1.Q.q03.b11.1.e1`, `C2.Q.q03.c7.1.e1`; the other 15 queries of each arm pass. These certify
first width-refusal locations for the named routes only (not any implementation, rollback, cost or scratch behaviour). Sequential and
Cell B stage tables remain to be derived under a new reviewer allowance; their rows follow the §3 rule for dependent requests (Revision 3.2.2).

## 9. Run plan, budget and launch protocol

* **Contents of the single invocation** (in order): (0) verify every pin and `PINS.sha256`; (1) conformance §7; (2) EQ-3 for every
  arm under P4096; (3) Cell A, Cell B and the sequential control with both views; (4) the Pareto evaluation of §2 (comparator,
  guard, trigger, TRADE-OFF); (5) S4–S6 and the controls; (6) the mutant suite including W31; (7) write all artifacts, hash, read
  back independently and compare.
* **Budget.** One invocation, 60 s external wall clock, 1 GiB address space, no children, network, devices or installs, zero
  retries. **Counted-operation budget:** ≤ 1,000,000 M, A, S, D, K events summed over *every* arm and every phase, including
  conformance tests, mutants, refused attempts, the warm-up and the three timed passes; oracles are excluded from the
  operation budget but included in wall, memory and output limits. **Output budget:** ≤ 10 MiB including stdout, stderr, logs,
  provenance and artifacts; a violation stops the runner and is recorded as FAILED with the cause `OUTPUT_CAP`. Reduced ≤ 4096
  bits and raw ≤ 16384 bits under P4096.
* **Layout (new, isolated; not created):** `research/qcg_0/p0/` with files ≤ 150 lines: `ledger.py`, `poly.py`, `arms_a.py`, `arms_b.py`,
  `arms_seq.py`, `joins.py`, `refs.py`, `o1.py`, `o2.py`, `mutants.py`, `run.py`, `test_p0.py`, `launch.sh`, and `PINS.sha256`.
  The pins file and the tool manifest are specified below; their hashes and the contract's are recorded by the owner out of band.
* **Fail-closed launcher (`launch.sh`, written under the implementation GO; specified here).** Files: `PINS.sha256` is
  **checksum-only** (`<sha256>  <path>` lines for every source file of `p0/`, `launch.sh`, `TOOLS.manifest`, the reference JSON and the
  documents above); `TOOLS.manifest` lines are `<path>|<exact first line of --version>`. Neither file lists its own hash; the owner
  records the hashes of `PINS.sha256`, `TOOLS.manifest` and this contract out of band in the authorization record, so there is
  no circularity. The deadline is owned by GNU `timeout` itself: it exits **124 only when its own deadline fired**; the runner
  never exits 124 and installs no SIGTERM handler, so a child killed by the kernel (for example out of memory, status 137) is
  FAILED, not TIMEOUT. No `--kill-after` is used: the hard wall stays 60 s.

```bash
set -u ; set -o pipefail ; set -o noclobber           # no set -e: the finalization path below must always run
cd /home/john/Projects/hardware/SPU || exit 2
sha256sum -c research/qcg_0/p0/PINS.sha256 >/dev/null || exit 2                  # nothing is launched on any differing file
while IFS='|' read -r tool want; do
  [ "$("$tool" --version 2>&1 | head -1)" = "$want" ] || { echo "tool mismatch: $tool" >&2; exit 2; }
done < research/qcg_0/p0/TOOLS.manifest                                          # nothing is launched on any differing version
mkdir -p build/qcg_0 || exit 2
LEAF=build/qcg_0/run_01 ; mkdir "$LEAF" || exit 2                                # exclusive: refuses an existing leaf
{ date +%s.%N; git rev-parse HEAD; } > "$LEAF/provenance.txt" || exit 2          # informational only
/usr/bin/timeout 60 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304 -- \
  /usr/bin/python3 -B -I research/qcg_0/p0/run.py --out "$LEAF" >"$LEAF/stdout.log" 2>"$LEAF/stderr.log"
RC=$?
# ---- single finalization path: every step is attempted; nothing is inferred if any evidence write fails ----
PRC=0 ; PINS_AFTER=$(sha256sum -c research/qcg_0/p0/PINS.sha256 2>&1 | head -c 1024) || true
sha256sum -c research/qcg_0/p0/PINS.sha256 >/dev/null 2>&1 || PRC=1               # post-run pin check, always attempted
USED=$(du -sb "$LEAF" 2>/dev/null | cut -f1) ; USED=${USED:-99999999}
CAUSE=""
if [ $((USED + 4096)) -gt 10485760 ] || [ "$RC" -eq 90 ] || [ "$RC" -eq 153 ] || [ -e "$LEAF/CAP_BREACH" ]; then CAUSE=OUTPUT_CAP ; fi
# 1. all REQUIRED metadata first; no marker has been chosen or written yet
W=0
echo "$RC" > "$LEAF/exit.code" || W=1
{ echo "pins_after_rc=$PRC"; printf '%s\n' "$PINS_AFTER" | head -c 1024; } > "$LEAF/pins_after.txt" || W=1   # bounded: <= 1 KiB + header
if [ -n "$CAUSE" ]; then : > "$LEAF/$CAUSE" || W=1 ; fi
# 2. only now choose the marker; any metadata failure forces FAILED and can never leave COMPLETE or TIMEOUT
if [ "$W" -ne 0 ]; then MARK=FAILED ; : > "$LEAF/FINALIZE_FAILED" 2>/dev/null || true
elif [ -n "$CAUSE" ]; then MARK=FAILED
elif [ "$RC" -eq 0 ] && [ -f "$LEAF/RUNNER_DONE" ]; then MARK=COMPLETE
elif [ "$RC" -eq 124 ]; then MARK=TIMEOUT
else MARK=FAILED; fi
MW=0 ; : > "$LEAF/$MARK" || MW=1
N=0 ; for m in COMPLETE FAILED TIMEOUT ; do if [ -e "$LEAF/$m" ]; then N=$((N+1)); fi ; done
if [ "$N" -eq 0 ]; then echo "RESULT_UNAVAILABLE: no terminal marker persisted" >&2 ; exit 4 ; fi   # nothing is inferred
if [ "$W" -ne 0 ] || [ "$MW" -ne 0 ] || [ "$N" -ne 1 ]; then echo "FINALIZE_FAILED write=$W marker_write=$MW markers=$N" >&2 ; exit 3 ; fi
case "$MARK" in COMPLETE) exit 0;; TIMEOUT) exit 11;; *) exit 10;; esac
```

  The finalization path runs after every launch and always attempts the post-run pin check; it reserves 4 KiB for its own metadata
  (the `+ 4096` in the cap test) and writes only bounded files (`exit.code`, `pins_after.txt` ≤ 1 KiB of detail, at most one cause file, exactly one
  marker), so the aggregate cap covers the final evidence. **All required metadata is written before any marker is chosen**; if any of those writes fails the marker is forced to FAILED (a
  `FINALIZE_FAILED` file is attempted) and COMPLETE or TIMEOUT can never be created in that branch. If a FAILED marker cannot be persisted either, no marker
  exists and the launcher reports `RESULT_UNAVAILABLE` (exit 4); a finalization failure with a durable FAILED marker is exit 3. Completion is never inferred
  and, when a marker exists, the count must be exactly 1. Pin drift is recorded in `pins_after.txt` and does not change the marker. **Output cap enforcement:** `RLIMIT_FSIZE` (4 MiB per file) is set by `prlimit` and applies to the runner's writes to
  stdout, stderr and artifacts (prevention, per file); the runner keeps its own running total of bytes it writes and stops at
  8 MiB (prevention, total); the launcher's `du` check against 10 MiB, made before the marker is chosen, is detection. **Runner contract for
  caps:** the runner does all writing through one function that checks the running total and each file's size before every write; on a
  limit breach or any write `OSError` it creates, if it can, the empty file `CAP_BREACH` and exits **90**; it installs no SIGXFSZ handler (a kernel
  per-file-limit kill is status 153); it never writes `RUNNER_DONE` after a breach or write error, and `RUNNER_DONE` is the last file written.
  The launcher treats status 90, status 153, `CAP_BREACH`, or a leaf within 4 KiB of 10 MiB as `OUTPUT_CAP`: the marker is FAILED, an
  `OUTPUT_CAP` file is written, and COMPLETE is impossible. Runner exit codes are therefore 0, 90 (cap), or 1–99 otherwise, never 124. Oracles run in the same process under the same wall, memory and output limits.
* **Non-launching prerequisites (probed 2026-10-23; no experiment code):** `/usr/bin/timeout` 9.12, `/usr/bin/prlimit` 2.42.4,
  `/usr/bin/python3` 3.14.8; `/usr/bin/time` absent and unused; `build/qcg_0` absent. Re-verified inside `launch.sh`, which stops on
  any failure. If a later deterministic job were to exceed 60 s it would fall under the repository detached-runner rule.
* **Artifacts:** versioned UTF-8 JSON with canonical rational pairs (unissued positions recorded as `NOT_ISSUED`, with no event id): arm states, phase ledgers per category, outputs, statuses,
  event ids, attempt ledgers, the Pareto evaluation, mutant results, terminal marker; copy from gitignored `build/` into
  `research/qcg_0/` after review.

## 10. Independent review checklist (revision 3.2)

0. **Revision 3.2 corrections (new):** B1 C2 reads and evolution are tape-specific and reference only constructed jets (c6a, c6b, full c6; jets
   shifted per tape); B2 FDINIT's initial parameter t_0 = 0, table traversal and single operation counter are explicit; B3 the runner cap contract
   (exit 90, no SIGXFSZ handler, `CAP_BREACH`, `RUNNER_DONE` last) and the launcher's `OUTPUT_CAP` attribution preclude COMPLETE; B4 one
   finalization path with bounded metadata (4 KiB reserve), the post-run pin check always attempted, no `set -e`, exactly one marker, and
   `FINALIZE_FAILED`/`RESULT_UNAVAILABLE` when evidence cannot be persisted. **(Revision 3.2.1)** Required metadata is written before the marker is
   chosen and a metadata failure forces FAILED, never COMPLETE. Also: the stale PINS-layout sentence and the X-18 wording are removed, and event ids
   carry their route context.

1. §2: administrative checks (zero-divisor guard, parity, bounds, imports, degree assertions) are not K and not counted; semantic
   tests named in the text are K; preparation K = 0; the liveness rule for L_peak is reproducible.
2. §3/§5: the event grammar is unique for every program in the contract: the nested-primitive counter rule, the generic
   `<PRIMITIVE>.<polynomial>` names, P1–P31, the Cell B steps e1–e12, h1–h13, k1–k8, and the sequential required-step table
   (S1 positions only; S2; S3) with the per-arm evolution rules.
3. §5: `PADD`/`PSUB` unequal-length rule and the zero-polynomial convention are unambiguous.
4. §4: the P-1 references and field mapping are adopted as the reviewer produced them; the X-3(h) vacuous point is handled.
5. §8: X-12 has the grid/value assertion; X-21 and X-23 have concrete perturbations; the Cell A W31 events match the certified list.
6. §9: TIMEOUT is attested only by `timeout`'s own exit 124 (runner never exits 124, no SIGTERM handler); no `--kill-after`; the
   pins file is checksum-only and `TOOLS.manifest` is compared as strings; the output cap is enforced per file and in total and
   checked before the marker is chosen; exactly one marker; the post-run pin check is always attempted.
7. Items 1–10 of the previous checklist still hold (W proxy, aggregation, comparator, statuses, reference mapping, hand counts,
   14 conformance rows).
8. No certified value or mathematical statement is reopened; the policies of D-1…D-6 are accepted only with the scopes recorded in §11.

## 11. Readiness and open items

**Author's verdict: REVISE-RESPONDED, READY for independent re-review of Revision 3. NOT READY for implementation.**
Prerequisites that remain: (a) reviewer PASS on §10; (b) a new reviewer allowance to derive the sequential-S1/S2/S3 and Cell B W31
event tables from the now-named programs (the Cell A table is already certified); (c) a complete `PINS.sha256` and `TOOLS.manifest`;
(d) [done: owner D-1…D-6 recorded below]; (e) an owner authorization and the frozen execution budget. P-1 is discharged by the supplemental
references (adopted in §4).

**Owner dispositions (recorded 2026-10-23; ratified with the independent reviewer's stated qualifications). These adopt the scopes below and
broaden none of them; acceptance is not authorization.**

| ID | Verdict | Accepted scope |
|---|---|---|
| D-1 | ACCEPT | C1/B-PH (Cell A) and C1/PHFD (sequential) equivalence is a **conformance control**, not a C1-specific performance advantage. |
| D-2 | ACCEPT | Forward differencing is not applicable to random-access Cell A (`NOT_APPLICABLE`, excluded from comparators); it is retained as a **mandatory sequential comparator**. |
| D-3 | ACCEPT | The arithmetic ledger (literal-constant S, semantic K versus administrative checks, M2 informational) is an **abstract operation-accounting convention**, not a proxy for CPU timing, instruction count or hardware performance. |
| D-4 | ACCEPT | Deterministic **lexicographic** comparator selection with eligibility and **ASCII arm-id tie-break**; complete secondary comparisons (per-category virtual best, full ledgers) retained. The comparator is the lexicographically selected one, not claimed the best conventional method. |
| D-5 | ACCEPT | `T_ret_peak` measures **retained-state storage only**; scratch lifetime (`L_peak`) and other memory measures are reported separately; no peak-total-memory claim. |
| D-6 | ACCEPT | The joint-versus-standalone sharing metric J_c/Σ_c is **deferred**; P0 makes no sharing-efficiency claim. |

The R2 review certificate is used for its reference results (preparation counts, the Cell A W31 events, the P-1 references); its REVISE
verdict is not an assessment of Revision 3 or 3.1. The next reviewer pass verifies the amended contract against the four objections it
raised: sequential S1 operation selection, nested composite event identities, deadline attestation, and pin/version manifests with
output-cap enforcement. No certified numerical reference is regenerated. The sequential and Cell B W31 stage tables need a new,
separately authorized allowance (request drafted in `P0_CONTRACT_R3_STAGE_ALLOWANCE_REQUEST.md`; the R2 allowance is exhausted).

**Reviewer recommendations at the time (superseded by the dispositions above):**

| ID | Decision | Reviewer recommendation |
|---|---|---|
| D-1 | C1 declared equivalent to B-PH (Cell A) and PHFD (sequential) | accept as a scoped conformance design, no candidate-specific advantage claim |
| D-2 | FD `NOT_APPLICABLE` in random-access Cell A; sequential FD retained | accept for P0 scope |
| D-3 | literal-constant shift policy, M2 informational | accept as an abstract accounting convention (not CPU timing or hardware cost) |
| D-4 | lexicographic comparator with eligibility and ASCII arm-id tie-break | accept; call it the lexicographically selected comparator, not the best conventional method |
| D-5 | guard on `T_ret_peak` (retained-state storage), split reported | accept for retained-state storage only, not total or heap memory |
| D-6 | defer the J_c/Σ_c sharing metric | accept; P0 makes no sharing claim |
