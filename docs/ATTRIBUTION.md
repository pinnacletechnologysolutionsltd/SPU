# Attribution & Credit Lineage

A standalone record of who contributed what. Split into two parts:
**Foundational Lineage** — the mathematical and conceptual ancestors of the SPU
project — and **SPU Original Engineering** — the specific contributions made
in this project.

*Last updated: 2026-05-22*

---

## Part 1: Foundational Lineage

These are the works and people on whose ideas the SPU project builds. None of
them are responsible for the SPU architecture, its bugs, or its claims.

### Synergetics & Tetrahedral Geometry

| Contributor | Contribution | Reference |
|---|---|---|
| **R. Buckminster Fuller** | Synergetics: tetrahedron as irreducible structural unit; IVM (isotropic vector matrix); vector equilibrium (cuboctahedron) as zero-energy ground state; whole-number tetrahedral volumes (synergetic accounting); jitterbug transformation; concentric hierarchy of polyhedra | *Synergetics* (1975), *Synergetics 2* (1979) |

### Quadray Coordinates

| Contributor | Contribution | Reference |
|---|---|---|
| **Kirby Urner** | Quadray coordinate system: 4-axis tetrahedral coordinates, zero-sum hyperplane, canonical form min(a,b,c,d)=0, expository documentation | grunch.net/synergetics/quadintro.html; kirbyurner.github.io/quadrays |
| **Tom Ace** | Quadray basis matrix (the 4×3 matrix expressing ABCD directions in Cartesian, used by every ABCD pipeline to this day); F,G,H circulant (basis-axis rotation specialization with integer-rational entries at tetrahedral angles) | minortriad.com/quadray.html (1997 C++ implementation) |

### Rational Trigonometry

| Contributor | Contribution | Reference |
|---|---|---|
| **Norman J. Wildberger** | Rational trigonometry: replacement of angle/distance with spread/quadrance; triple spread formula; proof that geometry requires no transcendentals; universal hyperbolic geometry; chromogeometry | *Divine Proportions* (2005); WildEgg YouTube channel |

### Spread-Quadray Rotors & ABCD-Native Computing

| Contributor | Contribution | Reference |
|---|---|---|
| **Andy Ross Thomson** | Spread-Quadray Rotors (SQR): 4D rotor algebra native to tetrahedral basis; synthesis of Fuller/Wildberger/Urner for computer graphics; ABCD-native rendering pipeline; ABCD-to-clip in one matrix multiply; rationality-driven dispatcher architecture; six-engine rotation primitive taxonomy | *Quadray-Rotors-v5.pdf* (May 2026); *Synergetics-Cookbook.pdf* (May 2026); *Prime_Projection_Conjecture_v5.1.pdf* (Feb 2026); A.R.T. Explorer (arossti.github.io/ARTexplorer) |
| **Leo Murillo** | K(u) cubic identity K³ = −K: the key algebraic result enabling closed-form Rodrigues exponential for tetrahedral rotation without transcendentals. Resolved an open question in earlier SQR versions | Zenodo 19689050 (2026) |
| **Strüppi Pohl** | D-up (Strüppi-Up) world-up convention: structural alignment of the world-up axis choice with the A₄ tetrahedral symmetry group; Capoeira-ginga tetrahedral pose framing; gravitational alignment of the tetrahedron as tripod | Personal communication / ABCD.Earth contributor note (2026) |
| **Evgeny Yanenko** | State-machine-harness framing of ROTC: exactness state carried by the data (CLEAN/PENDING/FAULT), rotations as guarded transitions, reduction as an explicit fallible operation — the reframing that turned the /3 exactness caveat into an ISA contract (formalized in `docs/ROTC_EXPONENT_STATE_MACHINE.md` and §6 of `docs/ROTC_KINEMATICS_PAPER.md`). Also author of "Evolving Categories" (2004, arXiv), a categorical framework for representing data and algorithms uniformly as state-machine transitions — the broader theoretical foundation for the harness approach | `Theory/EvolvingCategories.pdf` (Evgeny Yanenko, 2004); personal communication (2026) |

