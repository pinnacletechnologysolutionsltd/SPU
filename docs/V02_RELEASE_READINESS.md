# SPU v0.2 release readiness index

**Status (2026-11-10, §11): TECHNICALLY READY as a scoped experimental release at `a2cfee73`; NOT PUBLICATION-READY. Publication: HOLD.** Prepared 2026-11-06 under SPU-V02-READINESS-INDEX-0 (documentation only);
updated 2026-11-07 for the GEN1-STA-1 closure, 2026-11-08 for the GEN1-RESET-EDGE-1 closure and the removable-media
backups of both Gen-1 evidence packages, and 2026-11-09 for the portable Gen-1 integration regression, branch relationships
and release-packaging constraints (§1, §3, §9, §10).

This is a navigation aid. It does not replace or reinterpret the [hardware evidence ledger](hardware_evidence.md),
the [capability matrix](CAPABILITY_MATRIX.md) or the original campaign reports, and it authorizes no experiment.
Each row uses the disposition of its cited source. Where sources disagree, the disagreement is listed in §8, not resolved.

## 1. Source baseline

| Item | Value |
|---|---|
| Revision inspected | Current: `599dbd0a33980fa156eed998ea3169f9ee218cca` on local `dev/next` (portable Gen-1 integration regression), the source revision for this 2026-11-09 update. Historical baselines, kept: first prepared against `6e9cbb0`; 2026-11-06/07 `21ea715c772b5d18bbfa4be93f9e7c8fafe267e6`; 2026-11-08 `d35e166d9d3b621006af48a45a9feb61423189b2` |
| Public state | **Not published.** As of 2026-11-09T04:14Z. Remote refs were read with `git ls-remote public` (no fetch); they equal the local remote-tracking refs. Counts are `git rev-list --left-right --count <ref>...dev/next` at `599dbd0a`; the commit containing this update adds one more to each "ahead" figure. <br>• `main` at `9fe2ceeb6f1113b7323a541d80316784d6cc526f`: an ancestor of local `dev/next`; `0 22` (local 22 ahead, 0 behind). It is also an ancestor of public `dev/next` (`0 8`). <br>• `dev/next` at `e7d37aa6714b42aa79b07df1a9c625143dd112b4`: an ancestor of local `dev/next`; `0 14`. History of this figure: `0 9` at `21ea715`, `0 11` at `d35e166`. <br>• `master` at `4e0d5b908e5bb1e0e86ba979b87affb83bd2a372`: the remote `HEAD` (GitHub default branch); separate history with no merge base (`883 82`). <br>Nothing in this index is on the public remote until a separately authorized push. A fast-forward of public `main` to a reviewed local revision is **proposed only** (§10) and needs separate approval. |
| Gen-1 CPU package | [`hardware/boards/artix7/wukong_v3/cpu_v02/`](../hardware/boards/artix7/wukong_v3/cpu_v02/README.md), frozen; 36 + 9 entries in `PACKAGE_SHA256.txt` / `portable/PORTABLE_SHA256.txt` |
| Build configuration | Vivado 2026.1 SW Build 6511674; part `xc7a100tfgg676-1` (speed −1); top `cpu_board_2r_top`; clocks `sys_clk` 20 ns, generated `cpu_clk` 40 ns |
| Golden image | `.bit` `442a229e…`, configuration payload `.bin` `cc259988…` ([SOURCE_MANIFEST](../hardware/boards/artix7/wukong_v3/cpu_v02/SOURCE_MANIFEST.md)) |
| Board procedure | Wukong V3 (XC7A100T), SRAM load with `openFPGALoader -c dirtyJtag --freq 1000000` (no flash options), UART 115200 8N1 over the onboard CH340 |

## 2. Gen-1 CPU: physical board observations

Every row is a **single-unit, single-session** observation of the fixed-program image; none is CPU qualification.
Common limits in every entry: one 14-instruction program family (SLI, SLD, SMUL, SRD), UART TX only, no timing margin,
rail, clock or temperature measurement. Read each entry's "Adjacent evidence dimensions not established" list.

