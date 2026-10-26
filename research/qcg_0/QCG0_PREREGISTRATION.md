# QCG-0 — Algebraic Curve and Motion-Law Discovery: pre-registration

Date: 2026-10-23. Revision 3 (documentation-only correction after the independent Revision 2 re-inspection, disposition
REVISE; the six findings plus the degree addendum are applied, §18). Revision 2 (documentation-only correction after the independent fixture review; Revision 1 incorporated
the owner's cell and baseline decisions).
Status: **DRAFT. Documentation and mathematical analysis only. Execution and implementation HOLD.**
Author: Claude. Independent fixture reviewer: fresh-context `/root/qcg0_fixture_reviewer`, disposition **REVISE /
CERTIFIED WITH CORRECTIONS** (§0.2). The quintic PH5 is certified; this revision corrects the specification and changes
no certified value. The Revision 1 text hashed to `b33205e9…25fa8`; that is the text the reviewer saw.
Isolated path `research/qcg_0/`. Nothing outside this directory was modified: not X1, X2, RPLU2, RTL, ISA, simulator,
QSG-2 (`research/qsg2/`) or any frozen contract. The author's computation was limited to a drafting calculator (exact
`Fraction`, scratch, not an oracle of record, not a pilot); its checks are named where used. The independent reviewer
separately recorded bounded calculations (manifests pinned in §0.2); those are the reference values, not the author's.

Evidence tags: `[MATH]` proved here · `[LIT]` literature result recalled, not re-verified in this environment ·
`[SW]` repository software result · `[PRED]` author prediction, stated before measurement, not a gate · `[HYP]`.

## 0. Question and claim boundaries

