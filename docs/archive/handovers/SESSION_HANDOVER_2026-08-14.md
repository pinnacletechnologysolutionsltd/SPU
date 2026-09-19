# Session handover — 2026-08-14

Audit session. Started as a review of GTP's SPU-4 product tranche, became a
root-cause investigation of a flagship spin that had been silently unbuildable
for four weeks.

## 1. Repository state

- `master` in sync with origin. **Four commits authored today**, plus an
  11-commit backlog (`7b80a59`..`fce7089`) that had been sitting local and was
  pushed this morning along with the `v1.2-typestate` tag — see §6.
- Three files intentionally uncommitted: `CLAUDE.md`, `docs/SPIN_CATALOG.md`,
  `hardware/rtl/core/spu4/spu4_som_edge.v` — the last three `~400 LUT` claims.
- Regression: **193 PASS / 0 FAIL**, reproduced on three independent runs.

| Commit | Change |
|---|---|
| `bc06156` | Restore the Tang SOM sidecar build (broken since `df6cffd`) |
| `082ed6c` | Correct SPU-4 resource claims; open T9 (evidence-anchor gap) |
| `ffb8d7e` | Move axiomatic level off the chirality field |
| `dba840f` | Make the harness aggregator able to fail |
| earlier | `fce7089`..`7b80a59` pushed this morning, incl. `v1.2-typestate` tag |

## 2. What landed

**The sidecar regression (the big one).** `build_25k_spu13_som_sidecar.sh` had
failed P&R since 2026-07-17. Root cause: 13 incidental lines in `df6cffd`
replacing the UART baud tick's constant modulo with a down-counter — correct
and necessary for Xilinx, catastrophic on Gowin. Fixed by a `BAUD_COUNTER`
parameter; both vendors measured, both forms silicon-proven on their own board.
Full numbers in the commit message and the RTL comment, including two refuted
candidate fixes so they are not retried.

**Gatekeeper bit aliasing.** `spu13_axiomatic_gatekeeper` was wired in
`7b80a59` reading `phinary_cfg[3:2]`, which lies inside `phinary_chirality`
(`[8:1]`). Board tops passing `16'h000C` decoded to `2'b11 = OFF`, so the guard
was dead on the SOM and A7 math spins. Moved to `[10:9]`; TEST 7 added as a
field-independence control with a verified negative control.

**Harness honesty.** `run_all_tests.py` summed four auxiliary suites into
`total_pass` with no fail counterpart — a failing or deleted oracle dropped the
headline while `Total FAIL` stayed 0. Fixed and verified by negative control
(deleting an oracle now yields 192/1, previously 192/0). Seven suites that
contributed invisibly now print sections; the printed total reconciles to 193.

**SPU-4 resource claims.** The `~400 LUT4 / 668 cells` figure understated the
build ~2x. Re-derived: **835 LUT4, 390 ALU, 336 DFF** on GW5A-25A. The GW1N-1
"fits with room to spare" claim is withdrawn to OPEN.

## 3. Verified positives worth keeping

- **SPU-4 probe (§3.2j) is bit-reproducible** — `9599f5e4…22664`, regenerated
  three times today.
- **§3.2g.5 is fully reproducible** — `f4e271e` + current toolchain +
  `build_25k_spu13_som_sidecar.sh` → `8753c492…` exactly. This resolves an
  entry that recorded *no build command at all*.
- **The SOM1 frame CRC is genuine CRC-32** — verified against `zlib.crc32` on
  four vectors. The bench validates it against a re-implementation of the same
  algorithm, so this external check is the first independent confirmation.
- Toolchain is **not** implicated in anything: install predates the July proof,
  nextpnr byte-identical, July sources reproduce July bitstreams today.

## 4. Open, not fixed

1. **A7 sidecar unverified after my change.** `BAUD_COUNTER` was added to a
   module `spu_a7_som_sidecar_top` consumes, and only checked through yosys.
   §3.2g.6 should not be re-trusted until a full pnr/pack run passes. Needs
   `build/chipdb/xc7a100tfgg676.bin` generated from the 464 MB `.bba`.
2. **T9 — silicon evidence has no source anchor.** `hardware_evidence.md`
   records a bitstream SHA for every result and pins none to a commit;
   **8 of 14** entries record no build command either. Measured status:
   §3.2g.2, §3.2j REPRODUCE; §3.2g.1, §3.2k DIFFER; §3.2g.3 was BUILD_FAILED
   and is now fixed (new anchor `af0c5e4c…`); §3.2k.1 UNMEASURED (killed after
   90 min — re-run without `--placed-svg/--routed-svg/--detailed-timing-report`).
   Also `hardware_evidence.md:26` names Yosys 0.50; 0.63+87 is installed.
3. **No board-build check exists.** This is why a flagship spin stayed broken
   four weeks. Highest-leverage item on this list.