| Ledger | Observation (source wording) | Disposition | Boundary (from the entry) |
|---|---|---|---|
| [§3.40](hardware_evidence.md#340--cpu-board-4c-r1-first-fixed-program-surd-cpu-run-over-uart-2026-10-30) | One volatile load ran the fixed program; expected record `(13,4,9)` | SILICON OBSERVATION PASS (single run, fixed program) | Not full ISA qualification; KEY0 reset not run; timing internal only |
| [§3.41](hardware_evidence.md#341--cpu-rom-2b-one-word-rom-variant-operand-variation-over-uart-run-2026-10-30-entry-prepared-2026-10-31) | One-word ROM variant; predicted `(16,8,9)` | SILICON OBSERVATION PASS (single run, one authorised ROM-word change) | One program, one run |
| [§3.42](hardware_evidence.md#342--cpu-board-4c-step-b-single-key0-restart-of-the-resident-one-word-image-2026-10-31) | One KEY0 restart of the resident image | SILICON OBSERVATION PASS (single press, scoped restart functionality) | Does **not** establish asynchronous reset safety; press time not captured |
| [§3.43](hardware_evidence.md#343--cpu-rom-2c-variant-b-denominator-25-operand-variation-over-uart-2026-10-31) | Variant B; predicted `(7,4,25)` | SILICON OBSERVATION PASS (single run, one authorised three-word ROM change) | One program, one run |
| [§3.47](hardware_evidence.md#347--gen1-repeat-1-three-independent-reloads-of-the-golden-fixed-program-surd-cpu-image-2026-11-05-utc) | Three independent reloads of the golden image | SILICON OBSERVATION PASS (3/3, one session) | One session, one unit |
| [§3.48](hardware_evidence.md#348--gen1-key0-repeat-1-five-key0-restarts-of-the-golden-surd-cpu-image-after-one-load-2026-11-05-utc) | Five owner-reported KEY0 presses after one load | SILICON OBSERVATION PASS (one load, five owner-reported KEY0 presses, one session) | Press edges, bounce and press-during-execution not observed; not a failure rate |
| [§3.49](hardware_evidence.md#349--gen1-variant-a-operand-variation-213-of-the-fixed-program-surd-cpu-over-uart-2026-11-06-utc) | Variant A; predicted `(7,4,9)` | SILICON OBSERVATION PASS (single run, one authorised two-word ROM change) | One program, one run |
| [§3.50](hardware_evidence.md#350--gen1-power-cycle-1-cold-power-cycle-observed-device-self-configured-from-flash-at-power-on-2026-11-06-utc) | Cold power cycle; the board self-configured from flash at power-on | **HOLD** (by design, at the post-power-on gate) | Establishes **no** Gen-1 result after a power cycle; flash content not identified |
| [§3.51](hardware_evidence.md#351--gen1-power-cycle-1-run-03-golden-gen-1-load-after-a-cold-power-cycle-2026-11-06-utc) | Golden load after one cold power cycle | SILICON OBSERVATION PASS (single run) | Gen-1 flash boot, flash identity, power-on reset timing not established |
| [§3.52](hardware_evidence.md#352--gen1-reset-edge-1-timed-key0-reset-recovery-of-the-golden-gen-1-image-2026-11-08-utc) | GEN1-RESET-EDGE-1: timed KEY0 pulses from an RP2350 open-drain generator (`gen1_reset_pulse_od`) into the golden image after one load; 15/15 trials gave the expected record count (C0 single pulse 5/5, T second pulse 5/5, C2 second pulse after HALT 5/5) | SILICON OBSERVATION PASS — scoped physical reset recovery, 15/15 trials across three cases, one Wukong unit | **Measured:** KEY0 timing, including the second pulse in T 1.75–2.00 µs (±0.25 µs) after release. **Inferred, not observed:** CPU execution at that edge (simulation window plus nominal clock). Not established: per-phase coverage, metastability, reset during UART transmission, general reset correctness |

The experimental programmable H0 CPU ([§3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc))
is a separate image and is not the Gen-1 baseline.

## 3. Gen-1 CPU: simulation, software and reproduction (not board evidence)

| Item | Status | Source |
|---|---|---|
| RTL simulation | Capability matrix: "Yes" for the integrated Surd CPU; expected records derived from RTL simulation (`build/cpu-rom-2a/out/sim/vectors.log`, outside Git) | [matrix](CAPABILITY_MATRIX.md), §3.40–3.43 |
| Software arithmetic | "Arithmetic accepted for its tested software scope" | [matrix](CAPABILITY_MATRIX.md) |
| Configuration-payload reproduction | CPU-REPRO-1B: PASS-BIT-EXACT (single reproduction) | [REPRO_1B_RESULT](../hardware/boards/artix7/wukong_v3/cpu_v02/portable/REPRO_1B_RESULT.md) |
| Second-host reproduction | PASS-BIT-EXACT for the payload, 0 report differences against the golden build (single run) | [desktop record](CPU_REPRO_DESKTOP_2026-11-06.md) |
| Directed integration simulation | GEN1-ISA-COVERAGE-2: **CLOSED — scoped PASS** (attempt 2; attempt 1 FAILED on harness defects). Seven directed cases (G golden, N1 negative coefficient, N2 normalization-to-fit, O overflow refusal, I invalid denominator, M1 reserved-bit rejection, M2 unsupported SADD rejection) on the unchanged `cpu_board_2r_top` RTL, judged against exact UART frames, with negative controls. Evidence in `build/gen1-isa-coverage-2-attempt-02/` (outside Git) | Owner acceptance; harness untracked in `spu_strategy/` |
| Architectural contract | [`GEN1_ARCHITECTURAL_CONTRACT.md`](GEN1_ARCHITECTURAL_CONTRACT.md) (`5948d8d5`, owner document-consistency acceptance): the frozen machine's four accepted encodings, arithmetic, reset, bitstream-only program loading, exact UART frames, exclusions, and claims tagged implemented / RTL-simulated / silicon / unverified. Describes the implementation; not a new ISA | Contract |
| C++ simulator profile | SPU-GEN1-SIM-IMPL-0 (`14ab48a6`): `spu_vm --profile gen1-surd` ([usage](software_guide.md)). Standalone conformance suite PASS: 7/7 fixture frames, the recorded silicon success frames (§3.40, §3.41, §3.43, §3.49), an independent expected-state model, legacy behaviour unchanged. A clean-tree build of `14ab48a6` reproduced the same frames. A directed **fault-after-readback** case (word 10 rejected after two SRDs), with the frozen RTL as reference, confirms that a fault frame keeps already-read slices (contract §9); the seven-case oracle zeroes them, and none of its cases reaches this path. **Software conformance only**, not RTL or silicon evidence | `build/gen1-sim-impl-0/`, `build/gen1-fault-after-srd/` (outside Git) |
| Portable integration regression | GEN1-INTEGRATION-PORTABILITY-1: the same suite relocated with repository-relative paths, committed as `599dbd0a`. Bench, UART parser and expected-record fixture (`3268eed2…`) are byte-identical to the frozen attempt-2 inputs. Migrated-suite verification run: 7/7 cases, all negative controls detected, exit 0 (owner-accepted 2026-11-09; evidence in `build/gen1-integration-portability-1-replacement-run/`, outside Git; the earlier environment-failed launch is preserved). Needs only Python 3 and Icarus Verilog; tested with Python 3.14.4 and one Icarus 14.0 development build, other versions not qualified. **RTL simulation only**: not silicon evidence, not exhaustive ISA coverage, not netlist equivalence. It is not part of `run_all_tests.py`, and it does not hash the board RTL files of the filelist | [README](../hardware/tests/spu13/gen1_integration/README.md) |

A reproduction is not a board run and adds no ledger entry.

## 4. Gen-1 timing qualification

**GEN1-STA-1: PASS — nominal routed static timing analysis of the frozen Gen-1 implementation under the recorded
constraints and assumptions** (owner decision, 2026-11-07). Record: [GEN1-STA-1 closure](GEN1_STA_1_CLOSURE_2026-11-07.md).
This is STA, not a board observation, and adds no ledger entry.

- Accepted results (attempt 2): setup WNS +6.360 ns, hold WHS +0.060 ns, recovery +17.927 ns, removal +0.233 ns, pulse
  width WPWS +9.500 ns, 0 of 20,176 endpoints failing; multi-corner (Slow and Fast) worst-of-both figures; check_timing clean
  apart from the `raw_rst_n` / `uart_tx` I/O-delay flags; no user exceptions; CDC safely timed; `cpu_clk` on one BUFG
  reaching 6,771 clock pins. Negative controls NC1 (setup), NC2 (hold) and NC3 (unclocked endpoints) detected as predicted.
- Owner protocol decisions: NC3's `set_clock_sense -stop_propagation` mechanism is accepted as a **post-hoc methodological
  repair** of attempt 1's invalid `delete_clocks`, not an unchanged frozen test; the evidence is accepted for internal
  qualification but was **not externally anchored** before execution.
- History: attempt 1 ended **UNKNOWN** (harness defects in the BUFG query and NC3; `build/gen1-sta-1/INTERPRETATION.md`).
  The implementing agent's acceptance review is not independent; the independent review was a separate reviewer agent of the
  **same model family** (`build/gen1-sta-1/attempt-02/INDEPENDENT_REVIEW.md`, outside Git; see §7).
- Not established by this STA: physical timing margin (device grade marking, oscillator, rails, temperature), asynchronous
  reset behaviour, and I/O timing (`raw_rst_n` has no input delay and `uart_tx` no output delay;
  [§3.40](hardware_evidence.md#340--cpu-board-4c-r1-first-fixed-program-surd-cpu-run-over-uart-2026-10-30)). The STA used
  speed grade −1; its temperature-grade property query returned empty. Margins are thin in places (hold +0.060 ns,
  removal +0.233 ns).
- Separately, and without changing this STA result: a scoped physical reset-recovery observation now exists
  ([§3.52](hardware_evidence.md#352--gen1-reset-edge-1-timed-key0-reset-recovery-of-the-golden-gen-1-image-2026-11-08-utc), §2).
  It is a board observation, not timing analysis, and it does not qualify reset timing, recovery/removal margins or
  metastability.

## 5. First-generation rational GPU

Source: [capability matrix](CAPABILITY_MATRIX.md) GPU row and known limitation 6. **Not production-ready.**

| Dimension | Status |
|---|---|
| Functional (host / RTL simulation) | Exact Python reference renderer and finite-width device model; RTL simulation "Yes" |
| Physical implementation | First video, first triangle, two-triangle depth ([§3.8–3.10](hardware_evidence.md#38-first-video-output--640x480-vga-on-a-monitor-2026-09-04)); T1G visual switching passed ([§3.37](hardware_evidence.md#337--t1g-two-cycle-visual-acceptance-retry-2026-10-07)), operator-observed, not exact pixel verification; T1H H1 **on hold** ([§3.38](hardware_evidence.md#338--t1h-scalar-diagnostic-visual-replay-2026-10-07)) |
| Timing | Tool-reported internal timing only; board-level I/O timing and reset behaviour **unqualified** ([Vivado baseline](../hardware/boards/artix7/spu_a7_gpu_vga_vivado_baseline_2026-10-25.md)) |
| Development | GPU/HDMI deferred until Gen-1 CPU qualification (desktop migration handover, §3, on branch `migration/snapshot-2026-11-06`). Open-flow GPUVGA repair (XC7-GPU-2 patch A) preserved but **unapplied** (preservation record `research/XC7_PRESERVATION_2026-11-06.md` is in the development and research history; it is not part of the curated v0.2 release) |

## 6. HEX-SOM (software-only research)

The [capability matrix](CAPABILITY_MATRIX.md) states that the HEX-SOM experiment and reproduction record were not located
in the checkout (RTL, synthesis and hardware: "Not established"). The final reports have since been located in the owner's
private recovery archive (`research/hex_som_2b/FINAL_REPORT.md`, `research/hex_som_3a/FINAL_REPORT.md`; not in Git).
Their recorded findings, unverified by rerun:

- **HEX-SOM-2B: CLOSED — PASS** for execution, exactness and registered confirmation. **Negative accuracy finding preserved:**
  on Iris the selected configuration *tied* the untrained baseline (0.9467 vs 0.9467); no learning-dynamics change produced
  confident accuracy above the untrained baseline; the earlier HEX-SOM-2 trained map scored 0.901 against 0.948 untrained;
  no hexagonal accuracy advantage over a square grid was demonstrated.
- **HEX-SOM-3A: CLOSED — PASS** for exact retrieval on the registered workload. Nested grouping cut candidate evaluations
  24.2% versus flat grouping but was 11.1% slower in setup plus query; no complete-cost advantage was demonstrated.
- Not established: any FPGA throughput, area or energy benefit; no hardware accelerator exists.

## 7. Evidence preservation

| Class | What | Backup status |
|---|---|---|
| In Git (local `dev/next`) | Ledger, capability matrix, frozen Gen-1 package, reproduction records, research findings (incl. Soul, QAF, bound, XC7), [GEN1-STA-1 closure](GEN1_STA_1_CLOSURE_2026-11-07.md), RP2350 pulse-generator source `hardware/rp2350/gen1_reset_pulse/`, portable Gen-1 integration regression `hardware/tests/spu13/gen1_integration/` | Local clone; public `dev/next` at `e7d37aa` is 14 commits behind `599dbd0a` (§1) |
| Outside Git, restored locally | `build/` run evidence for §3.40–3.51 (every cited directory present), `build/cpu-repro-1/`; the golden Vivado build directory | Restored from verified laptop migration archives |
| Outside Git, created on this host: GEN1-STA-1 | `build/gen1-sta-1/` attempt 1 and `attempt-02/` (harness, run, manifests, acceptance and independent reviews) | Private archive package `gen1-sta-1-evidence-20261107T051058Z` (129 files; `gen1-sta-1.tar.gz` sha256 `d8b50286…`). Second copy on removable media (stick `6745-6D7D`) made 2026-11-08 and **verified by read-back after unmount/remount**: package checksums 4/4, tarball byte-identical, 129/129 extracted files, internal manifests verified in place. Not verifiable inside the package by design: temporary checkpoint-copy hashes, and checkpoint hashes that name host paths. Recorded in the package's `USB_COPY.txt` |
| Outside Git, created on this host: GEN1-RESET-EDGE-1 | `build/gen1-reset-edge-1/` (34-entry `MANIFEST.sha256`, sha256 `f22157e6…`) and the bench pre-check `build/gen1-reset-edge-1-stage0-od/` | Private archive package `gen1-reset-edge-1-evidence-20261108T063542Z` (50 files: evidence, bench pre-check, generator source, planning notes, simulation bench; `gen1-reset-edge-1.tar.gz` sha256 `ddea1a38…`). Second copy on stick `6745-6D7D`, **verified by read-back after unmount/remount**: package checksums 4/4, 50/50 extracted files, 34/34 evidence manifest, tarball byte-identical. Recorded in `USB_COPY.txt` |
| Private recovery archive | Owner's archive indexed at `~/Archive/INDEX.md` (not in this repository): laptop migration archives, H0 UART-silicon bundle, Arch-era research, recovered laptop material; the two Gen-1 evidence packages above are separate dated folders added later and not listed in the frozen 2026-11-06 index | 2026-11-06 contents: second copy on separate removable media, verified by read-back on 2026-11-06. Gen-1 packages: see the rows above. The stick is **unencrypted**, **no off-site copy is established**, and encrypted storage for private parts is planned, not done |
| Unresolved / lost | Of 49 `build/` directories cited anywhere in the ledger, 19 are absent: 11 were in an Arch build archive lost on 2026-11-06, 8 were not in any located backup. All absent ones belong to entries before §3.40. Arch-era toolchain copies were also lost | Not recoverable from located copies |

## 8. Discrepancies between sources (not resolved here)

1. `cpu_v02/README.md` says the package is "not yet rebuilt"; REPRO-1B and the desktop record report bit-exact rebuilds. The
   README is hash-covered by the frozen package, so it is unchanged.
2. ~~The capability matrix CPU row (reconciled 2026-11-05) cites §3.40, 3.41 and 3.43, not §3.42 or §3.47–3.52.~~
   Resolved 2026-11-10: the row now cites §3.42 and §3.47–3.52 and links the architectural contract.
3. The capability matrix HEX-SOM row and [`V02_DOCUMENTATION_RECONCILIATION_2026-11-05.md`](V02_DOCUMENTATION_RECONCILIATION_2026-11-05.md)
   report no located HEX-SOM record; §6 reports recovered final reports outside Git.
4. Release regression counts quoted in session handovers (for example "269/0") are not recorded in a tracked document,
   so this index cites none.

## 9. Publication blockers (HOLD)

Completion criteria are listed only where a source defines them.

| # | Blocker | Status | Evidence or decision reference |
|---|---|---|---|
| 1 | GEN1-STA-1 timing qualification | **Closed: PASS** for nominal routed STA only (2026-11-07); physical margin, reset timing and I/O timing remain unqualified. The reset campaign GEN1-RESET-EDGE-1 is **closed: PASS** as scoped physical reset recovery (2026-11-08, 15/15, execution overlap inferred). It does not qualify reset timing or metastability. Both evidence packages have verified removable-media copies; no off-site copy | §4; [closure](GEN1_STA_1_CLOSURE_2026-11-07.md); [§3.52](hardware_evidence.md#352--gen1-reset-edge-1-timed-key0-reset-recovery-of-the-golden-gen-1-image-2026-11-08-utc); §7 |
| 2 | H0 tag `v0.2-h0-uart-silicon` | Local only; publication HOLD. **Owner decision 2026-11-10:** retained locally and excluded from the canonical v0.2 release (§11) | [§3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc); [ARCH_RECONCILIATION_HANDOFF](ARCH_RECONCILIATION_HANDOFF_2026-11-04.md) |
| 3 | Public branch synchronization and review | As of 2026-11-09 (§1): public `main` is 22 and public `dev/next` 14 commits behind `599dbd0a`, both ancestors, plus the commit containing this update; public default `master` is a separate history. Proposed: review, fast-forward `main`, make `main` the default (§10); not approved. **Superseded 2026-11-10:** no direct fast-forward; a curated release candidate instead, with `main` as the eventual default after verification (§11) | Owner decision pending; `docs/PUBLIC_BRANCH_RECONCILIATION_REVIEW_2026-11-05.md` on branch `migration/snapshot-2026-11-06` |
| 4 | Licensing clarification for RTL snapshots under `research/` | **Closed:** committed as `9f82f0d` (XC7-LICENSE-CLARIFICATION-0); not yet public | [LICENSING.md](../LICENSING.md) |
| 5 | Device-serial redaction | **CLOSED — owner-approved retention of previously public USB adapter serials** (2026-11-09). A read-only audit found three USB adapter serials, all already public; they are retained and no evidence is altered. Chip unique identifiers remain subject to redaction | [PUBLICATION_REDACTIONS.md](PUBLICATION_REDACTIONS.md) ("Retained unchanged on purpose") |
| 6 | 264 untracked `spu_strategy/` files at `d35e166` (`git status --porcelain --untracked-files=all -- spu_strategy`; 69 entries in default `git status`, which collapses directories; 4 further files are ignored). The earlier figure of 258 recorded no counting method; the difference matches the six GEN1-RESET-EDGE-1 planning, review and simulation files added on 2026-11-08 | Disposition pending (some are drafts or handovers; 7 contain a retained USB adapter serial, see item 5). The item-5 decision does not authorize their publication | Owner decision pending |
| 7 | Soul research handover in `research/` | HOLD; handover documents are excluded from release by policy | [PUBLICATION_REDACTIONS.md](PUBLICATION_REDACTIONS.md) ("Not included"); owner decision pending |
| 8 | Whether research belongs in the public repository | Open | Desktop migration handover, §4 item 3 (`docs/HANDOVER_2026-11-06_DESKTOP_MIGRATION.md` on branch `migration/snapshot-2026-11-06`); owner decision pending |
| 9 | Stale or incomplete summary documents (§8 items 1–3) | Open (item 2 resolved 2026-11-10) | §8 |
| 10 | Contributor terms (P2, added 2026-11-10) | `CONTRIBUTING.md`'s DCO refers to "the project's open-source license" (singular), while [LICENSING.md](../LICENSING.md) maps licences by directory. The frozen `cpu_v02/README.md` says this conflict must be settled before publication; it was missing from this table. **Owner decision:** clarify the per-file and per-directory licence wording, keep the DCO, no licensing redesign; human review of the final wording. Pending execution | Owner decision 2026-11-10 |

## 10. Proposed release packaging (2026-11-09; proposal only, nothing approved or performed)

Proposed form: a tag on a reviewed revision of the main repository, with a GitHub Release carrying the binaries.
No branch update, tag or Release has been made or authorized.

| Item | Status and constraint |
|---|---|
| Release branch | Fast-forward public `main` (an ancestor of local `dev/next`, §1) to the reviewed revision, then make `main` the GitHub default instead of the separate-history `master`. Each step needs separate approval |
| Proposed tested binary asset | Golden Gen-1 `.bit` `442a229e…` ([SOURCE_MANIFEST](../hardware/boards/artix7/wukong_v3/cpu_v02/SOURCE_MANIFEST.md)), with checksums and the source/build manifest. Its board evidence is SRAM loading only (§2) |
| Configuration payload `.bin` `cc259988…` | Reproduced bit-exactly (§3). **Never programmed to flash and never booted**: there is no qualified Gen-1 flash-boot evidence, and §3.50/§3.51 leave the flash identity and Gen-1 flash boot unestablished. It must not be described as tested; ship it only labelled as untested, or omit it |
| Release notes limits | Fixed 14-instruction program reporting over UART, not a freely programmable image; SRAM load (`openFPGALoader -c dirtyJtag`, no flash options); the image does not boot from flash after a power cycle; the §2 and §4 limits |
| Existing `v0.2-*` tags | `v0.2-lucas` (on the public remote, in `master`'s history, not in local `dev/next`) and `v0.2-h0-uart-silicon` (local only, annotated, an ancestor of `dev/next`; the experimental H0 image, blocker 2). A future `v0.2.0` release tag must be distinguished from both in its notes |
| GPU and HEX-SOM | No GPU bitstream is proposed unless its identity, board compatibility and evidence are reviewed (§5). HEX-SOM is software only (§6) |
| Open blockers | §9 items 6–10 remain; item 2 decided 2026-11-10 (H0 excluded); item 5 closed 2026-11-09. Superseded by §11 for packaging direction; publication remains **HOLD** |

## 11. Final readiness assessment at `a2cfee73` (2026-11-10)

Owner-accepted, read-only assessment. It changes no ledger entry and qualifies nothing beyond its cited sources.

**Technical readiness: READY as a scoped experimental release.** At `a2cfee73`:
- Frozen package manifests verify: 36/36 package files and 9/9 portable files.
- Golden `.bit` `442a229e…` and `.bin` `cc259988…` are present in the origin build tree, outside Git.
- The payload was reproduced bit-exactly twice (§3). Not re-run at this revision; the package is byte-identical.
- GEN1-STA-1 PASS, nominal only (§4).
- Physical observations: §2.
- [Architectural contract](GEN1_ARCHITECTURAL_CONTRACT.md) at `5948d8d5`.
- C++ `gen1-surd` profile at `14ab48a6`; `software/vm` is unchanged at `a2cfee73`, and its clean-tree build reproduced the frames.
- Conformance 79/79, including the RTL-backed fault-after-readback case.
- Full gate: `tools/verify_repo.sh`, detached job `spu-full-verify-01-20261109T203739Z-141975`, COMPLETE, **270 PASS / 0 FAIL** (evidence `build/gen1-gate-integration/full-verify-01/`, outside Git).
- Observation: two RTL benches fell back from Icarus to Verilator and passed; whether this occurred earlier was not established.

**Limitations that must appear in the release notes:**
1. **Machine:** fixed 14-instruction program; S0 only; four accepted encodings; no control flow; a new program requires bitstream regeneration.
2. **Physical evidence:**
   - single unit and single sessions; observations, not qualification;
   - JTAG/SRAM configuration only; flash boot not established (the `.bin` must be labelled untested, or omitted);
   - fault frames and normalization are verified in RTL simulation only.
3. **Timing:** nominal STA with thin hold and removal margins; I/O timing, reset timing and metastability unqualified; the STA's independent review was by a reviewer of the same model family.
4. **Software:**
   - `gen1-surd` agreement is software conformance, not RTL or silicon evidence;
   - the legacy C++ VM and the Python VM do not implement Gen-1;
   - 0x70–0x73 carry telemetry names in `spu13_arch.h` and the assembler (contract D1).
5. **Reproducibility** is specific to Vivado 2026.1 build 6511674, part `xc7a100tfgg676-1`.
6. **H0** is a separate experimental image and is not part of this release.

**Publication blockers and owner dispositions:**

| # | Blocker | Disposition |
|---|---|---|
| P1 | Research in the release branch: fast-forwarding public `main` to `dev/next` would publish 409 files, 352 under `research/`, including 62 Soul files and the Soul handover | **No direct fast-forward.** Build a curated release candidate from public `main` by controlled path-based integration, with a source-to-destination manifest (original commit and file hashes). It needs its own full regression and reproducibility check; this assessment does not transfer to it. `dev/next` and the isolated research clone are unchanged |
| P2 | Contributor terms (§9 item 10) | Clarify licence wording; keep the DCO |
| P3 | Default branch | `main` eventually, after the candidate is verified and integrated; `master` history is kept intact, with no force-push or deletion |
| P4 | H0 tag | Retained locally; excluded from the canonical release. Proposed tags: `v0.2-rc1`, then `v0.2.0` |

**States:**
- **Approved direction:** a curated release candidate; `main` as the eventual default; H0 excluded.
- **Pending execution:** the curated-branch plan and construction, the licence-wording correction, branch synchronization, the public README revision against the curated tree.
- **Still HOLD:** pushes, public tags, release publication, default-branch changes.