**Question (owner's wording).** Can an algebraic motion law generate geometry, derivatives and certified constraints
more efficiently than storing and maintaining those quantities separately? Stated operationally: for matched tasks that
return the *same* geometric observables, does any law-based representation beat the best conventional exact method in a
Pareto sense on counted arithmetic, peak integer width and stored state?

Four outcomes are registered independently and none implies the next: **closure** (the mathematics holds), **semantic
equivalence** (candidates agree with oracles), **feasibility** (within declared bounds), **measured advantage**. A correct
but more expensive result is a valid result. Exactness against floating point is not an architectural advantage: exact
Bézier and exact PH implementations in ordinary rational arithmetic are the baselines. Nothing here claims hardware speed,
area or silicon behaviour.

### 0.1 Owner decisions recorded (2026-10-22) and where they are applied

| # | Decision | Applied in |
|---|---|---|
| 1 | Fresh-context independent mathematical reviewer, separate from this authorship and from the HEX-SOM acceptance context (the owner suggests GPT-6.1 only if its SOM work stays isolated, otherwise another fresh context) | §10, `QCG0_FIXTURE_REVIEW_PACKET.md` |
| 2 | Reviewer independently certifies a nondegenerate rational quintic PH fixture (generators, integrated coordinates, tangent, polynomial speed, arc length, endpoints, regularity, exact reference values) | review packet |
| 3 | Fixture frozen before any candidate implementation or cost evaluation | §14, review packet |
| 4 | Advantage-screen cells: **A** random-access multi-observable evaluation on the quintic; **B** exact polynomial retiming on the registered cubic | §9, §13 |
| 5 | Conventional PH arms get the same derivative/speed/arc-length precomputation and caching rights | §8.1 |
| 6 | Sequential forward differencing is a mandatory negative-control comparison, not an advantage-screen cell | §9, §13 |
| 7 | Complete costs: precomputation, storage, composition, coefficient growth, repeated queries, normalization, observation | §11 |
| 8 | PH-class closure, primitive-generator closure and nonnegative-speed condition are treated separately | §4 closure ledger |
| 9 | E0 / E1 / E2 distinction preserved | §6 |
| 10 | The generalized h-form completeness claim is literature-dependent and unverified within this experiment unless the reviewer independently establishes it | §3, §4 ledger, §16 |

### 0.2 Independent review artifacts (pinned, unchanged by this revision)

The certificate is relative to the Revision 1 pre-registration and the issued review packet, whose hashes the reviewer
verified before calculating. Full SHA-256, as printed by `sha256sum` on 2026-10-22:

    1391b1d9804c0d5b636070b1bee3d1cdb9c445f2bea4df4444c78243cc4cc673  research/qcg_0/QUINTIC_FIXTURE_CERTIFICATE.md
    8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34  research/qcg_0/QUINTIC_FIXTURE_VALUES.json
    15e310df23279ae8d725d3b01bd7bef3bc95da3b260eac98517cdc31606e3704  research/qcg_0/QUINTIC_FIXTURE_REVIEW_MANIFEST.json
    4b9602998d2cb2fab14af5440c892cce06ca4189d98bb7f40616362849d3e324  research/qcg_0/REVIEW_CALCULATION_AUTHORIZATION.md
    b33205e92370a41de5d1b7806f8435057065ea5272ea21866f5700be99025fa8  QCG0_PREREGISTRATION.md at Revision 1 (superseded text)
    1f6c5b94ab610f4950a4f2244803aeb17def3adf7a21ea50d5664c2759b98c82  QCG0_FIXTURE_REVIEW_PACKET.md (issued; not edited)

The manifest also records the hashes of the reviewer's scripts and invocation logs (`research/qcg_0/review/`). No value in
the certificate or values file is regenerated or altered here; where this document quotes one it names the source.

**Revision 2 review artifacts (pinned, unchanged by Revision 3).** Disposition REVISE; they supply the exact §9.2 reference
values and the corrections applied in §18:

    f90db359a3045e0283a6bfb9163ac6bc231ce9d31d1a9f89b7baa9096bdb9844  research/qcg_0/REVISION2_REVIEW_CERTIFICATE.md
    a66af3d68da5a7dba439818778af9e8fe70244e3dc2d8250ea891354124a0b46  research/qcg_0/REVISION2_FIXTURE_VALUES.json
    b7e979aca3b78e07386b042c73080bf49a18967a2487708f8e5008d8a5c29a26  research/qcg_0/REVISION2_REVIEW_MANIFEST.json
    68f1fa7d8c16997add1ce032d7f410f131484b3efa550881237912f7681f8852  research/qcg_0/REVISION2_REVIEW_CALCULATION_AUTHORIZATION.md
    58ea27367b16b2daadd42454a73c089379449ee02dd0f26283a81d51911325fa  research/qcg_0/REVISION2_DEGREE_ADDENDUM.md
    fbaf2b5a85615bf6a3ade33c759f2d496596aeff234dcf2ce684f0f25bec4f42  QCG0_PREREGISTRATION.md at Revision 2 (superseded text)

The reviewer reversed the Revision 2 diff in memory and recovered the Revision 1 hash, confirming the diff. These reference
files are conditionally certified: the numbers are exact mathematical references under the stated placement and gated
predicates; they do not fix the cost ledger or establish refusal behaviour.

**Precedence.** The review packet is a pinned input and is not edited. Where the packet and this Revision 2 conflict
(curvature numerator, the K1 sparsity remark, the float control), Revision 2 governs; §17 lists each superseded packet item.

**Certified quintic (reviewer-selected by the frozen rule R-SEL).** U = −1 − t − t², V = −1 − t + t², h = 1; selection
tuple (−1,−1,−1,−1,−1,1); Res(U,V) = 4. From the certificate: x′ = 4t²+4t³, y′ = 2+4t+2t²−2t⁴, σ = 2+4t+2t²+2t⁴,
x = 4t³/3 + t⁴, y = 2t+2t²+2t³/3−2t⁵/5, S = 2t+2t²+2t³/3+2t⁵/5, N_raw = −4t−2t², r(1) = (7/3, 64/15), S(1) = 76/15,
κ(0) = 0, κ(1) = −3/25.

## 1. Prior art and what is not repeated

| Source | Disposition |
|---|---|
| `docs/QSG2_PH_CURVE_SPECIFICATION.md`, `docs/QSG2_SOFTWARE_RESULTS.md`, `research/qsg2/` `[SW]` | Cubic PH (linear U,V) against ordinary factored PH, power basis and Bézier: exact queries correct (588 comparisons), **no cost advantage** (e.g. position 53.0 vs 16.8 µs in Python), polynomial arc length is "an established PH benefit that conventional implementations can retain equally". QCG-0 does not repeat that comparison. Inverse arc length for U=1,V=t needs the root of t³+3t−3 (irrational). |
| `knowledge/KNOWLEDGE_ARCHAEOLOGY` (`docs/KNOWLEDGE_ARCHAEOLOGY_2026-10-20.md`) F4 `[SW]/[MATH]` | u⁻¹ = 2−√3 = tan 15° is the Cayley/half-angle parameter of the exact 30° rotation in Q(√3); Pell multiplication is a hyperbolic scale, not a rotation. Used in §6 (E1). |
| `docs/papers/rplu_paper.tex` (jet ring, "Jet Multiply-Accumulate", "Jet Inverse"), `docs/SPARSE_JET_MAC.md` | Jets exist as A31[ε]/(ε^(N+1)) with Cauchy product and unit inverse; **no composition operator is listed; the jet pieces are RTL/simulation, not in the silicon-tested image.** See §7. |
| `research/exact_geometry/closure.py` (contract `spu_strategy/contract_exact_geometry_closure_2026-10-17.md`) | Exact segment-intersection/closure over rational Quadray coordinates; QCG-0 join and loop checks reuse the idea, not the code. |
| `docs/SG0_SYMBOLIC_GPU_INTERFACE_DESIGN_2026-10-18.md`, `spu_strategy/proposal_sim_g4_programmable_geometry_2026-10-18.md` | Procedural patch generation and input-described affine sequences already exist as design/qualified software. |
| `docs/SPU_ARCHITECTURAL_DISCOVERY_REVIEW` pattern `[INF]` | Bounded-exact wins in this repository are decisions and certificates on given objects, not long iterated evolution. QCG-0 therefore weights continuity, closure and refusal tasks as much as sampling tasks. |
| `research/arch_discovery_1/X2_PREREGISTRATION.md`, `X2_P0_READINESS_PACKET.md` | Relational jet-state dynamics. QCG-0 stays separate and reuses only its vocabulary (classes of exactness, statuses). |

Literature `[LIT]`, recalled from memory and to be cited with exact references in the final report: Farouki and Sakkalis
(1990) introduced PH curves; Kosinka and Lávička's survey is linked from `docs/QSG0_GENERATIVE_GEOMETRY_RESEARCH.md`;
the polynomial solution of x²+y²=z² (Kubota, 1972); exact forward differencing for rendering curves (Lien, Shantz and
Pratt, 1987, adaptive forward differencing) and its use in tessellation hardware; PH curves for CNC feed-rate control
(Farouki and collaborators). None is relied on for correctness inside the pilot; each used statement is re-derived or
checked by the oracles.

## 2. Definitions

* A **path** is the image of a regular polynomial map r : [a,b] → Q² up to orientation-preserving monotone
  reparametrization. A **motion** is a pair (path, parameterization): the map r itself, with its timing.
* **Geometric equivalence:** r̃ = r∘φ with φ increasing on the interval. **Equal-time (trajectory) equivalence:** r̃ = r as
  functions of t. A representation may be a function of the path only (shape invariants: tangent direction versus arc
  length, curvature versus arc length) or of the motion (speed σ(t), timing).
* An **exactness class** (E0, E1, E2, §6) is a property of a *law*, not of the arithmetic.
* Domain: Q (primary, unbounded in the oracle; bounded profiles refuse explicitly). Q(√3) is an optional later profile;
  nothing in P0 requires it. No float anywhere in state, ordering or oracles; wall times are separate. No A31 residue is
  used as geometry (§7).

## 3. E0 planar PH generators over Q

Let w = U + iV with U,V ∈ Q[t], h ∈ Q[t] a **factor polynomial** (h = 1 is the primitive form), on an interval I.

* Hodograph: r′ = x′ + i y′ = h·w², so x′ = h(U²−V²), y′ = 2hUV.
Write g = U²+V² and d = w²/g = ((U²−V²)/g, 2UV/g), the **continued generator direction**, a rational point on the unit
circle defined wherever g ≠ 0 and independent of h and of its sign. Conventions (Revision 2, after the review; each
statement is `[MATH]` by direct expansion and was confirmed by the reviewer):

* **Speed.** |r′| = |h|·g, so the actual non-negative speed is |h|g. The expression h·g is the *signed progression rate*;
  it equals the speed only where h ≥ 0. (The packet's σ = h(U²+V²) is the signed rate.)
* **Unit tangent.** At a regular point (h ≠ 0, g ≠ 0) T = sign(h)·w²/g = sign(h)·d. For h > 0 it equals d; for h < 0 it is
  −d (traversal against the direction field). The earlier statement "T is independent of h" holds only for h > 0.
* **Stationary points.** h = 0 ⇒ r′ = 0 and |r′| = 0: T = r′/|r′| is 0/0 and must be refused; d is still defined if g ≠ 0.
  The curvature expression below is also undefined there. At a sign change of h the velocity reverses relative to the
  continued direction d and the actual tangent T changes sign; d is continuous through it. The path does **not** in general
  retrace itself (reviewer's counterexample: h = t, U = 1, V = t gives x = t²/2 − t⁴/4, y = 2t³/3, so at t and −t the x
  values agree and the y values have opposite signs; for a counterexample strictly inside [0,1] use t−1/2 and the translated
  generator). The specific composition r∘φ_bad does retrace, because it composes one curve with a φ that is symmetric about 1/2.
* **Curvature.** cross(r′,r″) = 2h²·g·N_raw (the h′ terms cancel because cross(w²,w²)=0). Hence, for the Euclidean signed
  curvature relative to the oriented tangent, κ = cross(r′,r″)/|r′|³ = **2·N_raw / (|h|·g²)**, where
  **N_raw := U V′ − U′ V** (kept for provenance). The earlier form 2N/(h·g²) agrees only for h > 0. Reversal flips the
  sign of κ through N_raw of the composed generator (checked below).
* **Factor-two rule (owner decision, Revision 2).** Wherever a *curvature numerator and denominator* are requested, the
  numerator is **N_κ := 2·N_raw** and the denominator is **D_κ := |h|·g²** (for h = 1, D_κ = σ²), so κ = N_κ/D_κ. The raw
  pair (N_raw, g²) is provenance only and is never labelled a curvature pair. The certified values file stores N_raw and
  D_raw = σ² for h = 1; a harness compares N_κ = 2·N_raw against it, with the factor stated here, and the values file is
  not edited. (The certificate's JSON also carries `kappa_corrected` for each Cell A row and the corrected endpoint pairs
  (0,4) and (−12,100) for the quintic.)
* Position r(t) = r(0) + ∫ r′, polynomial of degree deg(h)+2·deg(w)+1. The oriented arc length S_or(t) = ∫ σ_signed with
  σ_signed = h·g is polynomial; the accumulated traversal length L(t) = ∫|h|g equals S_or only where h ≥ 0 (§4 R6).
* Regularity: h ≠ 0 and g ≠ 0 on I (equivalently |r′| > 0). A zero of g in I cannot occur when gcd(U,V) = 1 (resultant ≠ 0).
  A zero of h is NONREGULAR for tangent and curvature queries, though the direction d is still defined there.

**Completeness over Q — independently proved by the reviewer (certificate §F-D); no external citation is relied on.**
Statement: for polynomials X, Y, Z ∈ Q[t] with X²+Y²=Z², there are h, U, V ∈ Q[t] with X = h(U²−V²), Y = 2hUV,
Z = h(U²+V²). Scope and assumptions: polynomial data over Q; the case Y = 0 and the zero triples are handled separately
by constant generators; d = gcd(X,Y) divides Z; with A=X/d, B=Y/d, C=Z/d the factors C+A and C−A are coprime with product B²,
so each is a rational unit times a square (C+A=αf², C−A=βg²), αβ is a rational square (δ²), and
h = dα/2, U = f, V = (δ/α)g. The factor h is a polynomial but **not necessarily positive or constant**: to get non-negative
speed on a regular interval choose the sign of Z positive there, which makes h positive. It does **not** show that every
curve has h = 1 over Q. The author sanity-checked the final construction (h(U²−V²)=dA, 2hUV=dB, h(U²+V²)=dC) but is not the
independent verification. The previous `[LIT]` note is superseded. The oracle still does not rely on completeness: all
pilot curves are built from generators.

**Inverse arc length** is outside the exact class (QSG-2 example; I recall that no non-linear polynomial PH curve admits a
rational arc-length parametrization `[LIT]`). Natural-equation (arc-length) state is therefore not an E0 object.

## 4. Retiming — the corrected result

Correction first. An earlier statement in this session ("a PH curve stays PH only if φ′ is a square") is **wrong for the
PH class** and right only for the primitive (h = 1) generator form. The owner's clarification is accepted; this section
states and proves the precise facts.

Let r be PH with hodograph h·w² and polynomial speed σ, and let φ ∈ Q[t] be a polynomial retiming.

**R1 (class closure) `[MATH]`.** ψ = r∘φ satisfies |ψ′|² = (φ′·σ∘φ)², a polynomial square. So the PH class is closed under
every polynomial reparametrization, with no condition on φ′. The generator in (U,V,h) form is
(Ũ,Ṽ,h̃) = (U∘φ, V∘φ, (h∘φ)·φ′), because ψ′ = φ′·(h∘φ)·(w∘φ)².

**R2 (speed and arc length).** With g=U²+V², the actual speed of ψ = r∘φ is |φ′·(h∘φ)|·(g∘φ), not (φ′·h∘φ)·(g∘φ) unless the
prefactor is non-negative. The signed progression rate φ′·(h∘φ)·(g∘φ) is a polynomial and equals the speed wherever
φ′·(h∘φ) ≥ 0 (zero included). On an interval where φ′·(h∘φ) ≥ 0 (for example monotone increasing φ with h ≥ 0) the
accumulated traversal length is S_or(φ(t)) − S_or(φ(0)), polynomial, where S_or = ∫ h·g is the *oriented* length of the
original parameterization (it equals the original's accumulated length only where h ≥ 0 on the original interval; the
formula must not be read as a composition of an accumulated length when h or φ′ is negative). If the prefactor changes sign the speed is generally a
piecewise polynomial (R6). A retimed parameter must stay inside the interval on which the original regularity
certificate holds; outside it the certificate does not apply.

**R3 (primitive form).** Within the form with h = 1 over Q the retiming condition is exact: ψ′ is a square in Q[i][t] iff
φ′ is a square in Q[i][t] (a quotient of squares in a UFD that is a polynomial is the square of a polynomial), and a real
polynomial is a square in Q[i][t] iff it equals ±q² with q ∈ Q[t]. So, **within primitive Q-generators**,
φ′ = ±q² is necessary and sufficient. For φ′ = q² the new generator is (U∘φ·q, V∘φ·q); for φ′ = −q² use
(−V∘φ·q, U∘φ·q) (multiply w by i). A positive rational constant that is not a square (for example φ(t)=2t) needs h ≠ 1 or
the extension Q(√c).

**R4 (stationary points) `[MATH]`.** If φ′ has a zero inside the interval the retimed curve has |r′| = 0 there (a
stationary point). The h-form still carries the continued direction d∘φ through it, whereas T = r′/|r′| is 0/0 and the
curvature 2N_raw/(|h̃|g̃²) is undefined. A tangent query must say which it returns; the registered convention is: the
direction query returns d, the tangent and curvature queries refuse. Control: φ(t) = t², h̃ = 2t(h∘φ); at t = 0 the
certificate gives continued direction (1,0) while T is 0/0.

**R6 (oriented versus accumulated length; certificate §F-C) `[MATH]`.** For φ_bad = 4t−4t² on PH3 (S = t+t³/3): with
B(t) = φ_bad + φ_bad³/3 the oriented length S(φ_bad(t))−S(0) = B(t), total oriented length 0; φ_bad′ = 4−8t changes sign at
t = 1/2 where φ_bad = 1 and the speed is zero; the accumulated traversal length is B(t) on [0,1/2] and 8/3 − B(t) on
[1/2,1], total 8/3. The single-polynomial class refuses the accumulated length (`OUT_OF_DOMAIN`); that is a class
statement, not a claim that the length is uncomputable: it is exact and piecewise polynomial. Oriented displacement and
accumulated length are different quantities and no arm may conflate them.

**R5 (reversal) `[MATH]`.** φ(t) = 1−t, φ′ = −1 = i². The primitive generator of the reversed curve is
(Ũ,Ṽ) = (−V(1−t), U(1−t)); verified in the drafting calculator that its hodograph equals −r′(1−t) for the cubic fixture.
Reversal composed twice restores the hodograph; the generator returns as its negative (the reviewer's proof: the second
reversal gives −W). Reversal flips the sign of κ (confirmed above through N_raw of the reversed generator).

**Closure ledger (kept separate, owner decision 8).**

| Statement | Status |
|---|---|
| PH-class closure: x′²+y′² a polynomial square is preserved by every polynomial retiming | `[MATH]` proved (R1), independent of any generator form |
| (U,V,h)-form closure: (Ũ,Ṽ,h̃)=(U∘φ, V∘φ, (h∘φ)φ′) represents the retimed curve for every polynomial φ | `[MATH]` proved (R1) |
| Primitive-generator (h=1) closure over Q: φ′=±q², q∈Q[t], necessary and sufficient | `[MATH]` proved (R3) |
| Non-negative polynomial speed: φ′·(h∘φ) ≥ 0 on the interval (monotone, non-negative h) | `[MATH]` (R2) |
| Every polynomial PH triple over Q has the (U,V,h) form with polynomial h (completeness) | `[MATH]` independently proved by the reviewer (certificate §F-D); h need not be positive or constant, and h = 1 is not always possible |
| Rational retimings leave the polynomial class | out of scope |

**Worked fixture (checked in the calculator).** Solving 3a²+3ab+b²=3 rationally gives (a,b) = (−2/7, −9/7), i.e.
w = −(2+9t)/7 and φ(t) = (4t+18t²+27t³)/49, φ′ = ((2+9t)/7)², φ(0)=0, φ(1)=1, monotone increasing. Applied to the QSG-2
cubic (U,V)=(1,t) the retimed generator is (w, φ·w) and the endpoint r(1) = (2/3, 1) is unchanged. Composite degrees grow
(position degree 9), which matters for the conventional arm that expands the composite polynomial (§8).

**Rational retimings** (Möbius or other rational φ) leave the polynomial class (rational PH curves). They are outside P0.

## 5. Composition, joins, reversal, closure

Concatenate E0 segments r_k on [0,1], each with its own (U_k,V_k,h_k). Two layers are kept apart (Revision 3, review
finding): **raw endpoint equalities** and **geometric join predicates** that gate higher continuity on lower.

*Raw equalities (a = the end of one segment, b = the start of the next; no placement implied by the first five):*
R_dir: T_a(1) = T_b(0) (actual unit tangents, sign(h) included); R_opp: T_a(1) = −T_b(0); R_vel: r′_a(1) = r′_b(0);
R_acc: r″_a(1) = r″_b(0); R_κ: κ_a(1) = κ_b(0) (signed, both regular); R_pos: r_a(1) = r_b(0) *after placement* (two
rational equalities in the plane; the P-CHAIN rule of §9.2 states the placement, and an explicit gap breaks R_pos).

*Geometric predicates (explicit gates):*

* **G⁰** = R_pos.
* **G¹** = G⁰ ∧ R_dir. **Cusp** = G⁰ ∧ R_opp.
* **C¹** = G⁰ ∧ R_vel (equal hodograph h_a w_a² = h_b w_b² at the joint). **C²** = C¹ ∧ R_acc.
* **G²** = G¹ ∧ R_κ.
* A raw equality never stands for a geometric join: equal derivatives across a position gap (fixture b9) are not C¹, and
  equal curvature with opposite tangent (b7) is a cusp, not G².
* Generator-level shortcuts: for h_a, h_b > 0, R_dir ⇔ cross(w_a,w_b) = U_aV_b − U_bV_a = 0 with w_a ∥ w_b, and
  R_opp ⇔ dot(w_a,w_b) = 0 with both nonzero (w and −w give the same hodograph). For general h use the actual tangent
  with sign(h). The reviewer's reference file records both layers (raw and gated) separately.
* **Arc length** adds exactly: S_total = ΣS_k(1) (accumulated lengths; oriented lengths add as signed quantities).
* **Loop closure:** Σ(r_k(1)−r_k(0)) = 0 exactly (a vector residual, not a scalar norm).

(Checked on the fixture w_a(1)=(1,1): w_b=(1,1) gives C¹; w_b=(2,2) gives G¹ with a speed jump; w_b=(−1,−1) gives G¹
with the generator negated, same tangent; w_b=(1,0) a corner; w_b=(1,−1) a cusp.)

Conventional exact Bézier does the same with a cross product and a dot product of end control differences: the cost class
is the same. This is an honest equal, not a win.

## 6. Typed law classes

| | E0 closed-form algebraic generator | E1 finite-group or certified orbit | E2 truncated differential jet |
|---|---|---|---|
| Object | (U,V,h) over Q[t] on an interval; also polynomial/Bézier control data | state (P, R) with R in a declared group G; steps are rational lengths along R | jet (j₀…j_N) of a state with a declared law A(P,V,t) |
| Exactness | every polynomial observable exact in Q | exact in the declared field; **E1a** finite group (C4 over Q, C12 over Q(√3)): bounded entries; **E1b** infinite rational-rotation group (e.g. the 3-4-5 rotation): exact, coefficient size grows with word length | the formal Taylor coefficients through N are exact; **the trajectory is approximate**; if the true solution is a polynomial of degree ≤ N the class is E0-by-degree (certificate required) |
| Guaranteed invariants | |r′| = σ; PH identity; arc-length polynomial; reversal rule | orthogonality of R; group closure (R^|G| = I); additive position growth | coefficient identities of the formal flow only; no invariant of the exact flow is guaranteed unless a structure-preserving form is proved |
| Refusals | NONREGULAR; OUT_OF_DOMAIN (non-polynomial retiming, inverse arc length, accumulated length when the prefactor φ′·h∘φ changes sign); ARITH_LIMIT / WORK_LIMIT | OUT_OF_DOMAIN (angle not in G); ARITH_LIMIT on E1b growth | `APPROX` is a class label, not a refusal; ARITH_LIMIT for coefficient growth; no error bound claimed unless proved |
| Reversibility | exact (R5) | exact (inverse word) | **not exact**: forward then backward step leaves a nonzero exact residual |

A jet of order N is *exact* for a polynomial curve of degree ≤ N: jets of PH curves are a basis change (Taylor basis),
not new information, and a jet of order 2 cannot hold a cubic. Class assignment therefore depends on the pair (order,
degree) and on a stated certificate. Describing E2 as an exact continuous trajectory is a registered error and a control.

## 7. Is RPLU2's jet machinery a useful substrate?

* Structure that transfers: the truncated Cauchy product, the unit-base jet inverse (needed for T = (…)/(|h|g) and κ = N_κ/D_κ
  as local series), sparse windows (`SPARSE_JET_MAC`), and the refusal-on-non-unit discipline.
* What does not transfer `[MATH]`: A31 is F_{p²}×F_{p²} (review §4F). It has no order, sign, magnitude or limit, so it
  cannot decide regularity (σ>0), monotonicity, arc-length sign or curvature sign. Ring identities (x′²+y′²=σ²,
  Cauchy-product identities) do hold in A31 and can serve as an X1-style *witness* for PH identities, never as geometry.
* Gap: the RTL jet MAC is parameterized in N but defaults to N=2; a cubic PH position (PH3) needs order ≥3, the quartic PH3h position ≥4, and the quintic ≥5. The
  RTL is simulation-verified and is not in the silicon image (paper, "From Jets to the RPLU Pipeline").
* Conclusion for scope: use the *algebra* (Cauchy product, inverse) over Q in software. A future ordered ring (Q, or Q(√3)
  via the existing Surd arithmetic) would need its own review. No A31 semantics are imported.

## 8. Baselines and arms (all in exact rational arithmetic, same inputs, same observables)

| Arm | Representation and method |
|---|---|
| B-Horner | Power-basis coefficients; Horner evaluation at each t (position, derivative polynomials, S and σ precomputed from the same generator) |
| B-FD | Exact forward differencing with fixed dyadic step: Newton difference table, d additions per polynomial per step, no multiplications; initial table by evaluation |
| B-TS | Exact Taylor shift (jet advance, order = degree): Horner shift, d(d+1)/2 additions per step with binomial/powers of h |
| B-Bezier | Bernstein control points, de Casteljau evaluation, derivative control points, exact |
| B-PH | Standard PH evaluation from the same generators with cached σ and S polynomials (QSG-2 "ordinary factored" arm) |
| B-COMP | Composition of evaluators for retiming: evaluate φ then r (no expansion of r∘φ), and the expanded composite polynomial (reported separately) |
| C1 | E0 law interface: (U,V,h) state, typed refusals, retiming algebra (R1–R5), join predicates, lazy observation |
| C2 | E0-by-degree jet arm: Cauchy-product jets over Q with jet inverse for T and κ; no A31 |

"Virtual best" is also reported: for each cost category the minimum over B-arms. Candidate wins against a single best arm
are not enough; the screening target in §13 uses the stronger virtual-best comparison as a secondary view.

### 8.1 Equal precomputation and caching rights (owner decision 5)

Every arm, candidate and conventional, may precompute once, at charged cost, and cache any of: the power-basis
coefficients of x, y, x′, y′, σ, σ², S, the curvature numerator N_κ = 2(UV′−U′V) and denominator D_κ = |h|(U²+V²)² (§3); Bernstein
control points and their derivative control points; difference tables; the generator coefficients and their derivatives.
No arm is forced to rediscover a PH identity per query, and no arm is given information another lacks. The conventional
PH arm (B-PH) therefore holds the same σ, S, N_κ and D_κ polynomials as the candidate. Frozen counting policy: Horner
cost is counted from the polynomial *degree* (no zero-coefficient skipping) for every arm; a sparse-aware variant that
skips zero coefficients is reported separately and may not replace the frozen count. Storage is reported two ways:
authoritative state alone, and state plus every cache an arm actually uses. A storage reduction accompanied by more
arithmetic is classified TRADE-OFF, never WIN.

**Predictions `[PRED]`, stated before measurement.** For uniform dyadic sequential sampling of a cubic PH with position,
x′, y′, σ, S: B-FD needs 15 additions per sample and no multiplications (position 2×3, x′ and y′ 2×2, σ 2, S 3).
A generator evaluation of (x′,y′,σ) from U,V costs 3 multiplications and 3 add/subs plus 2 additions to step U,V, so its
saving over FD is one addition for three multiplications. B-FD is expected to dominate S1–S3. The generator's expected
strengths are storage (six rationals against eight for a cubic Bézier), random-access queries, retiming (S4), and the
join and constraint tasks (S6). The most likely overall outcome is no Pareto win on S1–S3 and ties on S6.

*Cell A counts, recomputed for the certified quintic (stated before any measurement; this recomputation follows the
certificate and precedes all cost evaluation).* The certified polynomials have degrees x:4, y:5, x′:3, y′:4, σ:4, S:5,
N_κ:2 (U, V, U′, V′ of degrees 2, 2, 1, 1). Dense-degree Horner, doubling by shift, measured counts decide. **B-Horner (every polynomial cached in power basis; this is the 28/27 route):**
x 4, y 5, x′ 3, y′ 4, σ 4, σ² 1, S 5, N_κ 2 = **28 multiplications, 27 additions**. **Factored route (the arithmetic of B-PH, and of C1 in Cell A; the 26/23 route):** U, V, U′, V′ by
Horner (6 multiplications, 6 additions); U², V², UV (3); x′ and σ (2 add/sub); σ² (1); N_κ (2 multiplications, 1
subtraction); and the cached degree-4, 5, 5 integrals x, y, S (14 multiplications, 14 additions) = **26 multiplications,
23 additions**. That is 2/28 (about 7%) of the multiplications and 4/27 (about 15%) of the additions: these two predicted *arithmetic*
categories fall below the 20% threshold (the reviewer confirmed the counts under the degree-only Horner and free-doubling
convention). The integrals x, y and S are half of all multiplications and cannot be derived from U,V for free. Excluding
them, derivative-side observables cost 14 against 12 multiplications (about 14%). The other counted categories (serialized
state, peak integer width, divisions, comparisons) are unmeasured, so these arithmetic predictions do **not** settle the whole
Cell A Pareto screen. Counting convention, frozen for every arm before execution: multiplication or division by 2 is a
shift, counted in a separate `shift` category and not as a multiplication or an addition; no other constant is treated
specially.
*Cell B:* direct evaluation of the original curve at φ(τ) (three Horner steps for φ, then three each for r and S) is
expected to dominate the retimed generator, whose composite position and arc length have degree 9 (certificate: x, y, S
composite degrees 9, 6, 9); the generator is expected to help only if the retimed object must stand alone, and it does
not avoid the degree growth under repeated retiming.

## 9. Matched tasks and fixtures

Inputs only are fixed here; expected outputs are derived by the independent reviewer (§10).

Curves (planar, Q): **PH3** (U,V)=(1,t), h=1 (cubic; QSG-2 primary: r=(t−t³/3, t²), S=t+t³/3, r(1)=(2/3,1), S(1)=4/3,
sigma(1/2)=5/4, T(1/2)=(3/5,4/5)); **PH5** the certified quintic U = −1−t−t², V = −1−t+t², h = 1 (§0.2; reviewer-selected by R-SEL, not by the author); **PH3h** (U,V,h) = (1, t, 1+t): a **quartic** (reviewer's degree addendum): x′ = 1+t−t²−t³, y′ = 2t+2t², x = t+t²/2−t³/3−t⁴/4,
y = t²+2t³/3, speed (1+t)(1+t²) of degree 3, arc length of degree 4; an exact jet of its position needs order at least 4.
Retimings: φ_sq = (4t+18t²+27t³)/49 (square derivative, monotone); φ_ns = t² (h-form only, stationary at 0);
φ_rev = 1−t; φ_bad = 4t−4t² (φ′=4−8t changes sign at 1/2; control).

| Task | Observables returned (identical for every arm) |
|---|---|
| S1 | positions r(k/16), k=0..16 |
| S2 | S1 plus x′, y′, σ and unit tangent T at each sample (T as an exact rational pair) |
| S3 | S2 plus the arc-length increment on [k/16,(k+1)/16] for k = 0..15 and κ at each sample k = 0..16. **Endpoint convention (frozen):** at k = 16 the increment is absent (null), as in the certified values file; κ is returned as the pair (N_κ, D_κ) and, for the reference, as a quotient |
| S4 | S3 for the retimed traversal r(φ(k/16)) with φ_sq, φ_ns (h-form and a refusal in the primitive form), φ_rev |
| S5 | the chain CH1 of §9.2 (inputs fixed there) with position, unit tangent, speed and accumulated arc length at nine chain parameters |
| S6 | continuity and constraint verification on the join and closure inputs of §9.2: G⁰, G¹, cusp, C¹, C², G², loop closure |

### 9.1 The two advantage-screen cells (owner decision 4) and the negative control (decision 6)

**Query tape (both cells).** 16 rational parameters in this exact, non-monotone order (random access, two repeats to
expose caching): 5/7, 1/9, 3/8, 8/9, 1/2, 2/5, 6/7, 0, 1, 1/3, 7/10, 2/9, 5/6, 3/4, 1/9, 5/7.

**Cell A — random-access multi-observable (primary).** Curve: the reviewer-certified quintic PH5 (primitive form). For
each query t every arm returns, as exact rationals, the same nine values and flags: r(t) (2), r′(t) (2), σ² (1), σ (1,
valid because σ = U²+V² is a rational function value with no root), S(t)−S(0) (1), and the curvature numerator and
denominator as the pair (N_κ(t), D_κ(t)) = (2·N_raw, σ²) per the factor-two rule of §3 (the certified values file stores
(N_raw, D_raw), so the harness compares N_κ against 2·N_raw), no quotient required and no division performed; a query where
D_κ = 0 is flagged and not divided. Arms: B-Horner, B-Bezier (de Casteljau plus derivative control points), B-PH (with §8.1 caches), C1, C2, and
B-FD (the negative control, evaluated only at the dyadic subset where it applies, or re-initialized and charged where it
does not). Precomputation, storage, per-query arithmetic, coefficient widths, query overhead and the shared-computation
ratio J_c/Σ_c (§11) are reported.

**Cell B — retimed trajectory (secondary).** (Certified reference rows: `cell_B.rows`, 16 rows of seven values.) Curve: the registered cubic PH3 with the retiming φ_sq. For each tape value τ
every arm returns: ψ(τ) = r(φ(τ)) (2), the timed derivative ψ′(τ) = φ′(τ)·r′(φ(τ)) (2), the signed speed φ′·σ∘φ and the
non-negative speed (valid because φ′ ≥ 0), and S(φ(τ)) − S(φ(0)). Arms: C1 (retimed generator, §4 R1), B-COMP (original
curve evaluated at φ(τ), the strongest conventional arm), the expanded composite polynomial in power basis, the composite
in Bernstein form with de Casteljau, B-TS on the composite, and B-Horner. Charged: composition, degree growth (position
degree 9), initialization, storage and repeated evaluation. Control: the non-monotone retiming φ_bad: the certified values
give the oriented length B(t) (total 0), the accumulated traversal length B on [0,1/2] and 8/3−B on [1/2,1] (total 8/3),
and the single-polynomial class refuses the accumulated length with `OUT_OF_DOMAIN` (R6); oriented and accumulated length
are two different required outputs.

**Mandatory negative control.** Sequential dyadic sampling (S1–S3, step 1/16) on PH3 and PH5 is measured for every arm and
reported with the prediction that B-FD dominates. It is not an advantage-screen cell and its outcome does not decide
whether to continue.

### 9.2 Chain, join and closure inputs (normative inputs; reference values are the reviewer's pinned JSON)

Revision 2 supplied the translations, ordering, parameter convention and derivative data the review found missing. Every
polynomial is over Q, interval [0,1] per segment, h = 1 unless stated. The literal expected outputs (CH1 rows, raw and
gated predicates for b1–b9, loop vectors, adapted Cell A rows) are in the reviewer's `REVISION2_FIXTURE_VALUES.json`
(§0.2); the inputs in this section are normative, the expected outputs are those of the pinned JSON, and the "intended role"
column is design intent only. The reviewer's
gated truth table, copied here for reading convenience and governed by the JSON (G⁰, G¹, cusp, C¹, C², G²):

| b | G⁰ | G¹ | cusp | C¹ | C² | G² |
|---|---|---|---|---|---|---|
| b1 | T | T | F | T | F | F |
| b2 | T | T | F | T | T | T |
| b3 | T | T | F | T | F | T |
| b4 | T | T | F | F | F | F |
| b5 | T | T | F | T | T | T |
| b6 | T | F | F | F | F | F |
| b7 | T | F | T | F | F | F |
| b8 | T | F | F | F | F | F |
| b9 | F | F | F | F | F | F |

Loop closure (reviewer): L0 residual (0,0), total length 8/3; **L1 residual (−1/1500000, −1/1000000)**, not closed, total
length 2000001/750000. The CH1 joins: C² and G² at u=1; C¹ and G¹ but neither C² nor G² at u=2 (acceleration (−4,2) to
(−3,4), curvature 2/25 to 0). For b9 every raw tangent, velocity, acceleration and curvature equality with b2 holds while
the position gap is (1/4,0), so no geometric predicate holds.

**Placement rule P-CHAIN.** Segment k+1 starts at the endpoint of segment k (zero-origin local polynomials are translated by the
preceding endpoint; **no additional gap** is added), unless a fixture lists an explicit gap or translation vector. Segment order is the list order. **Chain parameter** u ∈ [0, m] for m segments: segment
k = min(⌊u⌋, m−1) and local t = u − k, so a joint value u = j belongs to segment j (right-continuous) and u = m is the end of
the last segment (k = m−1, t = 1). Accumulated arc length is the sum of the preceding segments' total lengths plus the local
length.

**Chain CH1 (S5).** seg0: (U,V,h) = (1, t, 1) (PH3), start (0,0). seg1: (1, 1+t, 1) (the same polynomial curve continued).
seg2: (1, 2, 1+t) (constant direction, growing speed). Nine chain parameters u = 0, 1/3, 2/3, 1, 4/3, 3/2, 2, 7/3, 3.
Observables per u: position, unit tangent (sign(h) convention of §3), speed |h|g, accumulated arc length.

**Join inputs (S6).** Segment a = PH3, end generator w_a(1) = (1,1), w_a′(1) = (0,1), h_a = 1, h_a′ = 0. Next segments b
(placement P-CHAIN, start at a's endpoint):

| Id | (U,V,h) of b | Intended role (truth values to be derived by the reviewer) |
|---|---|---|
| b1 | (1+t, 1, 1) | same start generator, different w′ |
| b2 | (1, 1+t, 1) | continuation of a's polynomial curve |
| b3 | (1+t, 1+2t, 1) | same start generator and N_raw(0) as a, different w′ |
| b4 | (2, 2+t, 1) | parallel start generator, different magnitude |
| b5 | (−1, −1−t, 1) | start generator −w (sign gauge) |
| b6 | (1, t, 1) | start generator (1,0) |
| b7 | (1, −1+t, 1) | start generator (1,−1) |
| b8 | (1000000, 1000001+t, 1) | start generator (10⁶, 10⁶+1), near-parallel |
| b9 | b2 translated by (1/4, 0) | explicit position gap |

For C² and G² the reviewer needs w_b′(0) and h_b′(0), which the polynomials above supply (and h_b′(0) = 0 for h_b = 1);
for CH1 seg1→seg2 the derivative of h_c is 1. A predicate is a function of these data; no tolerance is involved.

**Closure inputs.** L0: seg a = PH3 followed by its reversed generator (−V(1−t), U(1−t)), h = 1. L1: the same with the second
segment's h set to 1 + 1/1000000. The closure residual is the exact vector difference of the chain endpoint and start.

No floating-point control is specified in P0. A tolerance comparison could be added only after a separately registered
predicate and normalization are fixed and an independent reviewer supplies literal expectations (§17).

## 10. Oracles and independence

* **O1:** polynomial arithmetic on `Fraction` lists, written fresh: build x′,y′,σ from the generator, integrate for r and S,
  verify x′²+y′²=σ² and dS/dt=σ as *coefficient* identities, evaluate κ from cross(r′,r″)/σ³ independently of the
  generator formula, compute the composite r∘φ by explicit polynomial composition, and decide joins from the control-point
  or coefficient data with the Bézier formulas (not from the generator predicates).
* **O2:** an independently authored second pass: Bernstein form built by exact basis conversion, de Casteljau with
  derivative control points, forward differences computed from a difference table of exact samples, Taylor shift by
  repeated synthetic division, all compared coefficientwise. Candidate helpers never generate their own expectations.
* The reviewer files literal expected outputs for S1–S6 and for every control before execution. Disagreement with a
  candidate is FAIL and stop. The author of the pre-registration is not the fixture reviewer.

## 11. Cost accounting

One instrumented rational class counts every add/sub, mul, div, comparison, gcd call and the raw and reduced bit-lengths
of all intermediates, identically for every arm. Reported separately (never summed into one number): initialization and
conversion (generator → power/Bernstein/difference table, including composite expansion), per-sample cost, observation
cost (the division for T and κ is counted when materialized), serialized state bits, peak live scalars, peak integer
widths (reduced and raw), and cache or table maintenance. Refusals are tabulated by stage. Wall time is secondary
(one warm-up and three timed passes only if included in the invocation budget, median reported descriptively).

**Shared-computation metric (owner's multi-observable hypothesis), corrected in Revision 3.** The earlier definition
telescoped (Σ = cost(S3), so J/Σ = 1 by construction) and is withdrawn. Define, for each arm and each counted category c
(add, mul, div, compare, shift), with **exactly the same output values and the same charged preparation**:

* J_c = cost_joint,c(all S3 observables): one engine produces position, x′, y′, σ, T, the arc-length increments and κ together.
* Σ_c = cost_alone,c(position) + cost_alone,c(S2-only observables {x′, y′, σ, T}) + cost_alone,c(S3-only observables
  {arc-length increment, κ as (N_κ, D_κ)}). Each *standalone* engine starts from the arm's authoritative state and its
  caches, charges every prerequisite it needs (including any generator or intermediate value that a joint engine would
  share), and may use nothing computed by another standalone engine.

An arm *shares computation* in category c if J_c ≤ 0.8·Σ_c. Zero-denominator convention, frozen now: if Σ_c = 0 and J_c = 0
report `n/a`; if Σ_c = 0 < J_c report `UNDEFINED_RATIO`; never substitute a value. Report J_c, Σ_c and J_c/Σ_c per category
and never sum categories. Sharing without a lower absolute J_c than the best conventional arm's J_c is not an advantage.
(Expected structure `[PRED]`: for B-FD the standalone engines keep separate difference tables, so J ≈ Σ; for the generator
arm, U, V, U′, V′ are shared by x′, y′, σ, T and N_κ. Measurement decides.)

## 12. Directed controls and mutants

| Control | Expected result / mutant killed |
|---|---|
| φ′ = 2t in the primitive form | refuse `NOT_PRIMITIVE_RETIMING` (R3); accept in the h-form; a candidate that silently accepts fails |
| φ_ns stationary point | the continued direction d is defined; the actual tangent T = r′/\|r′\| (0/0) and the curvature are refused; a candidate that returns a tangent there, or refuses d, fails |
| non-monotone φ_bad (φ′ changes sign at 1/2) | oriented length B(t) exact (total 0); accumulated length piecewise (total 8/3) refused by the single-polynomial class with `OUT_OF_DOMAIN`; a candidate that reports one polynomial for the accumulated length, or conflates it with the oriented length, fails |
| negative h (reversal in h-form, φ′<0) | unit tangent = −d, speed = \|h\|g, κ = 2N_raw/(\|h\|g²); a candidate using h·g or w²/g without the sign fails |
| non-polynomial retiming (rational φ) | `OUT_OF_DOMAIN` |
| perturbed σ cache with unchanged generator | certificate failure (coefficient identity), not only point checks |
| Inconsistent joins (b9 gap, b8 near-parallel, L1 near-closed loop) | exact predicates classify (the certificate reports the near-miss cross determinant as 1, so G¹ is false); no float comparison is part of P0 |
| Reversal of a reversal | hodograph identity restored; generator equal up to sign |
| E2 jet step forward then backward (harmonic law P′=V, V′=−P, order-4 Taylor step, h=1/4) | the reference is the **operator** M(−h)M(h) − I = (−127/37748736)·I (certificate §F-E; the packet fixed no initial state, so no unique trajectory residual is claimed); a candidate labelling the step exact, or reporting zero for a nonzero state, fails |
| E1b 3-4-5 rotation (3+4i)/5, power k | exact; for k ≥ 1 both reduced entries have denominator 5^k (certificate lists k = 0..16); `ARITH_LIMIT` at the declared width depends on the registered ledger and operation order, which the certificate does not fix; never wrapped |
| E1a C4 word | the rotation entries stay in {0,±1} and R⁴ = I; accumulated positions are sums and are not bounded by this statement |
| Jet order 2 on a cubic | class label E2 (not E0-by-degree); position error nonzero; claiming exactness fails |
| Forward-difference off-by-one order, wrong binomial, dropped h^k, wrong factorial in a Taylor step | coefficient mismatch on a named fixture |
| Chain-rule slip (omit φ′, omit h∘φ), wrong reversal sign, mixed intervals | oracle mismatch on S4 |
| Width ceiling (reduced num/den ≤ 2³¹−1, raw ≤ 2⁶³−1) | atomic `ARITH_LIMIT`, no partial state |
| Cost ledger skipping normalization | ledger inconsistency detected |

Each broken variant needs a fixture that exercises the changed path; a surviving mutant is a test-design failure.

## 13. Gates and falsification

**Correctness gates (hard).** Zero mismatch between every arm and O1/O2 on all admitted inputs; all controls detected
with the specified status; every refusal atomic with state unchanged; artifacts read back and compared.

**Closure claims** are false if a counterexample is found to R1, R2 or R3 by the oracles (the retiming results are proved
here, so an oracle disagreement would indicate a statement error and stops the run).

**Advantage screen (exploratory; not a correctness gate; no statistical claim).** The two predeclared cells are **A**
(random-access multi-observable, primary) and **B** (retimed trajectory, secondary), §9.1. For each cell compare C1 and C2
with the best applicable conventional arm for that cell, each arm holding the §8.1 precomputation and caching rights. A
candidate shows a **Pareto signal** on a cell if some counted category (add, mul, div, compare, serialized state, peak
integer width) is at least 20% below that best conventional arm with no category higher. Shift, normalization and every
other ledger category belong to the no-higher guard; a shift-only improvement does not trigger the signal (P0 contract §2). A lower storage figure with
more arithmetic, or the reverse, is a **TRADE-OFF**, reported as such. A 20% reduction is an exploratory signal that
justifies a further bounded study; it is not proof of general superiority and it cannot rest on a conventional arm that
was denied information the candidate had. Secondary view against the per-category virtual best over the conventional
arms. Cell A is primary: a signal in Cell B alone narrows the conclusion to retiming. **Null:** if on both cells some
conventional arm is no worse than both candidates, the conclusion is "no measured advantage on this workload", with the
structural attribution (shared PH formulas, composition of evaluators, forward differencing). A candidate that matches
B-PH exactly is labelled equivalent to established PH evaluation. S1–S3 and the negative control inform but do not decide.
Tasks S5 and S6 are reported as capability and refusal results, not as screen cells.

**Class honesty gate.** Any output labelled exact from an E2 law, or any E0 claim that depends on A31 residues, is a
FAIL regardless of numbers.

## 14. Smallest recommended pilot (for separate owner authorization) and budget

**QCG-0 P0:** curves PH3 (cubic), PH3h (quartic) and the reviewer-certified quintic PH5; chain of three; **Cell A on PH5; Cell B
on PH3 with φ_sq, plus the φ_bad control**; the mandatory sequential negative control (S1–S3, dyadic step 1/16, 17
samples) on PH3 and PH5; S4 with φ_ns and φ_rev as capability checks; S5 on the three-segment chain; S6 on the designed
joints; the control table of §12; arms B-Horner, B-FD, B-TS, B-Bezier, B-PH, B-COMP, C1, C2. The reviewer-certified
quintic and the reviewer-derived S5/S6 reference values are pinned (§0.2) and are not regenerated. The cost ledger, arm
algorithms, output contracts, width and refusal rules are frozen in `QCG0_P0_EXECUTION_CONTRACT.md`, which must be
independently reviewed before any candidate code exists or any cost is evaluated. P0 remains HOLD.

Proposed budget (a proposal, not GO): one invocation, 60 s externally enforced, 1 GiB address space, no child
processes/network/devices/installs, ≤1,000,000 counted operations, 4096-bit reduced coefficients, 16384-bit raw
temporaries, 10 MiB output, zero retries. Launch shape as in `X2_P0_READINESS_PACKET.md` §7, with
`/usr/bin/timeout --signal=KILL 60 /usr/bin/python3 -I research/qcg_0/run.py --out build/qcg_0/run_01` after
`mkdir build/qcg_0/run_01` (no `-p`). Non-launching prerequisites (as probed for X2 on 2026-10-22: `/usr/bin/timeout`
present, `/usr/bin/time` absent and unused, Python 3.14.8 starts under `ulimit -v 1048576`, output leaf absent) are to be
re-verified before any GO. Inability to complete is a resource outcome, not permission to split. Freeze before GO:
this document's hash, the reviewer-filed fixture values, the arm algorithms, the control table, the ledger definition,
the command and the budget. Save full states (generators, coefficients, tables, jets, chain data, outputs) as versioned
UTF-8 JSON with canonical rational pairs and copy final artifacts from the gitignored `build/` into `research/qcg_0/`
after review.

## 15. What would be new

Relative to established PH algorithms: **nothing at the formula level.** The identities, polynomial arc length, rational
unit tangent and curvature, and the generator algebra are standard `[LIT]`/`[MATH]`. B-PH already uses them.
Relative to conventional exact polynomial forward differencing: nothing for sequential uniform sampling; FD is
expected to win it.

Candidate novelty, each testable and each possibly empty:
1. a **typed law interface** (E0/E1/E2) whose refusals make exactness claims checkable by a machine, including the
   h-form retiming algebra (R1–R5) as a first-class operation with closure and reversal;
2. a **shared-observable** representation in which direction (τ) and timing (σ) are separate state, giving tangent,
   speed, arc length, curvature and constraint predicates from one stored generator (measured by J_c/Σ_c, §11);
3. **E1 orbits** for turning (finite groups, Cayley/Pell structure) giving bounded-growth composed motion, if the
   Q(√3) profile is later authorized;
4. whether the Cauchy-product jet substrate adds anything over the shift and difference tables that conventional
   engines already have.
If none of these shows a measurable benefit, the result is the useful negative that curve and motion generators do not
need a native SPU primitive, and attention returns to X2.

## 16. Open questions and not done

Open: (a) completeness is **not open**: it is independently proved over Q by the reviewer (§3, closure ledger); what
remains is the implementation question of how a harness chooses between h = 1 and a polynomial h, and that h = 1 is not
always possible; (b) the PH5 fixture and the §9.2 reference values are derived by the independent reviewer (§0.2), still
conditional on the corrections of §18 being accepted at re-inspection; (c) resolved: Cells A and B (§9.1); (d) Q(√3) profile
for E1b/C12; (e) a mathematically fixed float-tolerance control, if ever wanted; (f) the cost ledger, arm algorithms and
refusal behaviour, which no reference value fixes; (g) the storage and peak-width categories of the Pareto screen, which
the arithmetic predictions do not address.

Not done: no pilot code, no candidate engines, no oracle of record, no experiment, no re-inspection of Revision 3 by the
reviewer yet, no X2 or QSG-2 change. Execution HOLD until the corrections are accepted and the owner authorizes P0.

## 17. Revision 2 change log and superseded packet items

| # | Review finding / owner item | Change | Where |
|---|---|---|---|
| 1 | Curvature factor of two | N_raw = UV′−U′V retained for provenance; curvature numerator N_κ = 2N_raw, D_κ = \|h\|g²; Cell A pair and §8.1 use N_κ; values file unedited with the factor stated | §3, §8.1, §9.1 |
| 2 | Negative-h semantics | speed \|h\|g; T = sign(h)·w²/g; κ = 2N_raw/(\|h\|g²); stationary points (T and κ refused, d defined); reversal | §3, R2, R4, §12 |
| 3 | Preserve the certified quintic | U, V, h and all values pinned by full hash, quoted from the certificate, not regenerated | §0.2 |
| 4 | Completeness | `[LIT]` replaced by the reviewer's independent proof with scope and assumptions (h polynomial, not necessarily positive or constant) | §3, closure ledger |
| 5 | Oriented versus accumulated length | R6 added; Cell B control text and §12 corrected | R6, §9.1, §12 |
| 6 | Missing S5/C²/G² inputs | translations (P-CHAIN), order, chain parameter, derivative data, closure inputs specified; no expected values invented | §9.2 |
| 7 | Float-tolerance claim | removed (arm, S6 sentence and control row); a replacement requires a separate registration | §8, §9.2, §12 |
| 8 | E0 / E1 / E2 distinct | §6 unchanged; harmonic E2 reference restated as an operator; E1a wording narrowed | §6, §12 |
| — | Also from the certificate | S3 endpoint convention frozen; G⁰ is two rational equalities in the plane (§5); K1 sparsity remark narrowed (below); Cell A hand counts recomputed for the certified degrees | §9, §5, §8.1 |

**Packet items superseded by this revision (packet not edited).** (i) F-A and F-B called (N, D) with N = UV′−U′V "the
curvature pair": the true numerator is 2N_raw (§3). (ii) K1 "no arm gains from sparsity": K1 makes the generator
coefficients dense only; derived polynomials are not dense (x has degree 4, y degree 5, x′ degree 3, and N_raw has a zero
constant term). This follows from the frozen rule and is not grounds to replace the fixture; the frozen Horner policy
counts by degree (§8.1) and a sparse-aware count is reported separately. (iii) The float64 misclassification expectation:
withdrawn, since a 10⁻⁶ closure residual is rejected by an absolute 10⁻⁹ tolerance even in floating point and the near-miss
determinant is 1; any numerical control needs a fixed predicate and normalization first.

## 18. Revision 3 change log (documentation only; Revision 2 text hash `fbaf2b5a…ec4f42`)

| # | Reviewer finding (REVISION2_REVIEW_CERTIFICATE.md / DEGREE_ADDENDUM) | Change | Where |
|---|---|---|---|
| 1 | Shared-cost metric telescopes (J/Σ = 1) | withdrawn; Σ is the sum of three *standalone-output* costs, J the joint cost, per category, with a frozen zero-denominator rule | §11 |
| 2 | Continuity predicates not gated | raw equalities and geometric predicates separated; G⁰ gates all, G¹ = G⁰∧R_dir, cusp = G⁰∧R_opp, C¹ = G⁰∧R_vel, C² = C¹∧R_acc, G² = G¹∧R_κ; b9 and b7 called out; reviewer's gated table quoted | §5, §9.2 |
| 3 | Sign-changing h does not generally retrace | universal retracing claim removed; counterexample h=t, U=1, V=t recorded; φ_bad retraces for its own reason | §3 |
| 4 | §16(a) called completeness unproved | replaced by the independently proved status and the remaining implementation question | §16 |
| 5 | Hand counts overstate the screen | wording limited to the two arithmetic categories; other categories unmeasured; shift counting frozen for every arm | §8.1 |
| 6 | Stationary row, S_or, P-CHAIN, "only computation" | continued direction d vs refused T; S_or defined; "no additional gap"; computation statement qualified | §12, R2, §9.2, header |
| 7 | PH3h is quartic | PH3 cubic, PH3h quartic with its polynomials; exact jet order ≥ 4 | §7, §9, §14 |
| — | Reference values | Revision 2 review artifacts pinned by full hash; the reviewer's values are referenced, not copied except the small truth table | §0.2, §9.2 |

Unchanged: all certified values, the Revision 1 and Revision 2 review artifacts, the review packet, and every other campaign.

**Revision 3.1 (editorial, 2026-10-23, after the Revision 3 PASS):** the 28/27 route is relabelled B-Horner and the 26/23 route
the factored route of B-PH and C1 (the earlier label put 28/27 on B-PH); stale status sentences in §9.2 and §14 updated;
`J/Σ` shorthand indexed; the §13 guard now names shift. No certified value or mathematical statement changed.
