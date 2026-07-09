# Synergetics Beyond Geometry — What's Real, What's Named-Only

Written 2026-07-08. John's question: the project draws its coordinate
system from Fuller's synergetics (IVM, Quadray, vector equilibrium) but
has it actually engaged synergetics' *other* principles — synergy as
emergent whole-system behavior, tensegrity's tension/compression
networks, precession, the VE as a physical (not just coordinate)
equilibrium? Audit answer below, organized by principle rather than by
module, since the same finding (real vs. name-only) recurs across
several unrelated files. Claim discipline per
`docs/SPU13_IDENTITY_AND_BOUNDARIES.md`: state proven work as proven,
dormant work as dormant, and never let the two blur.

## The map, by Fuller principle

| Synergetics principle | Fuller's meaning | SPU status |
|---|---|---|
| **Jitterbug transformation** | The VE (cuboctahedron) continuously deforms through the icosahedron to the octahedron and back — a real *dynamic*, structure-transforming process, not a static shape | **Real and tested.** `software/common/include/spu_physics.h`: exact Pell-orbit phase stepping, 8-step closure verified, reversible, icosahedron crossover at phase 2. Hardware: `OP_JITTER` in `spu_alu_gowin.v` — a genuine 1-cycle wire-permutation opcode. Also a `.sas` demo program, a Lithic-L language keyword (`jitterbug()`), and `spu_physics_test.cpp` (8+ checks). This is the strongest, most mature non-geometric synergetics content in the codebase. |
| **Vector Equilibrium as physical zero-point** | Fuller: the VE is the shape where push (compression) and pull (tension) are in perfect balance — a *physical* equilibrium claim, not just an origin convention | **Real, but unnamed as such.** The Davis Gate's ΣABCD = 0 test *is* an equilibrium condition, and the sum-invariance lemma (`knowledge/SPU_LEXICON.md`) proves it's conserved under every hot-path op — genuinely synergetic in spirit. It has just never been described as "the VE-as-equilibrium principle in silicon"; it reads as a parity check. Worth stating explicitly once, in a paper or here. |
| **Synergy** (whole-system behavior not predictable from parts) | Local interactions producing global, non-additive behavior | **Partially present, unnamed.** `spu_ivm_laplacian.v`'s algorithm — a 12-neighbor Laplacian relaxation converging to a global equilibrium from purely local rules — is a legitimate synergy primitive in the technical sense. It has never been framed or tested as "local rule → emergent global state"; it's just a diffusion filter today. Renamed from `spu_tensegrity_balancer.v` 2026-07-09. |
| **Tensegrity** (discontinuous compression held in continuous tension) | Real structural mechanics: separate strut (compression) and cable (tension) members in force balance | **Name only — now fixed.** No strut/cable distinction anywhere in RTL. Renamed to `spu_ivm_laplacian.v` 2026-07-09 (see `knowledge/SPU_LEXICON.md`, "IVM Laplacian" entry). |
| **Precession** | A force applied to a moving/rotating system produces an effect orthogonal to it — Fuller's metaphor for how local action yields systemic, not local, consequence | **Name only, orphaned.** `spu4_precession_tb.v` references `precession.hex` and a "Whisper broadcast" pass condition with no corresponding opcode in `isa_reference.md` or the VM. |

## The pattern underneath the gaps

`observer_stack_philosophy.md` already frames the manifold's computational
health in fluid vocabulary — `laminar_index`, `turbulence_alert`,
"structural stress analysis." `DavisGasket`'s τ (tension) / K (stiffness)
are literally Hookean. The archived `spu_active_inference.v` computes
`prediction_error` against a `prior_state` at `prior_precision`
(Friston's Free Energy Principle — precision-weighted prediction error;
`prior_precision` is the same shape as Davis's K, inverse tolerance and
inverse variance being the same idea from two literatures).
`spu_soul_metabolism.v` widens `adaptive_tau_q` — same τ symbol as
`DavisGasket.tau` — under sustained fault rate, a homeostatic-adaptation
analog. None of this was designed as one system; it accreted because
tension, precision, dissonance, and equilibrium are all names for the
same relationship: **an exact scalar measuring distance from
equilibrium/prior, checked against an exact tolerance for how far it may
go.** That primitive (Davis Ratio, C = τ/K) is real and silicon-proven.
Tensegrity, precession, and synergy-as-emergence are the *un-built*
expressions of it; Jitterbug and the Davis Gate itself are the *built*
ones. `knowledge/HARDWARE_MANIFEST_SPU13.md` §5 even shows the original
intent to unify two of these threads on real hardware — "OLED (Breath):
... Jitterbug/Metabolism charts" — a display meant to show Jitterbug
phase and Soul Metabolism state together. That pairing was envisioned
and never finished; Jitterbug got built, Soul Metabolism didn't.

## What this is not

- **Not a claim of consciousness, a literal "soul," or biological life.**
  "Soul Metabolism" and "Active Inference" are evocative names for
  control-theoretic mechanisms — same discipline as "Henosis" for
  soft-reset. State the mechanism plainly in paper-facing text; keep the
  evocative name as internal color.
- **Not a claim on Bee Davis's broader mathematical program** (Navier-
  Stokes regularity, BSD conjecture, Poincaré isomorphism) — the Davis
  Gate is *inspired by*, not a verification of, that work, exactly as
  `MATHEMATICAL_FOUNDATIONS.md` §5 already states.
- **Not a replacement for CFD/FEA tooling.** The claim is narrower:
  exact, reproducible, invariant-checked computation of a bounded set of
  relationships (equilibrium, tension/tolerance, predictive error), not
  general continuum mechanics.

## Relationship to the commercial wedge

`spu_strategy/killer_app_wedge_strategy.md` (private) identifies
industrial anomaly detection as the near-term entry point. Precisely
stated: anomaly detection is the wedge *into* this capability, not a
separate product. A vibration classifier that also computes genuine
structural tension/compression state — using the same Davis-Ratio-shaped
primitive that watches the SPU's own manifold — is one system wearing
two faces, external and internal. Selling the external face funds
building the internal one.

## Next steps (research-scoped, not build-now)

1. Name the Davis-Gate-as-VE-equilibrium connection explicitly, once, in
   a paper or `MATHEMATICAL_FOUNDATIONS.md` — cheapest fix, real content,
   zero new code.
2. Reframe (and give a real testbench to) the IVM Laplacian's
   actual algorithm as a synergy/emergence primitive — it is already
   renamed to `spu_ivm_laplacian.v` (2026-07-09) reflecting what it
   actually computes (12-neighbor Laplacian relaxation). If real
   tension/compression mechanics is wanted instead, design a new
   module against a written contract — the Laplacian is geometrically
   correct and should not be displaced for a different feature.
3. Retire or rewrite `spu4_precession_tb.v` — it currently proves
   nothing real.
4. Recover or rewrite `soul_map.vh`; decide whether
   `spu_active_inference.v` / `spu_soul_metabolism.v` are restored as
   written or redesigned — contract before RTL, per house convention.
   This is the piece that would finally realize the
   Jitterbug/Metabolism display pairing `HARDWARE_MANIFEST_SPU13.md`
   already imagined.
5. Give `spu_proprioception.v` a testbench before any status upgrade
   from "RTL exists" to "verified."

*CC0 1.0 Universal, like the rest of `knowledge/`.*
