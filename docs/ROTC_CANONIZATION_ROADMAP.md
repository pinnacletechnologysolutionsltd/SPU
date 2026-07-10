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

## Phase 2 — IROTC in the VM (next coding session's main course)

Order matters; each step gates the next:

1. **Register-plane decision** (the one real design choice left):
   φ-plane in the QR register file vs. a vector bank on the Lucas MAC
   sidecar. Components are Z[φ] pairs, NOT RationalSurd. Decide before
   writing any code.
2. **Implement** `LOAD2X`/`SCALE2`/`IROTC` + DOUBLED tag semantics in
   `spu_vm.py`. The 60-entry table must be GENERATED from the oracle
   (`--emit`), never hand-copied; verify against checksum at import or
   in a test.
3. **Trace oracle**: VM vs exact-Fraction over all 60 indices × both
   catalogs (sel[6]) on tagged inputs — style of
   `test_rotc_vm_rtl_trace.py`.
4. **Poison proofs**: `IROTC_ERR_UNTAGGED`, `IROTC_ERR_BADIDX` —
   destination survives bit-identically, fault flag raised (mirror
   `test_rotc_bad_angle.py`).
5. **Chain tests**: doubled load → mixed 10-step A₅ chains exact;
   a thirds ROTC mid-chain must clear the tag and fault the next IROTC.
6. **Assembler**: mnemonics in `software/tools/spu13_asm.py`.

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