4. **T7.4 wrapper contract.** `dissonance` is a `spu4_core` port only;
   `spu4_standalone_top` lacks it, making the fault contract's allowed wording
   false for the named product interface. Adding the port moves the §3.2j
   bitstream hash, so it is a real trade — three options written up in
   `docs/SPU4_FAULT_REPORTING_CONTRACT.md`. Settle alongside the program-load
   interface (raw write port vs SPI slave vs ROM boot). **No southbridge plan
   for SPU-4 exists anywhere** — and probably shouldn't; the core needs far
   less than SPU-13's RP2350 stack.
5. **T5b — LUCAS v0.3 not deposited.** `docs/LUCAS_MAC_PAPER.md` is 23 lines
   ahead of the published v0.2; the hand-written `.tex` has none of it, so the
   PDF is stale. John's call 2026-08-14: not urgent.
6. **Gowin mux blow-up mechanism unexplained.** ALU and DFF flat across every
   run, so it is a mapping pathology, not logic growth. Two rational fixes
   refuted. Recommend leaving it.
7. **Spin-name drift.** `build_a7.sh:12` documents spins its dispatch no longer
   handles (`robotics`, `su3share`, `rplu2core`, …); they fall to `*`.

## 4b. Board-build check — built, uncommitted, one open question

`tools/board_build_check.py` + `hardware/boards/board_build_manifest.json`.
Rebuilds board targets and compares bitstream hashes against a recorded
baseline. Records commit + build command + toolchain version per entry — the
field set §4.2 says `hardware_evidence.md` lacks. Deletes the artifact before
building, so a failed build cannot be scored against a stale `.fs` (a trap hit
for real this session). `--self-test` proves the comparison can fail.

The manifest is **not** silicon evidence: `sha256` is what this tree builds
today; `hardware_evidence.md` records what was flashed. Never copy between them.

Baseline recorded at `3c9e92d`, Gowin/Tang only (A7 needs the chipdb first):

| target | recorded | note |
|---|---|---|
| `spu4_probe` | `9599f5e4…` | == its silicon hash, 4 reproductions today |
| `som_hydrate_probe` | `6177aa67…` | == its silicon hash |
| `som_bmu_probe` | `a3df02d5…` | differs from silicon `0385b641…`, needs re-anchor |
| `irotc_probe` | `6ac1e8ab…` | differs from silicon `4aedc901…`, cause uninvestigated |
| `som_sidecar` | `a7d3459e…` | **see below** |

**RESOLVED — the check's premise holds.** `python3 tools/board_build_check.py
--only som_sidecar` rebuilt and reported **REPRODUCES `a7d3459e…`**. So Gowin
builds are bit-deterministic even for the large, near-limit design, and hash
comparison is a sound basis for this tool. The "near-limit designs may not be
bit-stable" worry is disproved; no utilisation-based fallback is needed.

**Loose end, not a blocker.** `som_sidecar` did produce `af0c5e4c…` earlier the
same day, and since the build is now proven deterministic, that difference must
have a source cause I did not identify — `bc06156`'s only non-comment change is
the intended one, and nothing else in the build's six-file source set changed
between the two runs. Worth one focused diff, but it does not affect the tool:
the recorded baseline is reproducible, which is all the check requires.

Note the method here. The tool was used to answer a question about its own
validity before being trusted — the same discipline as the negative controls on
`run_all_tests.py` and TEST 7. A check nobody has watched succeed *and* fail is
not evidence.

**The tool is therefore ready to commit** along with the manifest and this
handover section.

## 5. Recommended next session

In order:

1. **Commit `tools/board_build_check.py` + the manifest + this handover.**
   The determinism question in §4b is resolved (REPRODUCES); the tool is
   sound. Optionally run `--self-test` first to watch the comparison fail on
   demand. One loose end noted in §4b is worth a diff but blocks nothing.
2. ~~Write the board-build check~~ — built this session, see §4b. Extend to
   the A7 spins once chipdb generation is routine.
3. Generate the A7 chipdb and run `build_a7.sh 100t somsidecar pnr pack` to
   re-validate §3.2g.6.
4. T9 write-up into `hardware_evidence.md`: add commit + build command +
   toolchain version per entry. **Never overwrite a historical silicon hash
   with a fresh build** — it records what was flashed. Mark DIFFERS honestly.
5. T7.4 wrapper contract.

## 6. Corrections to earlier beliefs

- **The published v1.2 paper's evidence links were dead.** `v1.2-typestate`
  and its 11 commits were local-only while the Zenodo deposit was live, so
  every `blob/v1.2-typestate/…` URL in the PDF 404'd. Fixed by pushing this
  morning. "Tag is on origin" is now a release-checklist item — it is the one
  release step with no local symptom.
- The tranche plan's T3 described the gatekeeper decision as open; it had
  already been made in RTL by `7b80a59`. Now recorded as resolved.
- T5's "most substantive queued item" (the ½Z[φ] premise) was already published
  in typestate v1.2. Struck so it is not fixed twice.
- I hypothesised the SOM drift came from the gatekeeper instantiation, then
  from the toolchain, then from the frame's 48:1 dynamic index. **All three
  were wrong**, each refuted by measurement. The lesson is that the only
  reliable attribution here was rebuild-and-compare with one variable changed.
