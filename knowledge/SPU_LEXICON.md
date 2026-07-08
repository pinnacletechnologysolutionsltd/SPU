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
**SPU convention:** SPU-4 registers hold **signed** 16-bit components A–D;
the canonical-form constraint is *not* enforced by hardware. Test fixtures
and the rotor path use signed values freely.
**Literature:** Kirby Urner (from Fuller's synergetics), basis matrix by Tom
Ace (1997). Urner's canonical form requires `min(a,b,c,d) = 0` with
non-negative coordinates.
**Divergence:** SPU (following Thomson's SQR) drops the non-negativity /
canonical-form constraint at the register level; rotor algebra operates on
the unnormalized 4-tuple.
**Anchors:** `hardware/rtl/core/spu4/spu4_euclidean_alu.v`,
`hardware/rtl/core/shared/spu_quadray_regfile.v`,
`knowledge/MATHEMATICAL_FOUNDATIONS.md` §6.
**Status:** OPEN: state the exact normalization contract — when (if ever) is
canonical form restored, and is the zero-sum hyperplane or the min=0 form
the working representative? Resolve against Thomson's *Quadray-Rotors-v5*
and record the answer here.

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
**Status:** settled (encoding); OPEN: confirm §-references into
Quadray-Rotors-v5 with A.R.T. before the papers cite them.

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
**Literature:** the zero-sum hyperplane constraint appears in Urner's
Quadray normalization; "Davis Ratio," "cubic leak," and "Henosis" are
SPU-coined (attribution: Bee Davis, per `docs/ATTRIBUTION.md`).
**Divergence:** SPU-coined names for an SPU-specific runtime invariant.
**Anchors:** `hardware/rtl/core/shared/davis_gate_dsp.v`.
**Status:** OPEN: write the invariant's precise algebraic statement (which
quantity is summed, over which representation, and why it is conserved by
every hot-path op) as a short lemma — currently folklore distributed across
comments.

## Timing

### Piranha Pulse / Fibonacci-gated dispatch
**Class:** timing architecture.
**Definition:** the 61.44 kHz system reference pulse; instructions dispatch
at Fibonacci intervals (8/13/21 cycles). Deliberate design constraint —
timing deviations are design flaws, not artifacts to buffer away.
**SPU convention:** `spu_sierpinski_clk.v` generates the pulse; phase
signals phi_8/phi_13/phi_21 gate the sequencer.
**Literature:** none (SPU-coined).
**Anchors:** `hardware/rtl/top/spu_sierpinski_clk.v`,
`knowledge/CLOCK_ARCHITECTURE.md`.
**Status:** settled (names); OPEN: one-paragraph rationale for *why*
Fibonacci intervals, written once, citable by all four papers.

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

## House terms needing definitions (flagged, not yet formal)

### "Sovereign" (sovereign bus, Sovereign Geometry Library)
**Status:** OPEN: the prefix is used across the codebase without a fixed
definition. Write the one-sentence meaning (autonomy from external
libraries? no-floating-point closure? bus mastership semantics?) or retire
the prefix from paper-facing text.

### "Lithic" (module discipline; Lithic-L language)
**Definition (working):** single-purpose modules, typically 50–150 lines;
split concerns rather than grow files. Lithic-L is the .lith program
format's language spec.
**Anchors:** `knowledge/LITHIC_L_LANGUAGE_SPEC.md`, CLAUDE.md conventions.
**Status:** OPEN: confirm whether "Lithic" (discipline) and "Lithic-L"
(language) should share the name in papers or be separated.
