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

## Phase 3 — IROTC in RTL

- Micro-program engine on the Lucas MAC sidecar (PSCALE/ADD/SUB chains +
  shared `>>>1`, no guards in the hot path). Worst case 8 PSCALE +
  16 ADD/SUB.
- **Sequencer decision**: worst-case ~27 steps fits the Fibonacci-21
  slot only at 2 ops/cycle; otherwise IROTC is a 34-slot instruction.
- TB + bit-exact VM equivalence, then Tang 25K probe, then Artix-7.

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
