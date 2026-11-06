# Handover: laptop → desktop migration (2026-11-06)

Written on the laptop (`john-MacBookAir`, checkout `/home/john/spu-public-v0.2-rc2`) before moving to
the desktop. It records what is in git, what is only in archives, the state of each workstream,
and the open decisions. **Repository cleanup and reorganisation are deliberately deferred until
the archives are restored on the desktop.**

## 1. Git state

**Remote:** `public` = `https://github.com/pinnacletechnologysolutionsltd/SPU.git`. This is a **public** repository.

| Ref | Head | Pushed to `public`? | Notes |
|---|---|---|---|
| `dev/next` | `e7d37aa` | Commits yes; branch name added in this migration | v0.2 working line. ISA repairs (a12c318, 1934197, 469cb9e), LITHIC (f35d03c), ledger 3.47–3.51 |
| `research/soul-evidence-0` | `2773b7c` | yes | `dev/next` + 1 research commit (soul evidence). **This was the branch checked out in the shared laptop worktree at migration time** (switched by another workstream) |
| `main` | `9fe2cee` | branch name added in this migration | Ancestor of `dev/next` |
| `exp/idnt-r1` | `b7fdf47` | **only via this migration** | IDNT R1 experiment (worktree `build/idnt-r1-worktree`). Not merged; merging needs separate owner authorization |
| `migration/snapshot-2026-11-06` | see `git log` | added in this migration | Snapshot of every untracked or modified file in the laptop worktree except `spu_strategy/` (owner backup) and `clockInfo.txt` (Vivado scratch), plus this handover. Built on `research/soul-evidence-0` without changing that branch or the worktree |

- The detached-HEAD worktrees under `build/*-worktree` (H0 and frontend experiments) are all at
  commits reachable from the branches above, so no commit is lost. Their working files are in the
  `build/` archive.
- **The snapshot commit is unsorted.** It mixes workstreams: soul/QAF research, the southbridge PCB
  proposal, `pico_setup.sh`, and README edits by other agents. Sort it during cleanup.

## 2. Not in git: archives (`~/spu-migration-2026-11-06/`)

| Archive | Source | Content |
|---|---|---|
| `spu-build.tar.zst` | `<checkout>/build/` (about 2.1 GB raw) | All run evidence, harnesses, job records, routed checkpoints, worktrees |
| `spu-gate.tar.zst` | `~/.local/gate/` (about 1.2 GB raw) | Isolated build clones. **The golden Gen-1 build is here**: `spu-int3b-c3efc18/build/vivado/{board3_01,board3p_01,board4b_01}` (golden `.bit` 442a229e…, routed checkpoint 48e0e161…) |
| `claude-memory.tar.zst` | `~/.claude/projects/-home-john-spu-public-v0-2-rc2/memory/` | Agent memory notes |
| `SHA256SUMS` | — | Hashes of the three archives |

Not archived:
- `spu_strategy/`: the owner backed it up separately.
- Toolchains, which need reinstalling on the desktop:
  - Vivado 2026.1 (`~/2026.1/Vivado/bin/vivado`);
  - OSS CAD Suite 20261027 (`~/.local/opt/oss-cad-suite-20261027`, which includes openFPGALoader v1.2.0).

**Restore notes:**
- **Absolute paths.** Every harness, evidence record and ledger citation uses absolute paths under
  `/home/john/spu-public-v0.2-rc2/` and `/home/john/.local/gate/`. Restore to the same paths (same
  user name), or expect frozen harnesses to refuse to run (they check their own hashes and paths).
  Do not edit frozen harnesses to change paths. Make new copies and record the diff, as was done
  for GEN1-REPEAT-1.
- **Commands:**
  - `cd ~/spu-migration-2026-11-06 && sha256sum -c SHA256SUMS`
  - `zstd -dc spu-build.tar.zst | tar -C /home/john/spu-public-v0.2-rc2 -xf -`, after cloning the repository to that path
  - `zstd -dc spu-gate.tar.zst | tar -C /home/john/.local -xf -`
- **Worktrees.** The `build/*-worktree` directories contain `.git` link files that point at the
  laptop checkout's `.git/worktrees/`. After restoring, run `git worktree prune`, or recreate the
  needed worktrees with `git worktree add`.
