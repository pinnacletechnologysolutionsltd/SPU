# SPU Lexicon — Normative Vocabulary

The single source of truth for SPU-coined terms and adopted mathematical
vocabulary. Every term used in a paper, README, or outreach letter must have
an entry here; papers cite the literature line of the entry, not folklore.

**Entry discipline:**
- **Definition** — precise, one to three sentences, math where needed.
- **SPU convention** — the exact bit-level / RTL / oracle convention, which
  may be narrower or different from the literature.
- **Literature / Divergence** — the standard name and source if one exists,
  and an explicit statement of where SPU usage differs. Divergences are not
  errors; *undocumented* divergences are.
- **Anchors** — RTL, oracle, and knowledge-doc locations, so the entry rots
  loudly instead of silently.
- **Status** — `settled`, or `OPEN:` with the specific question that needs a
  human decision (these form the formalization worklist).

Attribution of ideas lives in `docs/ATTRIBUTION.md`; this file fixes
*meanings*. CC0 1.0, like the rest of `knowledge/`.

---

## Coordinate systems & geometry

### Quadray coordinates
**Class:** coordinate system.
**Definition:** four-axis coordinates (a, b, c, d) on basis vectors pointing
to the vertices of a regular tetrahedron (60° inter-axis angles), addressing
the IVM lattice.
**SPU convention:** SPU-4 registers hold **signed** 16-bit components A–D.
The working representative is the **zero-sum hyperplane** (ΣABCD = 0),
enforced continuously by the Davis Gate rather than at load time; Urner's
`min = 0` canonical form is never constructed or restored anywhere in the
RTL (no normalization block exists). Test fixtures and the rotor path use
signed values freely.
**Literature:** Kirby Urner (from Fuller's synergetics), basis matrix by Tom
Ace (1997). Urner's canonical form requires `min(a,b,c,d) = 0` with
non-negative coordinates.
**Divergence:** the SPU and Thomson's SQR both drop Urner's canonical-form
constraint (min=0, non-negative), but they diverge on what replaces it.
Thomson SQR §4 explicitly works in **full R4** — "no zero-sum projection"
(storage commitment #1, confirmed 2026-07-09 against _Quadray-Rotors-v5_).
The SPU works **on the zero-sum hyperplane** (ΣABCD = 0 enforced
continuously by the Davis Gate) with signed 16-bit components — a genuine
architectural divergence, not an alignment. Note the semantic shift:
the zero-sum representative addresses *vectors* (displacements), whereas
Urner's canonical form addresses *points*. **Fixed 2026-07-09:**
`MATHEMATICAL_FOUNDATIONS.md` §2 and §6 previously presented the min=0
canonical form as if it were SPU's operative convention — corrected to
state Urner's literature convention and the SPU divergence separately,
citing this entry as the RTL contract rather than competing with it.
**Anchors:** `hardware/rtl/core/spu4/spu4_euclidean_alu.v`,
`hardware/rtl/core/shared/spu_quadray_regfile.v`,
`hardware/rtl/core/shared/davis_gate_dsp.v`,
`knowledge/MATHEMATICAL_FOUNDATIONS.md` §6.
**Status:** settled (2026-07-08, resolved from RTL evidence: the Davis Gate
zero-sum test is the only normalization the hardware asserts). **Resolved
2026-07-09:** confirmed against Thomson's *Quadray-Rotors-v5* §4 — Thomson
explicitly works in full R4 ("no zero-sum projection"), so the SPU's
zero-sum hyperplane storage is a genuine architectural divergence, not an
alignment. Both drop Urner's canonical form; they diverge on what replaces it.

### Spread-Quadray Rotor (SQR)
**Class:** operator algebra.
**Definition:** Thomson's 4D rotor algebra native to the tetrahedral basis —
rotations expressed directly on Quadray 4-tuples without passing through a
Cartesian embedding; synthesis of Fuller (geometry), Wildberger (rational
trigonometry), and Urner (coordinates).
**SPU convention:** a rotor is carried as a packed pair `{Ra[31:0],
Rb[31:0]}` in Q12 fixed point; Janus polarity is an explicit Z₂ flag
p ∈ {+1, −1} per rotor (Thomson SQR §9). The RPLU uses the division-free
SQR constraint form.
**Literature:** Andy Ross Thomson, *Quadray-Rotors-v5.pdf* (May 2026);
per `MATHEMATICAL_FOUNDATIONS.md`, the SQR paper does **not** specify
fixed-point field arithmetic — the Q12 packing and field choices are SPU
additions.
**Divergence:** fixed-point width, packing, and the M31/A31 field embedding
are SPU-specific; cite Thomson for the algebra, SPU docs for the encoding.
**Anchors:** `hardware/rtl/core/shared/spu_cross_rotor.v`,
`software/lib/quadray_variety.py`, `knowledge/RATIONAL_CURVES_SPEC.md`.
**Status:** settled (encoding, 2026-07-09). §-references confirmed against
Quadray-Rotors-v5: §5 (Simplicial Rodrigues), §6 (F/G/H circulant),
§7 (opposite-edge axes), §9 (Janus polarity), §10 (fixed-axis primitives).
Note the SPU's zero-sum hyperplane storage is a divergence from Thomson's
R4 storage model (see Quadray coordinates entry). Cite Thomson for the
algebra, SPU docs for the encoding.

### IVM / Vector Equilibrium (13-axis)
**Class:** lattice / architecture rationale.
**Definition:** the isotropic vector matrix (CCP sphere packing); the
cuboctahedron ("Vector Equilibrium") is its local coordination shell. The 12
vertices + center give the 13 axes of the SPU-13 manifold representation.
**SPU convention:** 13 axes × RationalSurd components; the manifold is the
register-file-level object (832-bit burst in `spu13_core`).
**Literature:** Fuller, *Synergetics*; standard crystallography name is CCP/FCC.
**Divergence:** none in the geometry; the 13-axis *register* representation
is SPU-original.
**Anchors:** `hardware/rtl/core/spu13/spu13_core.v`,
`knowledge/MATHEMATICAL_FOUNDATIONS.md` §6.
**Status:** settled.

### Jitterbug transformation
**Class:** dynamic geometric transformation.
**Definition:** Fuller's continuous deformation of the vector equilibrium
(cuboctahedron, 12 vertices) through the icosahedron to the octahedron
(6 vertices) and back — a structural *motion*, not a static shape.
**SPU convention:** implemented as an 8-phase Pell-orbit interpolation:
even-indexed axes expand while odd-indexed axes contract at the
complementary orbit step; phase 0 = VE (equal scale), phase 2 =
icosahedron (crossover, equal Pell weight both rings), phase 4 =
octahedron (odd axes at minimum scale); the nucleus (QR[12]) is fixed.
Exact in Q(√3) throughout — no interpolation error at any phase.
Hardware: `OP_JITTER` is a pure 60° wire permutation
`(a,b,c,d)→(c,a,b,d)`, 1 cycle, 0 multiplies.
**Literature:** R.B. Fuller, *Synergetics* (1975) — the jitterbug model,
built from a physical strut-and-hinge cuboctahedron demonstrating the VE
as a transformable, not fixed, structure.
**Divergence:** none in the geometry; the Pell-orbit phase parameterization
and the fixed-nucleus convention are SPU-specific.
**Anchors:** `software/common/include/spu_physics.h` (`JitterbugState`,
`jitterbug_step`, `jitterbug_apply`), `hardware/vendor/gowin/spu_alu_gowin.v`
(`OP_JITTER`), `software/common/tests/spu_physics_test.cpp`,
`software/lib/sovereign_lut.py`, `knowledge/SYNERGETICS_BEYOND_GEOMETRY.md`.
**Status:** settled — the most mature non-static-geometry synergetics
content in the codebase; C++ oracle TB-verified (8-step closure,
reversibility, icosahedron crossover), hardware opcode implemented.

## Number systems & fields

### RationalSurd
**Class:** data type.
**Definition:** an element P + Q·√3 of Q(√3), the minimal field closed under
IVM/hexagonal geometry (cos 60° = 1/2, sin 60° = √3/2).
**SPU convention:** packed 32-bit word — upper 16 bits P, lower 16 bits Q,
both signed 16-bit. Never encode constants as raw signed decimal literals;
use explicit bit-packing (identity `{16'd..}` style per CLAUDE.md).
Wider paths use {P18,Q18} (e.g. SOM features) or {P32,Q32}.
**Literature:** standard real quadratic field Q(√3); "surd" is the classical
term for an irrational root.
**Divergence:** none mathematically; the packing is SPU-specific.
**Anchors:** `hardware/rtl/arch/` defines, `software/spu_vm.py`,
`knowledge/MATHEMATICAL_FOUNDATIONS.md` §3.
**Status:** settled.

### A₃₁
**Class:** algebra (ring).
**Definition:** the 4-dimensional algebra over F_p, p = M31 = 2³¹−1, with
basis [1, √3, √5, √15] — i.e. F_p[x,y]/(x²−3, y²−5). Not a field: it has
zero divisors (norm-zero elements such as (√15, 0, 0, 1)-scalings).
**SPU convention:** elements are 4×32-bit component vectors (z0..z3);
"unit" means multiplicative norm ≠ 0; the norm check is the FLAGS.V
mechanism.
**Literature:** standard construction (biquadratic étale algebra over F_p);
the name "A₃₁" is SPU-coined.
**Divergence:** name only.
**Anchors:** `software/lib/a31_field.py`,
`hardware/rtl/core/spu13/spu13_m31_multiplier.v`.
**Status:** settled.

### Lucas Phinary
**Class:** number system.
**Definition:** arithmetic in Z[φ]/L_p — golden-integer arithmetic reduced
modulo a Lucas prime, with Barrett-style reduction; supports exact
φ-scaling (PSCALE), chirality (PCHIRAL), multiply (PMUL), inverse (PINV).
**SPU convention:** see opcode semantics in `knowledge/LUCAS_PHINARY_MAC.md`
(ring separation and the Barrett bridge are normative there).
**Literature:** Z[φ] is the ring of integers of Q(√5); "phinary" echoes
Bergman's base-φ numeration, but SPU usage is modular ring arithmetic, not
positional numeration.
**Divergence:** "phinary" in the literature usually means base-φ *positional
representation*; SPU means the *quotient ring*. Say "Lucas phinary ring" in
papers to avoid the collision.
**Anchors:** `hardware/rtl/core/spu13/spu13_lucas_mac.v`,
`software/tests/test_lucas_mac_oracle.py`, `knowledge/LUCAS_PHINARY_MAC.md`.
**Status:** settled.

## Invariants & stability

### Quadrance / Spread
**Class:** metric vocabulary.
**Definition:** Wildberger's rational-trigonometry replacements for
distance² and angle: quadrance Q(A,B) is the squared separation; spread
s(ℓ₁,ℓ₂) ∈ [0,1] is the squared sine of the angle between lines. Both are
rational in rational inputs.
**SPU convention:** BMU classification distance is a *weighted field
quadrance* over RationalSurd features (exact, no square roots); tie-breaking
is deterministic by node index.
**Literature:** N.J. Wildberger, *Divine Proportions* (2005).
**Divergence:** none; SPU extends evaluation to Q(√3) field-squared form.
**Anchors:** `software/lib/rational_som.py`,
`hardware/rtl/core/spu13/spu_som_bmu.v`, `programs/wildberger_*.lith`.
**Status:** settled.

### Davis Ratio / Davis Gate / Henosis
**Class:** hardware invariant + recovery mechanism.
**Definition:** the per-cycle exact zero test ΣABCD = 0 (quadrance identity
over the four Quadray components). A nonzero sum is a "cubic leak."
Henosis is the one-cycle soft-recovery pulse triggered instead of a hard
reset.
**SPU convention:** exact integer zero test, never an epsilon comparison.
In RTL the tested quantity is `gasket_sum` — the sum of the four signed
16-bit components truncated to 16 bits, so the literal test is
ΣABCD ≡ 0 (mod 2¹⁶). An aliased leak of exactly ±k·2¹⁶ therefore reads as
zero; this is acceptable under the corruption model below but must be
stated when the gate is described as "exact."

**Lemma (sum invariance).** Write S(q) = A+B+C+D for a Quadray register
q = (A,B,C,D) with exact signed components. Every hot-path operation
preserves the zero-sum subspace {S(q) = 0}:
1. *Permutation rotations* (ROTC angles 2, 5 — the P5 bypasses) permute
   components, so S is unchanged.
2. *Circulant rotations* (ROTC angles 0, 1, 3, 4) with coefficients
   (F, G, H): each input component contributes to the outputs with total
   weight F+G+H, so S(Rq) = (F+G+H)·S(q). Every angle in the corrected
   catalog has **F+G+H = 1** (identity 1+0+0; thirds ⅔+⅔−⅓ = −⅓+⅔+⅔ =
   ⅔−⅓+⅔ = 1; the P5 rows are permutations). Hence S(Rq) = S(q).
3. *Linear ops*: S(q₁ ± q₂) = S(q₁) ± S(q₂) and S(k·q) = k·S(q), so
   zero-sum operands yield zero-sum results.

By induction, if every value *loaded* into the Quadray register file is
zero-sum (the toolchain obligation on QLDI immediates and boot hydration),
then S = 0 holds at every cycle of correct execution. A nonzero gasket sum
("cubic leak") therefore cannot be produced by correct execution — it
witnesses state corruption (e.g. an SEU), arithmetic wrap/overflow, or a
non-zero-sum load. This is why the Davis Gate is an **integrity check on
the machine, not a convergence check on the algorithm**, and why the exact
zero comparison (rather than an epsilon) is the correct test. Henosis, the
one-cycle recovery pulse, restores a zero-sum state rather than resetting.

**/3 divisibility — resolved 2026-07-08, and it is NOT automatic (real
finding, not a formality).** The thirds angles (1, 3, 4) compute an
integer circulant sum (e.g. angle 1: `2B − C + 2D`) then divide by 3 via
`div3` in `spu13_rotor_core_tdm.v` — the exact Hacker's-Delight
magic-constant algorithm (`n * 0x55555556`, take upper bits, sign-adjust).
This computes **true floor division**, not a divisibility check: it
never errors, never flags, and silently returns a truncated result when
the numerator isn't a multiple of 3. The VM (`spu_vm.py`) uses the
identical construction, so VM-vs-RTL trace equivalence passes even when
truncation occurs — that test proves hardware/software agreement, not
mathematical exactness against the intended 2/3, 2/3, −1/3 fractions.

**Proven condition:** on the zero-sum invariant (ΣABCD = 0), substituting
C = −(A+B+D) into the angle-1 sum gives `2B−C+2D = A + 3B + 3D ≡ A (mod 3)`
— i.e. **the rotation is exact iff the axis held invariant by that
circulant (A) is ≡ 0 (mod 3)**, independent of B, C, D. Confirmed
empirically (not just algebraically) with a genuine zero-sum
counterexample: `A=1, B=1, C=1, D=−3` (sum 0, A≢0 mod 3) — Q12-scaled
pre-div3 sum is −20480, not a multiple of 3; `div3` returns −6827
against a true value of −6826.667, a real, silent 1/3-unit (pre-scale)
error with zero indication anything went wrong. This would also violate
the sum-invariance lemma above in exactly this case, since the proof
assumed the exact F+G+H=1 combination, not a truncated one.

**Why every existing test missed this:** the canonical VM-vs-RTL trace
vector (`test_rotc_vm_rtl_trace.py`) is `A=1,B=2+2√3,C=3+3√3,D=4+4√3` —
not zero-sum at all (sum = 10+9√3), and it passes divisibility only
because 2,3,4 are consecutive integers (`2n−(n+1)+2(n+2) = 3(n+1)`,
always a multiple of 3 for any consecutive triple, a coincidence of the
chosen numbers, not a structural guarantee). The six-step silicon
closure (13/13 PASS) exercises whatever specific residues that program's
literal operands happen to have — not a residue sweep. **No existing
test has ever exercised a zero-sum state with a bad residue.** This is
an untested code path with a demonstrated failure mode, not a proven-safe
corner.

**Status: fix RTL-complete 2026-07-09, silicon pending.** The deferred-reduction
exponent-tagged ROTC core (`spu13_rotor_core_tagged.v`, 314 lines) implements
the full state machine from `docs/ROTC_EXPONENT_STATE_MACHINE.md` with
explicit fault flags (MISALIGNED/OVERFLOW/INEXACT). TB passes 9/9
acceptance tests (verified 2026-07-16). Tang 25K probe (`spu13_tang25k_rotc_tagged_probe.v`)
built and bitstream produced — awaiting board flash. The original TDM core
(`spu13_rotor_core_tdm.v`) with silent `div3` remains the silicon baseline
until the tagged core has its own silicon evidence entry. Do not claim
"ROTC thirds angles are exact" without noting which core was used.

A first proposed root-cause fix ("thirds-native global unit" — every raw
Quadray integer implicitly 3× the classical step, claiming `div3` cancels
structurally) was **wrong and has been retracted**: applying the integer
coefficients to an already-scaled input produces a 9×-scaled output, not
3×, because the coefficients themselves already carry the factor being
divided out — a fixed uniform rescaling cannot absorb a
multiplicative-per-application effect. Caught by building the oracle
before writing anything else (`software/lib/rotc_thirds_native.py`,
`rotate_no_div_DEAD_END`, kept as a permanent negative-result trail).

A **verified working** fix exists: a deferred-reduction, exponent-tagged
representation — state carried as `(value, exponent)`,
`true_value = value / 3^exponent`, raw integer coefficients applied
directly with the exponent incremented per rotation, division deferred
to an explicit renormalization point rather than eliminated. Cross-verified
against the exact ground truth across a real 4-step multi-axis
composition chain (`rotate_tagged`/`reduce_tagged`,
`software/tests/test_rotc_thirds_native.py`, 69 checks incl. ALIGN and a
genuine INEXACT fault case). This is a real ISA extension (register
exponent field, exponent-alignment for combining mismatched values) —
same shape as the sparse jet MAC's nilpotency tags. **Formal state
machine specified 2026-07-08:** `docs/ROTC_EXPONENT_STATE_MACHINE.md` —
states (CLEAN/PENDING/FAULT.{MISALIGNED,OVERFLOW,INEXACT}), transitions
(ROTATE/ALIGN/REDUCE), proven guaranteed-safe reduction points
(period-6 closure; single-axis chains under the original precondition).
**RTL implemented 2026-07-09:** `hardware/rtl/core/spu13/spu13_rotor_core_tagged.v`
(314 lines, 4-bit exponents, powers-of-3 LUT, signed-division exactness
check, sticky fault flags). Testbench `hardware/tests/spu13/spu13_rotor_core_tagged_tb.v`
covers the full §7 acceptance checklist — 7 tests, all PASS. Remaining:
FLAGS semantics in `knowledge/isa_reference.md` and golden vector
re-verification under the tagged representation.

Recommended now, independent of that decision: ship the cheap exactness
flag (§2(a) of the fix doc; `div3`'s remainder is nearly free to expose,
same house idiom as A₃₁'s FLAGS.V). Do not claim "ROTC thirds angles are
exact" in any paper or outreach material without this caveat until
either lands. AGENTS.md's "all 6 corrected ROTC angles pass" is true for
the tested vectors and
does not contradict this finding — it is narrower than it may read.

**Literature:** the zero-sum hyperplane constraint appears in Urner's
Quadray normalization; "Davis Ratio," "cubic leak," and "Henosis" are
SPU-coined (attribution: Bee Davis, per `docs/ATTRIBUTION.md`).
**Divergence:** SPU-coined names for an SPU-specific runtime invariant.
**Anchors:** `hardware/rtl/core/shared/davis_gate_dsp.v`,
`hardware/rtl/core/shared/spu_proprioception.v` (accumulates |gasket_sum|
per burst), `software/tests/test_rotc_vm_rtl_trace.py`.
**Status:** sum-invariance lemma proven and settled (2026-07-08).
(1) **/3 divisibility — PROVEN NOT TO HOLD UNCONDITIONALLY, 2026-07-08.**
This was expected to be a formality; instead it surfaced a real, currently
unmitigated correctness gap — see the full derivation and reproducible
counterexample directly below. Thirds-angle ROTC rotations silently
truncate (no fault, no flag) whenever the invariant axis isn't ≡ 0 (mod 3),
and no existing test exercises that case. Open until an exactness flag or
equivalent guard lands — do not claim unconditional ROTC-thirds exactness
in outreach material until then.
(2) **Quadrance/severity split — RESOLVED 2026-07-08.** All three layers
now agree on 4Σcᵢ² = ivm_quadrance + gasket_sum² as the leak-severity
formula: C++ oracle (`spu_physics.h`), Python VM (`DavisGasket.gasket_tick`),
and RTL (`davis_gate_dsp.v` quadrance port). The testbench
(`davis_gate_dsp_tb.v`) derives expected values from oracle functions,
not from the RTL implementation. The gasket-sum path was and remains
unaffected throughout.

### Stiffness (K) / Tension (τ) / Davis Ratio
**Class:** stability-model quantities.
**Definition:** from the Davis field equation **C = τ / K** — inference
capacity equals tolerance divided by curvature barrier. In the SPU:
**tension τ** is the accumulated severity of cubic leaks — it grows by the
quadrance of the manifold vector-sum on each leaking tick and halves
exactly (integer `>>1`, the ANNE mechanic) on stable ticks; **stiffness
K** is a fixed hardware constant (default unity) setting how much tension
the manifold tolerates per unit capacity. The intended reading is the
**mechanical / Hookean** sense — a spring constant, resistance of the
manifold to deformation under tension — not any numerical-analysis sense.
**SPU convention:** τ and K are RationalSurds; K defaults to unity
`{1, 0}`. No division anywhere: Davis Ratios are compared by
cross-multiplication (τ₁·K₂ vs τ₂·K₁), per `spu_ivm.h`'s `davis_ratio()`
and `DavisGasket::ratio_product()`.
**Literature:** C = τ/K is Bee Davis's Davis Framework
(`MATHEMATICAL_FOUNDATIONS.md` §5, attribution in `docs/ATTRIBUTION.md`).
**Divergence — outreach hazard:** in mainstream computational mathematics
"stiffness" means stiff ODE systems (widely separated timescales forcing
implicit integrators) or, loosely, ill-conditioning. SPU stiffness is
**not** that; a reviewer will bring the wrong prior. Papers must say
"stiffness constant K (in the Hookean sense)" on first use. Do not import
numerical-stiffness definitions into SPU docs. House usages to rephrase in
paper-facing text: "stiff pipeline" → "fixed-latency pipeline"
(`LITHIC_L_DEEP_DIVE.md`); "SQR stiffness requires recalibration"
(sentinel TB message) → informal, keep out of papers.
The `quadrance` output of `davis_gate_dsp.v` is now the Davis stiffness
4Σcᵢ² = ivm_quadrance + gasket_sum² (see Davis Gate entry, resolved 2026-07-08).
**Anchors:** `software/common/include/spu_physics.h` (DavisGasket),
`software/spu_vm.py` (DavisGasket, ~line 670),
`hardware/tests/common/davis_gate_dsp_tb.v`.
**Status:** settled (definition, Hookean sense, 2026-07-08). The τ
accumulation formula uses the positive-definite leak-severity form
4Σcᵢ² = ivm_quadrance + gasket_sum², aligned across all three layers
(C++ oracle, Python VM, RTL) as of 2026-07-08.
**K — implemented vs. roadmap (resolved 2026-07-08, John):**
*Implemented:* K is a fixed RationalSurd denominator in Davis Ratio
comparisons; every bitstream through first SPU-4 silicon holds K = unity
as the flat baseline reference. K appears nowhere in the hot path — the
gasket-sum invariant ΣABCD = 0 is K-independent by construction, so the
sum-invariance lemma holds for any K.
*Roadmap:* K is architecturally dynamic — a **scale-calibration
constant**. Precise statement (homogeneity argument): tension τ is
quadrance-valued, so under uniform rescaling of the coordinate grid by
λ, τ scales by λ²; choosing K ∝ λ² keeps C = τ/K invariant. Calibrating
K therefore means matching the tension tolerance to the metric density
of the grid, without touching topology or any structural invariant.
*Claim discipline:* no oracle, RTL, or test exercises non-unity K yet —
papers say "held at unity for baseline validation" and claim nothing
about dynamic-K behavior. Dynamic K in the datapath requires its own
contract (where K enters, what it multiplies) before this entry may
assert it. Physical-substrate analogies (e.g., photonic refractive-index
bias as a K analogue) are direction-level and live in
`docs/PHOTONIC_JET_RING_NOTES.md`, not here. Davis's own term for K is
"curvature barrier" — cite that phrase; avoid bare "curvature" in
paper-facing text (wrong differential-geometry prior).

## Timing

### Piranha Pulse / Fibonacci-gated dispatch
**Class:** timing architecture.
**Definition:** the system reference pulse (design target 61.44 kHz =
60 × 1024 Hz); instructions dispatch at offsets 8/13/21 within a 34-cycle
Sierpinski frame. Deliberate design constraint — timing deviations are
design flaws, not artifacts to buffer away.
**SPU convention:** `spu_sierpinski_clk.v` counts a 34-cycle frame and
fires phi_8/phi_13/phi_21 single-cycle pulses that gate the sequencer.
Claim discipline: 61.44 kHz is the **sovereign-domain design target**; the
implemented Sierpinski frame rate is clk_fast/34 (≈705.9 kHz at 24 MHz),
and 61.44 kHz is not integer-derivable from 24 MHz (closest ÷391 ⇒
61.381 kHz, −0.09%). Papers must not state 61.44 kHz as the implemented
rate — cite `CLOCK_ARCHITECTURE.md` §2.3–2.4 for target vs. realized.

**Why Fibonacci intervals (the citable paragraph):** the dispatch offsets
8, 13, 21 and the frame length 34 are consecutive Fibonacci numbers, so
every ratio between dispatch events is a convergent of φ. Three
engineering properties follow. (1) **Determinism** — dispatch is a fixed
function of a free-running 34-state counter: no arbitration, no
data-dependent stalls, so instruction timing is reproducible
cycle-for-cycle. (2) **Non-resonant switching** — φ is the irrational
number worst-approximated by rationals (all continued-fraction terms are
1), so dispatch events avoid low-order rational alignment with the frame
period; switching activity spreads across the spectrum instead of
stacking on one harmonic. (3) **Algebraic coherence with the datapath** —
φ is already a native constant of the machine (the Z[φ]/L_p Lucas MAC),
so timebase ratios and datapath constants live in the same ring, and
φ-scaling across timing and arithmetic is exact rather than approximate.
Claims beyond these three (numerological identities in older notes, e.g.
"76/34 ≈ √5") are **not citable** in paper-facing text.

**Literature:** none (SPU-coined names); the low-discrepancy property of
φ-spaced events is the standard three-distance/Weyl equidistribution fact.
**Anchors:** `hardware/rtl/top/spu_sierpinski_clk.v`,
`knowledge/CLOCK_ARCHITECTURE.md`.
**Status:** settled (2026-07-08 — names, rationale, and target-vs-realized
rate discipline).

## Jet / series vocabulary (2026-07 additions)

### Jet ring J_N
**Class:** algebra (local ring).
**Definition:** J_N = A₃₁[ε]/(ε^{N+1}) — truncated polynomial (jet) algebra;
multiplication is the Cauchy product with ε^{N+1} = 0. Units are exactly
the jets whose ε⁰ component is an A₃₁ unit.
**Literature:** standard jet/truncated-power-series construction; N=1 case
is dual numbers.
**Divergence:** none; base ring choice is SPU-specific.
**Anchors:** `software/lib/jet_ring_N.py`,
`hardware/rtl/core/spu13/spu13_jet_mac.v`, `docs/SPARSE_JET_MAC.md`.
**Status:** settled.

### Nilpotency window tag [lo, hi]
**Class:** hardware operand metadata.
**Definition:** a promise that all ε-channels of a jet outside lo..hi are
zero; the sparse jet MAC skips guaranteed-zero base products using tags
only (value-blind, data-independent timing). Tag algebra:
r_lo = lo_A + lo_B (clamped), r_hi = min(N, hi_A + hi_B).
**Literature:** none (SPU-coined, 2026-07-08).
**Anchors:** `docs/SPARSE_JET_MAC.md` §2–3.
**Status:** settled by contract; RTL pending.

### Digon-recursive schedule
**Class:** evaluation strategy.
**Definition:** evaluation of the Wildberger–Rubine hyper-Catalan series
over the subdigon type lattice in V-then-lexicographic order, with
incremental power reuse; "series stream" is the RTL realization
(static schedule ROM).
**Literature:** subdigon/hyper-Catalan combinatorics: Wildberger & Rubine,
*A Hyper-Catalan Series Solution to Polynomial Equations, and the Geode*
(2025). The lattice-walk scheduling is SPU-original.
**Anchors:** `software/lib/digon_recursive.py`,
`hardware/rtl/core/spu13/spu13_series_stream.v`,
`docs/SERIES_STREAM_CONTROLLER.md`.
**Status:** settled.

## Cluster & network vocabulary

### Determinism boundary
**Class:** architecture principle.
**Definition:** the SPU's timing guarantees (Fibonacci dispatch,
deterministic cycle counts, bit-exact replay) end at the FPGA pins. Every
transport beyond the pins — MCU, USB, radio, IP — carries frames
*unchanged in content* but adds nondeterministic latency; bridges relay
frames, they never extend timing claims. Corollary: clusters are
**coherence-aligned, not cycle-aligned** — cross-node ordering comes from
frames (sequence, dissonance), never from shared clock phase, and papers
must not imply lockstep across boards.
**Literature:** none (SPU-coined, 2026-07-08); the underlying idea is the
standard synchronous-island / GALS (globally asynchronous, locally
synchronous) decomposition.
**Anchors:** `knowledge/INTERCONNECT_ARCHITECTURE.md` §0.
**Status:** settled.

### Southbridge
**Class:** system role (MCU host adapter).
**Definition:** the RP2350 microcontroller that sits between any host and
the FPGA — owns SD boot, filesystem, table hydration, command streaming
over the SPI protocol contract (8 opcodes,
`docs/SOUTHBRIDGE_SPI_PROTOCOL.md`), and USB CDC telemetry.
**SPU convention:** the **homogeneity contract**: one protocol, one
console grammar, any large-enough board. SPI opcode set — 8 opcodes:
`0xA0` manifold, `0xAC` status, `0xAD` scale table, `0xAE` QR commit,
`0xAF` HEX projection, `0xB0` sentinel telemetry, `0xB1` instruction
write, `0xA5` RPLU config write (`docs/SOUTHBRIDGE_SPI_PROTOCOL.md` is
the count of record; some repo summaries elsewhere cite only the 5
opcodes exercised in early bring-up — that was shorthand, not the total)
— is frozen as v1: extensions add opcodes, never repurpose them; adding a
board means a pin map + constraints file, never a protocol fork. Smallest
fabrics (iCE40UP5K/GW1N-1 class) are exempt: they get bare pins (tier T0),
not a degraded southbridge.
**Literature:** name borrowed from PC chipset architecture (the I/O
companion chip); the SPU role is closer to a boot/host supervisor.
**Anchors:** `docs/SOUTHBRIDGE_SPI_PROTOCOL.md`, `hardware/rp2350/`,
`knowledge/INTERCONNECT_ARCHITECTURE.md` §2.
**Status:** settled (role, contract); protocol doc version header pending.

### Constellation
**Class:** deployment topology.
**Definition:** the macro tier of the Arlinghaus hierarchy — multiple
cluster nodes (each an SPU-13 governor with SPU-4 satellites) linked by
coherence beacons. Micro = edge node (SPU-4 alone), meso = cluster,
macro = constellation. Each tier checks its own invariant locally,
recovers locally (Henosis), and reports upward only unrecovered deviation
(dissonance).
**Literature:** hierarchy structure from Arlinghaus's hexagonal
hierarchies (Solstice); the hardware mapping is SPU-original.
**Anchors:** `knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7,
`knowledge/INTERCONNECT_ARCHITECTURE.md` §1.
**Status:** settled.

### Whisper protocol
**Class:** coherence signaling.
**Definition:** the SPU's coherence plane — a node continuously signals its
own laminar state; silence means incoherent or dead. Distinct from the
command plane (southbridge SPI protocol contract, 8 opcodes).
**SPU convention:** v0 (implemented): `spu_whisper_sane.v` emits `SANE\n`
over UART while `is_laminar` holds. v1 (specified 2026-07-08): fixed
18-byte ASCII line `W1 ii ff dd ss xx\n` at a 1 Hz default cadence —
node id, flags (snap_locked / henosis_since_last / relayed), saturating
dissonance, sequence, XOR checksum; fail-silent, 3-consecutive-miss
incoherence rule; governor may relay the worst satellite line one tier up
(≤2 lines/period/node). Full contract: `docs/WHISPER_V1_SPEC.md`.
**Literature:** none (SPU-coined); closest standard concept is a
heartbeat/liveness beacon, but whisper asserts *algebraic coherence*, not
mere liveness.
**Divergence / name collision:** `spu_whisper_tx.v` (artery peripheral) is
unrelated PWI telemetry using the "whisper" name — candidate rename
`spu_pwi_tx.v` before papers mention whisper.
**Anchors:** `hardware/tests/peripherals/spu_whisper_sane.v`,
`spu4_cluster_bridge.v`, `docs/WHISPER_V1_SPEC.md`,
`knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7.
**Status:** v0 settled; v1 RTL implemented + TB passes 2026-07-09
(emitter `spu_whisper_v1_emitter.v`, listener `spu_whisper_v1_listener.v`,
TB `hardware/tests/peripherals/spu_whisper_v1_tb.v` — 7 tests, all PASS).
Emitter wired into `spu4_core.v` (2026-07-09) with `whisper_tx` output port;
`dissonance` driven from the ALU gasket sum. Governor relay and zero-jitter
assertion are the two remaining §5 acceptance checklist gaps. Tang 25K probe
bitstream built, awaiting flash.

### Dissonance
**Class:** cluster telemetry quantity.
**Definition:** the 8-bit Davis-ratio deviation a satellite reports to its
governor — the residual ΣABCD state *after* local Henosis was attempted.
Zero dissonance ⇒ the satellite is laminar; the governor never sees raw
satellite state, only unrecovered deviation.
**Anchors:** `hardware/rtl/core/spu4/spu4_cluster_bridge.v` frame format,
`hardware/rtl/core/shared/spu_proprioception.v` (governor-side precedent).
**Status:** settled (2026-07-08). `dissonance[7:0] = min(|ΣABCD|, 255)` — the
saturating absolute value of the gasket residual — is now wired in
`spu4_core.v` as a combinational output from the ALU's A/B/C/D ports
(17-bit signed sum → absolute value → saturate at 255). 0x00 ⇔ laminar,
0xFF ⇔ saturated (|ΣABCD| ≥ 255). The `spu4_cluster_bridge` dissonance
input port awaits system-level wiring (instantiating the bridge in
`spu_system.v` and connecting the core's dissonance output) — a narrow
plumbing task, not an open design question.

## Build & product vocabulary

### Spin
**Class:** build/product vocabulary.
**Definition:** a named, reproducible bitstream configuration — a specific
subset of SPU modules synthesized for a specific board target. A **probe**
is a spin whose purpose is to produce one piece of silicon evidence
(typically a golden UART line) rather than end-user function.
**SPU convention:** Artix-7 spins are selected by argument to
`hardware/boards/artix7/build_a7.sh` (robotics, lucas, su3share,
rplu2pade, somprobe, …) and print uppercase in logs
(`RPLU2PADE_J11: PASS`); Tang 25K spins are one root-level script each
(`build_25k_*.sh`). Per-spin purpose, resource envelope, and silicon
status: `docs/SPIN_CATALOG.md`.
**Literature:** informal FPGA/ASIC industry usage, where a "silicon spin"
is a re-fabrication iteration.
**Divergence:** industry "spin" implies an *iteration in time*; SPU spins
are *parallel configurations*. Papers should say "build configuration
(spin)" on first use.
**Anchors:** `hardware/boards/artix7/build_a7.sh`, `build_25k_*.sh`,
`docs/SPIN_CATALOG.md`.
**Status:** settled (2026-07-08).

### IVM Laplacian (née Tensegrity Balancer — renamed 2026-07-09)
**Class:** settled term, concrete RTL primitive.
**Definition:** a 12-neighbor discrete Laplacian relaxation filter over the
IVM's 12-around-1 coordination shell — the natural diffusion/smoothing
operator on the cuboctahedral lattice. Sums neighbor contributions in
Q(√3), threshold-gates the residual per lane, and asserts equilibrium
when all 8 lanes drop below threshold. No strut/cable mechanics, no
prestress — this is the geometric consensus operator, not structural
tensegrity simulation. If genuine tensegrity (Fuller's
compression/tension members) is needed later, it would be a separate
application module built on top of the core primitives, not a
replacement for the Laplacian.
**Anchors:** `hardware/rtl/core/shared/spu_ivm_laplacian.v`,
`tools/simulate_synergetic_routing.py`.
**Status:** SETTLED — renamed 2026-07-09. The orphaned
`spu4_precession_tb.v` / `precession.hex` have no corresponding PRECESSION
opcode and are retained as exploratory artifacts, not active tests.
The structural-health-monitoring opportunity from the pre-rename audit
remains a valid future direction, tracked in
`spu_strategy/killer_app_wedge_strategy.md`.
**History:** formerly `spu_tensegrity_balancer.v`, flagged 2026-07-08 as
mislabeled. The Laplacian is geometrically correct and is what the IVM
lattice naturally produces — the rename acknowledges this rather than
pretending the module computes something it doesn't.

## House terms needing definitions (flagged, not yet formal)

### "Sovereign" (sovereign bus, Sovereign Geometry Library, sovereign domain)
**Class:** internal codebase vocabulary — **retired from paper-facing text**.
**Definition (internal):** the prefix spans three codebase meanings —
dependency independence (Sovereign Geometry Library: no external
libraries, no vendor IP, no FPU), bus mastership (SPU-4 as autonomous boot
master), and the deterministic timing domain (`CLOCK_ARCHITECTURE.md`).
**SPU convention:** papers and outreach text use the plain terms instead:
"self-contained" / "no external dependencies," "boot master," and
"deterministic domain." Code identifiers and internal docs keep the
existing names — no renaming churn.
**Status:** settled (2026-07-08, John's call: retire from papers; plain
terms in all paper-facing text).

### "Lithic" (module discipline; Lithic-L language)
**Class:** design philosophy (two expressions).
**Definition:** one philosophy with two expressions. In RTL, the *Lithic
discipline*: single-purpose modules, typically 50–150 lines; split
concerns rather than grow files. In software, *Lithic-L*: the .lith
program format's language spec. Papers present them together — the
language is the discipline applied to programs.
**Anchors:** `knowledge/LITHIC_L_LANGUAGE_SPEC.md`, CLAUDE.md conventions.
**Status:** settled (2026-07-08, John's call: share the name — one
philosophy, two expressions).
