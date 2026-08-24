# Session Handover — 2026-08-24

## 0. Scope note

Two threads today, both driven by the same fact: **SPU-4 hardware
(encoder, INA226 ×2) is genuinely blocked, ~1-2 days out** — nothing on
the primary programme moved today, and nothing here should be read as
having changed [[spu4-edge-node-focus]]'s status as the sole programme
once parts land. Thread 1 (photonics) picked up where the prior session
left off and **closed out completely**. Thread 2 (GPU/rasterizer) was
explicitly un-parked by John mid-session and is now mid-flight, in good
shape, with a clear next step scoped but not started.

8 commits today, `dcf223b..fe394b6`. All pushed to `origin/master`.

## 1. Photonics — CLOSED AT CURRENT SCOPE (John's explicit words)

Picked up from the E18–E21 campaign's 2026-08-24 closure (prior
session) and worked through its full agreed priority list to zero
remaining items:

- **Reliability model** (`09d17b2`): built a corrected whole-chain
  estimator folding E18's `R_i→R_{i+1}` dependence into the naive
  product-of-marginals model. Cut the point-estimate gap 71% but
  overshot into non-conservative territory at N=300,000 — **rejected**
  by its own pre-registered gate. `predicted_p_chain` (naive,
  conservative) remains adopted. Preserved as a completed result, not
  discarded.
- **Compilation contract** (`bf1ed7d`, `e8c9ab6`):
  `docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` — consolidates
  everything into one interface spec for what a photonic backend would
  need.
- **Architecture spec** (`3524a9e`): `docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md`
  — hypothetical-but-complete system architecture, four-tier evidence
  labeling throughout. Found and fixed a real gap along the way: REGEN
  (opcode `0x09`) is genuine RTL with a frozen ISA contract, not a
  photonics-branch convention — `knowledge/isa_reference.md` was
  missing the entry entirely.
- **Pair-0 calibration Phase 0** (`e18af6d`): a cheap sensitivity check
  (not a new calibration) found the pair-0 hypothesis for the
  overshoot is quantitatively viable (`p_hat_0∈[0.7173,0.7312]`) but
  not demonstrated. A mid-course bug (too-coarse sweep grid giving a
  false negative) was caught and fixed before reporting. **Phase 1
  (real calibration) explicitly not authorized.**
- **Placement implications**: scoped and closed with nothing to
  authorize — the "no change needed" conclusion was already
  independently reached three times; the item's own revisit
  precondition (new decided physical parameters) was never met.
- **Higher-`sigma_det` idea**: scoped and rejected outright — `sigma_det`
  is a single chain-wide simulator parameter, not per-event-tunable, so
  data gathered at a different noise level can't validly feed the
  existing estimator. A legitimate "fails at scoping" result.

**Read `docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md` first if this resumes**,
then [[photonics-research-branch]] memory for the full history. Nothing
is queued. Reopen only on a new architectural constraint, new physical
parameter, or independently motivated question — not by default.

## 2. GPU/rasterizer — reopened, real bugs fixed, verification triangle established

**Un-parked by John himself** (not a Claude proposal) — was explicitly
PARKED BY NAME in the 2026-08-16 SPU-4 focus decision, for pure
scope/focus reasons, no technical objection. First request got
mistakenly investigated in an unrelated Claude Code project
(`~/Projects/desktop/gzdoom`, John's separate Pinnacle graphics
company) before he corrected the target — worth remembering "GPU" is
ambiguous between the two without qualification.

**Audit found the triangle rasterizer was completely non-functional**,
despite `docs/SPIN_CATALOG.md` claiming the `VECTOR-GPU` spin's
rasterizer was "(TB-verified)" — confirmed by directly running the RTL,
not just reading it. Three real, independent bugs, all fixed same day
(`50a19c4`):

1. `spu_edge_stepper.v`: the inside/outside edge test was a hardcoded
   stub (`inside_out = 1'b1`, always true).
2. `spu_dual_raster.v`: a separate port-wiring bug — positional
   connections passed packed 64-bit concatenations where
   `spu_raster_unit` expects nine individual scalar ports, corrupting
   every coefficient.
3. `spu_raster_tb.v`: vacuous — its own comment claimed to check an
   outside-the-triangle case that was never actually implemented.