### Davis Framework

| Contributor | Contribution | Reference |
|---|---|---|
| **Bee Rosa Davis** | Davis Law C = τ/K (capacity = tolerance / curvature barrier); cache/bin/barrier state-classification architecture; Davis-Wilson map Γ_DW(A) = (Φ(A), r(A)); geometric approach to Navier-Stokes regularity, BSD conjecture, and Poincaré isomorphism within the Davis Field-Equation framework | *navier_stokes_regularity_v2.pdf* (Jan 2026); *Davis_BSD_Conjecture_Conditional.pdf* (Dec 2025); *Davis_Poincare_Isomorphism_Conditional.pdf* (Dec 2025); davis-wilson-map (github.com/nurdymuny/davis-wilson-map) |

---

## Part 2: SPU Original Engineering

These are the specific contributions made in the SPU project — the things built,
tested, and proven here that go beyond the foundational lineage.

### Field Extension Architecture

| Contribution | Description |
|---|---|
| **Q(√3) as hardware arithmetic basis** | Identification of Q(√3) as the minimal field extension of the rationals closed under IVM geometry; the multiplication formula `(ac+3bd) + (ad+bc)√3` as the single-cycle ALU operation; proof that this field never escapes to higher irrationals |
| **Q(√5) and Q(√15)** | Additional field extensions for rational sine computation (Pell orbit rotor) and rational projection/correction beyond the tetrahedral group |
| **Fixed-point surd encoding** | Q12 fixed-point representation for (P:int16, Q:int16) surd pairs; bit-exact zero test for Davis Gate without epsilon |

### RPLU (Rational Polynomial Look-Up)

| Contribution | Description |
|---|---|
| **RPLU architecture** | An indexed rational response surface implemented as FPGA BRAM lookup tables; flash-loaded chord records; deterministic state classification and correction lookup |
| **RPLU over Morse projections** | The specific combination of Morse-theoretic projection geometry with RPLU table indexing; discovered in conversation with Gemini |
| **RPLU flash boot chain** | SPI flash → BRAM loader → RPLU table verification; JEDEC ID check; 2051-record chord payload with rolling checksum; proven on Tang Primer 25K hardware (evidence: `docs/rplu_bringup_guard.md`) |

### Pell Octave

| Contribution | Description |
|---|---|
| **Pell octave representation** | Fractal decomposition of the Pell orbit rⁿ into (octave: int8, step: int3) pairs; eliminates 16-bit overflow beyond r⁸ while preserving exact P²−3Q²=1 invariant; infinite range in 11 bits |
| **Divorce of magnitude from mantissa** | Separation of rotor scale (octave counter) from stored surd mantissa (always from 8-entry vault); Davis Gate SNAP checks mantissa only |

### SPU Architecture

| Contribution | Description |
|---|---|
| **SPU-13 manifold engine** | 13-axis cuboctahedron/VE manifold; Q(√3) arithmetic ALU; division-free, float-free, branch-free hot path; Davis Gate with one-cycle Henosis correction |
| **SPU-4 sentinel** | Quadray satellite / edge-logic processor; precession-centric minimal SPU for sensor/peripheral aggregation |
| **RP2350 southbridge** | Architecture for USB/HID/sensors/timing offload via RP2350 as southbridge to SPU FPGA |
| **RP2040 visualization bridge** | Optional visualization/debug path via RP2040 |

### Hardware Verification

| Contribution | Description |
|---|---|
| **End-to-end probe ladder** | Seven-stage progressive hardware probe: flash ID → RPLU load → math path → SDRAM → lattice → full probe; each stage with exact UART telemetry proof lines |
| **SDRAM DQ[10] fault isolation** | Reproduced stuck-high pin with per-bit walk test; created masked build variant to continue bring-up on damaged board; proven board timing constants (INVERT_SDRAM_CLK=1, READ_CAPTURE_OFFSET=3) |
| **OSS CAD Suite flow** | Fully open-source synthesis flow: Yosys (synth_gowin) → nextpnr-himbaechel → gowin_pack → openFPGALoader; no vendor IDE required; 20 synthesis probe scripts for progressive bring-up |

