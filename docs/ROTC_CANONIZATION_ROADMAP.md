# ROTC Canonization Roadmap & Session Handoff

Written 2026-07-10 (end of the icosahedral session). Purpose: everything a
future session needs to finish and canonize the rotation catalog without
re-deriving context. Read alongside `AGENTS.md` (current status),
`docs/IROTC_SPEC.md` (opcode spec), and
`docs/ICOSAHEDRAL_QUADRAY_CATALOG.md` (findings).

## Where things stand (as of commits `badfa95`, `5ced109`)

- **Suite: 142/142.** Catalog 0–35 verified (silicon 0–5 on Artix-7;
  6–35 testbench/trace only). ROTC_MAX_VERIFIED_ANGLE = 35, gate at 36.
- **Icosahedral A₅ derived and machine-checked** (21-check oracle,
  `software/tests/test_icosahedral_catalog.py`, checksum
  `aabef37c9c8b0317`). Headline results: entries in ½Z[φ] (NOT Z[φ]);
  no PMUL/PINV needed; doubling theorem discharges the /2 statically for
  pure A₅ chains; PCHIRAL reaches the conjugate catalog; 132 total
  entries reachable.
- **IROTC/LOAD2X/SCALE2 specified** (`docs/IROTC_SPEC.md` v0.1, opcodes
  0xD6–0xD8 provisional). DOUBLED added as prefix state in
  `docs/STATE_MACHINE_HARNESS.md` §3.5. No VM, no RTL yet.
- `badfa95` and `5ced109` may be **unpushed** — check `git status -sb`
  before advising git operations (history was rewritten 2026-07-07).

## Phase 1 — Canonize 0–35 (mostly bench work, John's hands)

1. **Artix-7 bench runs**: extended-angle probe covering 6–35 (current
   probes self-check 0–5 only). Includes the octahedral closure checks
   (24 self-inverse, 33↔35) on zero-sum vectors. On pass, promote the
   claim tables in AGENTS.md and paper §10 from "Simulation (probe
   queued)" to Silicon.
2. **Paper §11 rewrite**: the icosahedral bullet still says "derivation
   started" — replace with the verified results (½Z[φ], doubling
   theorem, conjugate catalog). The A₄→S₄→A₅ trajectory is the paper's
   capstone argument.
3. **arXiv decision**: ROTC paper is the most self-contained
   (release-wherever-ready strategy). Needs: §11 rewrite, TeX
   conversion, and the closed-form rank-1-mod-2 theorem (nice-to-have,
   §7 open item — why exactly 16/64 residue classes are safe for every
   icosahedral numerator).

## Phase 2 — IROTC in the VM ✅ COMPLETE 2026-07-10 (same-day session)

All six steps done; suite 145/145. Decisions and findings:

1. **Register-plane decision → QR register file overlay.** Z[φ] pair
   `(a, b)` lives in the same component slots as the `(P, Q)` surd
   packing. Forced by the spec's own tag algebra (thirds-ROTC clears,
   QADD linearity) — those rules are only enforceable on shared
   registers; also reuses the sidecar's existing qr_commit path.
2. **Implemented** (`spu_vm.py` 0xD6-0xD8; table generated via
   `--emit-vm` → `software/lib/irotc_catalog.py`, checksum-verified at
   first dispatch).
   **MAJOR FINDING: the v0.1 1-bit DOUBLED tag was unsound.** The
   doubling theorem does not compose across catalogs — mixed products
   `conj(M₁)·M₂` leave ½Z[φ] (denominator 4; oracle check 20, now 22
   checks total), so main→conj chains silently truncate (101/200 random
   repro). Repaired as a 4-state typestate (UNTAGGED/FRESH/MAIN/CONJ,
   2 bits/register in RTL) + third dispatch fault `IROTC_ERR_CATMIX`;
   SCALE2 re-conditions to FRESH; PCHIRAL swaps MAIN↔CONJ. Octahedral
   ROTC (24-35, not in A₅) demotes MAIN/CONJ→UNTAGGED (sandwich check).
   Spec bumped to v0.2; `STATE_MACHINE_HARNESS.md` §3.5 updated. This is
   the harness story's best exhibit yet: theorem-licensed states, and
   the machine refuses exactly where the theorem's hypothesis fails.