Root cause: `knowledge/RATIONAL_SHADER.md` (the original design doc)
already carried its own stale-banner from 2026-07-16 — its named
modules were deleted in a cleanup commit, and the audit that found this
(`docs/DOCS_RTL_CLEANUP_SCOPE_2026-07-16.md`) explicitly flagged that
the real `hardware/rtl/gpu/` files were never re-verified against it —
that reconciliation sat open for over a month until today.

**Built a genuine three-way verification triangle, all sharing one
oracle** (John: "start with the oracle" over a bigger oracle→Vulkan→RTL→
silicon contract, matching this session's own established discipline):

- `software/lib/gpu_raster_oracle.py` — independent, bit-exact,
  direct-evaluation Python oracle (not incremental like the RTL, so it
  can't share an accumulation bug with what it checks).
- `software/tests/test_gpu_raster_oracle_rtl_parity.py` (`8293451`) —
  exhaustive exact-pixel-set parity, full 640×480 screen, 3 triangles.
  Replaces the old 2-point vacuous check. Wired into `run_all_tests.py`.
- `software/gpu_vulkan/` (`fe394b6`) — a minimal GLSL compute shader +
  one-shot Vulkan C++ host program (no validation layers, staging
  buffer, or swapchain — a verification utility, not a renderer),
  dispatched on this machine's real discrete AMD GPU (Radeon RX 550,
  RADV POLARIS12). Exact parity against the oracle on the first run.

`run_all_tests.py`: **214 → 216** over the course of the day (both new
parity tests are real regression gates now, not orphaned checks).

**Scoped but not started: depth buffer + texture mapping.**
`spu_texture_dma.v` turned out to be a red herring — a generic SDRAM-
bridge exerciser, not texture-mapping infrastructure; real texture
mapping starts from zero. No depth-buffer RTL exists at all, and
`spu_gpu_top.v`'s own header states "No framebuffer: pixels stream out
synchronously" — a real stored depth buffer would be an architectural
departure, not an incremental add. Both features actually share one
prerequisite (per-pixel attribute interpolation, using the edge-function
values `spu_edge_stepper.v` already computes but doesn't expose), and
that prerequisite needs a division — forbidden in RTL by AGENTS.md's
hard constraints. Checked whether the RPLU/Padé modules sharing the
`hardware/rtl/gpu/` directory could serve as ready-made division-
avoidance machinery — **they can't**; unrelated finite-field domain
(A31/M31), not generic fixed-point reciprocals. A reciprocal LUT would
need to be built fresh.

**Recommended next step, not yet authorized:** depth-v1 — extend
`spu_dual_raster.v`'s hardcoded "unit0 always wins" to a real depth
comparison between two *flat* (non-interpolated) per-triangle depth
values. No division, no interpolation, buildable immediately, a named
limitation (won't handle slanted/intersecting triangles) rather than a
hidden one. The bigger, shared "attribute interpolation + reciprocal
LUT" piece that would unlock real depth and any texture mapping is
explicitly scoped as its own separately-authorized follow-on, not
started.

**Read [[spu13-gpu-rasterizer-audit-2026-08-24]] memory first if this
resumes.**

## 3. SPU-4 — untouched today, parts imminent

Nothing moved on the primary programme itself today. **Parts expected
~2026-08-25/26** ("not far away, maybe a day or two" — [[session-2026-08-17-hardware-order-timing]]).
Prep work (RTL/doc accuracy pass) was already done 2026-08-20; the
encoder mechanical-fit question is still open from that update. Check
whether parts have actually landed before assuming this ETA held.

## 4. Business/admin

John doing company admin himself for now. Flagged: **website help likely
needed soon** ("stay tuned") — no specifics yet, watch for a concrete ask
next session rather than assuming scope.

## 5. What's actually queued for next session

Nothing forced. In priority-adjacent order, none of these are defaults:

1. **SPU-4 bring-up**, once parts are confirmed landed — the real
   primary programme, resumes as-is.
2. **GPU depth-v1**, if John wants to continue that thread — scoped,
   cheap, ready to build (§2 above).
3. **Website/admin help**, if a concrete ask lands.
4. Photonics, GPU attribute-interpolation, or anything else — only on a
   new reason, not because a thread is sitting open.

## References

- Commits: `dcf223b..fe394b6` (8 commits, this session).
- [[photonics-research-branch]], [[spu13-gpu-rasterizer-audit-2026-08-24]],
  [[hypothesis-vs-cause-wording-discipline]],
  [[controlled-mechanism-experiment-template]] (memory).
- `docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md`,
  `docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` (photonics entry points).
- `knowledge/isa_reference.md` (REGEN `0x09` gap fixed this session).