### Robotics Direction

| Contribution | Description |
|---|---|
| **Robotics/proprioception as first application domain** | Narrowing the SPU roadmap to robotics control and telemetry as the first serious application; actuator state, encoder/IMU-like proprioception, contact/friction RPLU correction |
| **Simulation-first approach** | Software simulation suite before hardware loop closure; actuator model, encoder model, RPLU correction table, telemetry visualization in Python VM |

---

## Part 3: Convergent Lines

These are areas where SPU work and external work have independently converged
on similar ideas. Credit is shared; neither party copied the other.

| Idea | SPU | External | Relationship |
|---|---|---|---|
| Rational surd fields for tetrahedral geometry | Q(√3), Q(√5), Q(√15) — derived for SPU control path | Q(√2, √3) for convex hulls — Thomson Cookbook §11.6 (May 2026) | SPU surd work shared with Thomson early 2026; Cookbook future-work section independently proposes different field for rendering. Convergent but different field choices, different domains. |
| Cache/classification surface | RPLU: BRAM-based indexed rational lookup for hardware correction | Davis-Wilson map: Γ_DW(A) = (Φ(A), r(A)) for Yang-Mills/Navier-Stokes state classification | SPU inspired by Davis-Wilson pattern; RPLU is a hardware realization of the cache-map concept for a different domain (robotics control vs. gauge theory). |
| Davis Gate / laminar condition | ΣABCD = 0 as bit-exact zero test with one-cycle Henosis correction | Davis Law C = τ/K as field equation with semantic cache Φ(u) and bin-crossing contradictions | SPU Davis Gate is a hardware implementation of the laminar concept inspired by the Davis Framework; the mathematical treatment in Davis's papers is theoretical (axiomatic proofs); SPU's is empirical (hardware telemetry). |

---

## Part 4: What SPU Does NOT Claim

To avoid overreach, the SPU project explicitly does not claim:

- To have proven any Millennium Prize problems (Navier-Stokes regularity, BSD,
  Poincaré). The Davis papers in `Theory/` are external, conditional/axiomatic
  works by Bee Rosa Davis. SPU references them as theoretical motivation, not
  as proven results.
- To have originated synergetics, rational trigonometry, Quadray coordinates,
  or Spread-Quadray Rotors. These belong to Fuller, Wildberger, Urner/Ace, and
  Thomson/Murillo/Pohl respectively.
- To have "discovered" field extensions as a mathematical concept. Q(√3) is
  standard algebra. SPU's contribution is applying the *specific* field
  extensions Q(√3), Q(√5), Q(√15) as a fixed-point hardware arithmetic basis
  and proving they work in silicon.
- That the Davis-Wilson map or Davis Framework have been independently verified
  or peer-reviewed. They remain external, speculative works used as conceptual
  inspiration.

---

## Part 5: How to Credit This Project

If you are writing about, building on, or referencing the SPU project, the
recommended attribution statement is:

> This project builds on synergetics (Fuller), Quadray coordinates (Urner, Ace),
> rational trigonometry (Wildberger), Spread-Quadray Rotors (Thomson, with
> Murillo's K³=−K identity and Pohl's D-up convention), and the Davis Framework
> cache/bin architecture (Davis). The original engineering contribution here is
> the SPU/RPLU architecture: rational field extensions Q(√3)/Q(√5)/Q(√15) as a
> division-free, float-free FPGA arithmetic basis; RPLU as a hardware lookup
> and correction surface; Pell octave for unbounded rational rotor range; and
> the progressive probe ladder producing reproducible hardware telemetry on
> open-source toolchains.

---

*CC0 1.0 Universal — public domain*