3. **Trace oracle** ✅ `test_irotc_vm_trace.py` (9 checks: 60×both
   catalogs ×3 vectors, junk-A rejection, A₄ alias interop, sel[6]
   don't-care on aliases).
4. **Poison proofs** ✅ `test_irotc_poison.py` (14 checks, all three
   faults + BADIDX>UNTAGGED precedence + SCALE2 recovery).
5. **Chain tests** ✅ `test_irotc_chains.py` (12 checks: 40×10-step
   pure-catalog chains exact, thirds mid-chain, octahedral demotion,
   QADD lattice).
6. **Assembler** ✅ both `spu13_asm.py` and the VM inline assembler,
   bit-identical encodings (inline LOAD2X accepts 5-arg and packed
   forms; inline QLDI remains packed-only — pre-existing divergence).

## Phase 3 — IROTC in RTL (engine done 2026-07-10; probes remaining)

- ✅ **Sequencer decision (John, 2026-07-10): term-serial, 13-slot.**
  The v0.1 micro-program dilemma (21 @ 2 ops/cycle vs 34) dissolved:
  each alphabet value is a single-cycle signed pair map, so one shared
  term unit does any rotation in a FIXED 13-cycle slot (φ₁₃ gate),
  uniform across all 60 indices × both catalogs. Key insight recorded
  in spec §6: the engine is signed exact Z[φ] — it cannot reuse the
  mod-L_p MAC datapath, only the sidecar's plumbing.
- ✅ `spu13_irotc_engine.v` + TB: 120 oracle-generated golden cases
  bit-exact (VM↔RTL closed transitively through the shared derivation
  oracle), 12-clock latency pinned per case, 10-step back-to-back
  chain, BADIDX/UNTAGGED/CATMIX fault matrix with poison holds.
  Generic yosys synth clean, 0 DSP. Tables generated via `--emit-rtl`.
- ✅ **Tang 25K probe — SILICON 2026-07-10 NZT** (`IROTC:P E=00`
  repeating; evidence §3.2k). Probe authored by DeepSeek, verified +
  repaired before bench (stale TB port name — the claimed TB pass was a
  stale binary; impossible TB UART timeout — CLK_FREQ now a parameter;
  wrong LED legend in the build script; one-shot verdict line —
  changed to the §3.2g repeating pattern, which is what made the bench
  capture work). Probe constants, hardcoded ROM (540/540 vs .mem),
  start-pulse fix, and fault FSM verified correct. Oracle check 23 pins
  the inline ROM against the derivation permanently. Silicon scope:
  idx 16 (period-3) + idx 36 (period-5, genuine φ-arithmetic) + all
  three dispatch faults; conjugate catalog not yet in silicon.
- ✅ **Core integration 2026-07-11** (decision: in-core, not the sidecar
  DeepSeek sketched — the sidecar pattern is stateless and IROTC chains
  need persistent registers; a "SIMD instruction" integrates inside the
  core next to the register file). ENABLE_IROTC generate in
  spu13_core.v: 0xD6-0xD8 in the dispatch FSM, engine on the core QR
  file, 13×2-bit tag file with the full transition algebra at every
  write site (default-clear for unknown writers). SPI dispatch = the
  existing 0xB1 fall-through. spu13_core_irotc_opcode_tb.v (25 checks),
  suite 148/148. TB lesson: wait for VE hydration (init-port priority)
  before issuing instructions.
- 🟨 IROTC SPI spin built 2026-07-11 (`build_25k_spu13_irotc_spi.sh` →
  `tang_primer_25k_spu13_irotc_spi.fs`, southbridge .cst/pins).
  **Lean config MATH=0 + IROTC=1**: the MATH=1 southbridge base no
  longer fits at HEAD (25.5k LUT4 post-synth vs 23k device; last
  successful placement 2026-06-29 was already 90%) — core growth since
  June 29 is a standing regression for `build_25k_spu13_southbridge.sh`,
  flagged, not yet addressed. `gen_qrf` now enables on ENABLE_IROTC
  alone (gen_qrf_only path, no TDM rotor; do NOT issue ROTC on MATH=0
  spins — it hangs the inst handshake by design of the stub tie-offs).
  **Hydration interlock added** (John's question caught it):
  instructions are held until VE hydration is not pending/in-flight
  (`qrf_hydrated = init_done || !boot_done`) — structural, no timeout;
  fixes a latent sequencer-vs-hydration race and the TB gotcha class.
  Proof: `spu13_spi_core_irotc_tb.v` — CRC'd 0xB1 writes + 0xAE
  readbacks through the real spu_spi_slave: LOAD2X, idx36 main,
  **idx36 conjugate**, CATMIX with no-commit proven over the link,
  SCALE2 recondition → legal switch. Suite 149/149. Bench firmware:
  `hardware/rp2350/rp2350_spu_irotc_test.c` (6-case table, same
  vectors). **Awaiting bench** — this run puts the conjugate catalog
  in silicon.
- ⬜ Artix-7 after Tang bench (claim discipline as always).

## Phase 4 — Harness formalization (parallel track, low urgency)

Decision from 2026-07-10 discussion: the harness generalizes, but
position it honestly — it is typestate analysis where the states are
licensed by algebraic theorems (DOUBLED = doubling theorem, CLEAN =
mod-3 condition), plus hardware fault semantics and the three-layer
oracle discipline (independent exact oracle / implementation
equivalence / poison proofs). Yanenko's "Evolving Categories" (2004,
`Theory/EvolvingCategories.pdf`) is the framing inspiration and is a
vision sketch by its own admission — cite it alongside typestate
(Strom & Yemini 1986), design-by-contract, and model checking.

Sequence: (a) extract a short method doc into `knowledge/` now-ish;
(b) let harness Phases 3–6 (Padé → batch inverter → SOM → BTU, per
`docs/STATE_MACHINE_HARNESS.md`) accumulate as case studies;
(c) standalone methods paper only after ≥4 subsystems. Transfer targets
worth naming in the doc: embedded protocol/driver state (the southbridge
SPI machine is an in-repo candidate), resource lifecycles, robotics
kinematic chains (strongest case — it IS the ROTC application), and
deterministic game-engine substrates (asset pipelines, rollback
netcode). Do not let this track displace the SOM/anomaly-detection
wedge.

## Small admin (can be knocked out any session)

- Delete or archive remote branch `feature/reset-unify-clean` (John:
  "old branch, not sure if we need it").
- gitignore `hardware/pcb/bench_adapter/kicad/.history/` (KiCad plugin
  litter); decide whether `bench_adapter.kicad_pcb` should be committed.
- `run_all_tests.py`: `su3_pass` counts toward total_pass but a failure
  doesn't increment total_fail (latent counting quirk, pre-existing).

## Watchpoints for the next session (hard-won this week)

1. **Verify DeepSeek's claims independently before they touch docs** —
   this week: false "pre-existing failures", impossible 3+9 period
   split, false pure-Z[φ] claim. The pattern is consistent: the code
   mostly works, the *claims about it* drift.
2. When RTL ports change, grep ALL instantiation sites including board
   tops (`hardware/boards/**`) — testbenches passing is not enough.
3. Keep derivations executable in-repo. Never delete the script after
   extracting findings.
4. Three-way bit-identical discipline for any new table: oracle
   (generated + checksummed) / VM / RTL.
5. The /2 (icosahedral) and /3 (thirds) look similar but are opposites:
   /2 is statically dischargeable (finite group), /3 is not
   (non-closed catalog). Don't let docs or code conflate them.

## Session handoff 2026-07-12 (read this first next session)

Tree: everything pushed through `73acd91`; only John's hand-routed
`bench_adapter.kicad_pcb` is untracked (deliberate). Suite: **153/153**.

**In flight at close:** the IROTC SPI bitstream is rebuilding from the
BSRAM-engine netlist as a DETACHED process (survives session end).
Check: `ls build/tang_primer_25k_spu13_irotc_spi.fs`; progress in
`build/spu13_irotc_spi_nextpnr.log` (expect BSRAM:1 in utilisation —
if BSRAM:0 it's a stale netlist, kill and rerun
`build_25k_spu13_irotc_spi.sh`). The old case-ROM netlist LIVELOCKED
routing (~58.9k congestion plateau, two seeds); the BSRAM engine
(73acd91) removes the mux forest. Ops note: pkill -f patterns that
appear in your own command line self-kill the shell (exit 144) — use
[b]racket patterns and separate kill from launch invocations.

**Next actions, in order:**
1. Bitstream lands → `tools/gen_paper_figures.py` (venv has matplotlib)
   → recompile `docs/theorem_licensed_typestate.tex` → bench handoff:
   RP2350 target `rp2350_spu_irotc_test` (polls boot_ready = 0xAC
   byte 3 mask 0x04), FPGA SRAM-load the .fs, six-case CDC output;
   case [2] = conjugate catalog silicon, case [3] = CATMIX no-commit
   over the link. Evidence entry on pass (§3.2k format).
2. GTP micro-round (order not yet sent): Q(φ) generalization of
   segments_intersect_interior (docstring lists the three confirmed
   gaps: φ-coords assert-crash, collinear overlap missed, T-junction
   boundary), + tensegrity doc rider (adopt "discrete exact
   admissibility" positioning + the fault-code→physical-diagnosis
   table from John's 2026-07-12 paste).
3. Artix-7: IROTC spin (engine now BSRAM — A7 has plenty), then the
   A7 evidence entry.
4. Standing regression: MATH=1 southbridge spin no longer fits at HEAD
   (AGENTS known-limitations) — needs a diet or a 2-device split
   decision (John).
5. Paper: figure lands → TeX freeze candidate; Fuller §-numbers
   (640.02, 724.30) still await John's primary-source check.

Working model: GTP performs, Claude orchestrates/verifies/owns reserved
RTL (spu13_core.v, spu_spi_slave.v). Verify every GTP/DeepSeek numeric
claim against the tree before commit — this week's hit rate on that
rule was 100% useful.

### Addendum 2026-07-12 (same day, mid-morning)

- IROTC SPI bitstream: netlist confirmed BSRAM engine (**BSRAM: 1/56**
  in nextpnr log — not the stale case-ROM). Router converging, overuse
  ~15.4k at iter 253k and falling (old netlist livelocked at ~58.9k).
  Detached build + 120s watcher loop both still alive; watcher prints
  sha256 + utilisation when the .fs lands. Nothing to do but wait.
- Cartesian bridge v0 checklist (spec §5): **closed** — all six items
  verified against `test_cartesian_bridge.py` (30 checks), boxes ticked.
- Bridge RTL ingest promoted: spec **§7** now defines the
  `spu_cartesian_quantizer` contract (S24.8 in, round-half-even,
  saturate, Q=0, registered 1-cycle). Input is fixed-point, NOT
  IEEE-754 — floats never exist on the fabric; host/southbridge owns
  any float→S24.8 step.
- Quantizer RTL **landed same morning**: GTP performed from the §7
  order, module passed the staged oracle-derived TB verbatim (incl. the
  two boundary traps: 32767.5 rounds out→sat, -32768.5 rounds back
  in→no sat). `hardware/rtl/core/shared/spu_cartesian_quantizer.v`.
  Suite back green at **154/154**. The TB remains the acceptance
  authority — never edit it to fit an implementation.
- GTP round queue: **both orders done** — quantizer (d8352a6) and the
  Q(φ) micro-round (9f58f66, verified claim-by-claim; GTP report was
  accurate throughout).
- Deferred cleanup (GTP suggestion, agreed, low priority): rename
  `guard_struts_disjoint_interior` → `guard_struts_no_contact` or
  similar — since 9f58f66 it enforces closed contact, not just interior
  disjointness, so the name undersells it. Touches the guard, its
  fault_detail, feasibility doc + STATE_MACHINE_HARNESS.md guard rows.
  Bundle with the next tensegrity round, not worth solo churn.

### Session close 2026-07-12 (read this first next session)

Tree: five local commits **NOT pushed** (d8352a6 quantizer, daeb961
tee fix, 9f58f66 tensegrity Q(φ), 4030b4a + this one docs). John's
`bench_adapter.kicad_pcb` still deliberately untracked. Suite:
**154/154**. Both GTP orders from the round queue performed, verified,
committed — GTP's reports were accurate throughout this session.

**Bench run: PASS, 2026-07-12 late** — 6/6, including case [3]
(conjugate-catalog, lane 3) and case [4] (CATMIX no-commit, holds at
lane 3). First conjugate-icosahedron silicon. Full result + evidence:
`docs/hardware_evidence.md` §3.2k.1; AGENTS.md IROTC entry updated.

- Bitstream: `build/tang_primer_25k_spu13_irotc_spi.fs`,
  sha256 ca54c1dcdd1b358f786dab9a1094192c94402e86800bcd5cb6301ca0844c072a,
  BSRAM 1/56, LUT4 49%, worst Fmax 47.2 MHz @ 12 MHz constraint.
- **SRAM-load, not flash**: `openFPGALoader -b tangprimer25k <fs>`
  (no -f; keeps RPLU2 boot tables at flash 0x110000 intact).
- Wiring, **corrected 2026-07-12 late**: this section previously said
  GP16–19 ("NOT GP0–4") — that was wrong. The bench board can't reach
  GP16–19, and John's RP2350 Pico 2 exposes only GP0–4. The actual
  built artifact (`build/rp2350_irotc_check/rp2350_spu_irotc_test.uf2`)
  had always been compiled with `-DSPU_RP2350_ZERO_HEADER_SPI=ON`
  (CMakeLists.txt:25-27,41-47), i.e. GP0–3 all along — confirmed via
  `build.ninja` DEFINES and reproduced with a clean rebuild at
  `build/rp2350_irotc_gp0_3/rp2350_spu_irotc_test.uf2`. Correct wiring:
  Tang 25K PMOD **J4** — CS#=G10, SCK=D10, MOSI=B10, MISO=C10 — to
  RP2350 spi0 GP0–3 (MISO=GP0←C10, CS=GP1→G10, SCK=GP2→D10,
  MOSI=GP3→B10), common ground. This is what was on the bench for the
  passing run above.
- **No SD card needed**: boot_done is tied 1'b1 in this spin
  (spu13_tang25k_fpga_top.v:492) — hydration is the internal 13-cycle
  VE walk; boot_ready (0xAC byte 3 mask 0x04) comes up immediately.

**Queue (unchanged order, bench item now done):** A7 IROTC spin (needs
a new A7 board target; engine is BSRAM now, A7 has plenty) → MATH=1
southbridge fit decision (John) → Fuller §640.02/§724.30 primary-source
check (John) → INA226 sensor demo (digital path 100% done incl. quantizer
RTL d8352a6; blocked on John's PCB layout/parts/fab — see memory) →
deferred guard rename (bundle with next tensegrity round).

Paper: figure + TeX regenerated from live logs this session (tee fix
daeb961 was blocking the generator end-to-end); TeX freeze candidate
once bench evidence lands.