- **Verify after restore:**
  - `build/*/MANIFEST.sha256` (run from each directory);
  - `build/gen1-*/` evidence;
  - the golden checkpoint `sha256sum ~/.local/gate/spu-int3b-c3efc18/build/vivado/board3p_01/route/routed.dcp` → `48e0e161…`.

## 3. Workstream status

**Gen-1 CPU qualification** (frozen `hardware/boards/artix7/wukong_v3/cpu_v02/`, top `cpu_board_2r_top`):
- **Silicon (ledger):**
  - 3.40 golden; 3.41 one-word variant; 3.42 one KEY0 press; 3.43 Variant B;
  - 3.47 three reloads; 3.48 five KEY0 restarts; 3.49 Variant A;
  - 3.50 cold power cycle: **the board self-configures at power-on from a bitstream already in
    flash** (owner: probably the last GPU image; not identified, no flash read);
  - 3.51 a golden load after a cold power cycle: PASS.
- **Timing, GEN1-STA-1** (`build/gen1-sta-1/`, read `INTERPRETATION.md`):
  - Disposition **UNKNOWN**. Attempt 1 of 1 is consumed.
  - Nominal STA on the golden routed checkpoint reproduces the recorded values exactly: WNS
    +6.360, WHS +0.060, recovery +17.927, removal +0.233 ns. check_timing is clean apart from the
    two intended I/O flags. CDC is safe, there are no exceptions, and REPRO-1B agrees.
  - Negative controls: NC1 (setup) and NC2 (hold) behaved as predicted.
  - The judge printed FAIL because of a harness BUFG-query defect. Vivado's own clock path shows
    `cpu_clk_reg/Q` → `cpu_clk_BUFG_inst` → 6,771 loads.
  - NC3 did not run (`delete_clocks` is not a Vivado command).
  - Closing it needs an owner-authorized attempt 2 with the two fixes in `INTERPRETATION.md`.
  - The readiness assessment is in `spu_strategy/GEN1_TIMING_READINESS_2026-11-06.md` (in the
    owner's backup). Even a PASS is STA within the assumptions: speed grade, oscillator and
    operating conditions are unverified on the board.
- **Open dimensions:**
  - a KEY0 press during execution, and reset-edge timing;
  - timing margin and electrical measurement;
  - Gen-1 flash boot, and the identity of the current flash content;
  - other programs.
- **Board state at handover:** the golden Gen-1 image was loaded in SRAM after 3.51. The flash
  holds the older image. Power-on will boot the flash image, not Gen-1.

**ISA:** the compatibility campaign is closed PASS (a12c318, 1934197, 469cb9e; regression
269/0). LITHIC QNORM/IDNT rows are corrected and the HEX/QLOAD conflicts recorded (f35d03c).
QNORM, QLOAD and HEX semantics are deferred. The ISA is still early and unstable; frozen versions
are the working method.

**IDNT R1** (`exp/idnt-r1`):
- Scoped simulation PASS; release regression 270/0. Synthesis UNKNOWN; hardware NOT RUN.
- Integration is DEFERRED.
- Evidence: `research/idnt_r1/` on the branch, and `build/idnt-r1-worktree/build/regress/idnt-r1-release-01`.

**H0** (programmable CPU research, ledger 3.46): experimental. It is not the qualification
baseline.

**GPU/HDMI:** deferred until CPU qualification is complete.

## 4. Open decisions for the owner
1. **Device serial in the public ledger.** The DirtyJTAG serial `CB81353DCE678119` appears in
   `docs/hardware_evidence.md`, in 3.40–3.51 and earlier entries, and is already on `public`.
   `docs/PUBLICATION_REDACTIONS.md` says device serials are normally redacted for publication.
   Decide whether to redact going forward. Rewriting pushed history is a separate decision.
2. **GEN1-STA-1 attempt 2:** authorize it or not.
3. **Repository cleanup:** sort the snapshot branch, retire stale worktrees, choose the
   integration line (`dev/next` vs `main`), and consider whether research belongs in this public
   repository.
4. **The stale package README line.** `hardware/boards/artix7/wukong_v3/cpu_v02/README.md` still
   says the build is "not yet rebuilt"; CPU-REPRO-1B rebuilt it bit-exactly.
