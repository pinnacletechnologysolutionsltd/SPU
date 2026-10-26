# RET-4 — bounded build hygiene preparation, 2026-10-19

Closed at owner direction; **HOLD — no deletion authorized**. No existing build artifact was deleted,
changed, moved, compressed, archived or overwritten. INF-1R remains R_HOLD;
this inventory is the separately requested read-only maintenance operation.

Reused [RET policy](BUILD_ARTIFACT_RETENTION.md),
[RET-1](RET1_RESTORATION_REVIEW_2026-10-18.md),
[RET-2C](RET2C_REASSESSMENT_2026-10-18.md),
[RET-3](ret3_review/README.md) and the existing retention inventory. No new
archival framework, dependency graph or recursive content scan was created.

## Size and scope

One metadata-only traversal, no symlink following: ceiling 20 seconds / 500,000
entries; completed in 6.83 seconds, 310132 entries, 37899 directories and 262 skipped
symlinks; zero I/O errors. Apparent regular-file bytes **74459374673 (69.35 GiB)**;
unique-inode allocated bytes **75092738048 (69.94 GiB)**. Directory allocation excluded.
This is a live observation, not a stopped-source snapshot. Btrfs reflinks,
snapshots and sharing mean allocated bytes are not guaranteed reclaimable bytes.
Read-only metadata may update access times under filesystem policy.

| Largest top-level consumers | Apparent GiB |
|---|---:|
| `build/spu_surd_register` | 40.50 |
| `build/toolchains` | 3.78 |
| `build/pell_rtl1` | 2.31 |
| `build/gpu` | 1.65 |
| `build/t1d_rtl_sim_worktree_20260916` | 1.42 |
| `build/gpu_evaluation` | 1.26 |
| `build/stage_b_clean_d88ee61` | 1.10 |
| `build/sparse_jet_mac` | 1.07 |

Largest individual files: three OSS CAD Suite archives, each 747,823,634 bytes;
Diagnostic-02 stderr 555,264,799 bytes; three xc7a100t BBA files, each
464,566,361 bytes; bottleneck timing logs 426,649,382 and 426,645,797 bytes;
compact-03 native route capture 387,324,934 bytes. These are **PROTECT**, not
proposed removals. Equal size is not duplicate-content or dependency evidence.
The earlier whole-build inventory recorded 69,233,882,436 apparent bytes on
2026-10-17 UTC; scopes are comparable observations, not exclusive-storage deltas.

## Protection and candidate confidence

- **Verified disposable / approved reclaim: zero.** No stopped-source or
  independent recovery boundary was established here.
- **Strong generated-intermediate candidates:** the three caches below total
  25,694 apparent / 28,672 allocated bytes. Both retained review manifests
  explicitly exclude caches; retained source hashes and timestamp/size headers
  match. This establishes rebuildable-cache candidacy, not absence of every
  external reference or permission to remove them.
- **Low confidence, not a removal estimate:** 16,506 Python cache files total
  381,480,984 apparent bytes across build/. This includes tool installations and
  frozen trees; do not bulk-delete. Repeated tool archives/BBA files and build
  objects require narrowly scoped dependency/restoration decisions first.
- **Uncertain material stays PROTECT:** especially the sampled parent
  prepare_snapshot cache whose timestamp/size header no longer matches source.

Known protected/external boundaries: all seven RET-2/RET-3 candidates; all 475
RET-1 review entries; CPU timeout telemetry, packet-06 route/capture and pinned
inputs; CPU D1/R3 source and dependency pins; RUNNER-F2 and SSM-4 evidence;
SG-0/SSM-3 baselines; SIM-G1 archives and external spu-sim consumers; FPGA
bitstreams/constraints/timing; toolchains and chipdb. Existing INF-1 records
remain historical evidence. No original PROTECT classification is changed.

Git worktree registration protects curation_worktree_20261007,
d4_canonical_decision_p1b/qualification_source_01, both sparse_jet_mac source
trees, isa_software_semantics/qualification_source_01,
spu_lossless_reduction/c0_cpu_20261005/gate_checkout_01, stage_b_* registered
trees, t1d maintenance/RTL worktrees and t1e_depth_arbitration_qualification's
clean_checkout. These are exact families identified by `git worktree list
--porcelain`, not deletion globs. Active ownership/quiescence of any build
directory remains unconfirmed; process listings cannot establish disposability.

## One small conditional batch (three files only)

All paths below are relative to repository root; source files, manifests,
reports and cache directories themselves remain untouched. Candidate cache
mtimes are 2026-10-02 UTC; age is not a deletion criterion.

- `build/gpu/t1r_vgafix_control_verification_20261002/review_02/__pycache__/build_isolation_fixtures.cpython-314.pyc` — 7843 apparent / 8192 allocated bytes.
  SHA-256 `5901978034dc87a08ebcfcb1659e3e2a0ba4c97fe2a0273cd8b0d14ceefb8f99`.
  Preserve `build/gpu/t1r_vgafix_control_verification_20261002/review_02/build_isolation_fixtures.py`
  (SHA-256 `cca4d7791601c95d7c44b419111037ef03a3332c70d37c3a71f9d2ff27df2c32`).

- `build/gpu/t1r_vgafix_control_verification_20261002/review_03/__pycache__/build_isolation_fixtures.cpython-314.pyc` — 7843 apparent / 8192 allocated bytes.
  SHA-256 `ec3ba0b67fcde16987ce88387bc0cc186aefe38a7bf22a0c8eac4c42b8e2668f`.
  Preserve `build/gpu/t1r_vgafix_control_verification_20261002/review_03/build_isolation_fixtures.py`
  (SHA-256 `cca4d7791601c95d7c44b419111037ef03a3332c70d37c3a71f9d2ff27df2c32`).

- `build/gpu/t1r_vgafix_control_verification_20261002/review_03/__pycache__/virtualenv_fixtures.cpython-314.pyc` — 10008 apparent / 12288 allocated bytes.
  SHA-256 `f2b54dd2b6612689f4eee1346bb4ab72daf921e6e9f3cc139d98995d92d9ad6c`.
  Preserve `build/gpu/t1r_vgafix_control_verification_20261002/review_03/virtualenv_fixtures.py`
  (SHA-256 `1d48ea895b647068973c1838896ae2f0e85cf952e5ed599c6e61acaee83ab481`).

Before approval: owner confirms stopped writers/no sourceless or explicit cache
consumer for these three paths; review the named review contracts and manifest
exclusion, and resolve any known external pins. Unknown dependencies keep that
member PROTECT. Do not infer no references from a scan omission. Use RET-1's
existing strict member/hash verification for preserved evidence; this proposal
introduces no archive, restore or executable replay operation. The source/
evidence preservation checks above do not claim independent recovery.

Execution requires a separate explicit exact-path approval after those checks.
Immediately before removal recheck types, all parent paths for symlinks, file
hashes, single-link status and source/manifest identities at the stopped-source
boundary; abort on drift. Delete only the approved files, never a wildcard or
whole directory. Afterwards verify only approved paths disappeared, all retained
manifest members still match, sources are unchanged and record measured free
space plus a permanent approval/execution receipt under the existing RET policy.
No recreation, test import, compile or replay is authorized by this preparation.

This pilot is deliberately tiny and will not materially recover the 69 GiB.
Meaningful recovery needs one owner-selected large retention boundary (for
example toolchain copies) resolved under existing RET controls, not more
infrastructure or a repository-wide dependency investigation. Keep that decision
independent of ongoing mathematics/GPU/simulator work.

Validation: review_02: 10 retained manifest members match; review_03: 14 retained manifest members match. Three candidate source/header/hash
checks pass; fourth mismatched cache excluded. A bounded follow-up metadata
walk of pell_rtl1/gpu/aor1 (30,000-file / 3-second cap) located these examples;
only the two named small review manifests and their declared files were read
for retention verification. No cleanup, research experiment or qualification
fixture executed.

Documentation checks: changed-file links and whitespace pass (including
untracked files). `python3 -B tools/doc_audit.py --actual-pass 238` exited zero
but reported 14 broken links, 30 uncited claims, one stale total, 126 orphans
and one superseded-status finding in its tracked-document scope. That audit
is not a clean repository qualification; no unrelated repairs were attempted.

## Closure — owner decision, 2026-10-19

RET-4 investigation is closed at HOLD. Inventory/classification was completed
within its bounded scope; writer/consumer closure remains unresolved and
reconstruction assurance unverified. Actual reclaimed storage: **0 bytes**.
The earlier three-bytecode-file proposal is abandoned, not a cleanup batch.

Retain these exact database candidates for possible review during a future
backend rebuild, relative to
`build/spu_surd_register/backend_compatibility_20261012/compact_sink_capture_tool_build_02/compile/`:

| Candidate | Allocated bytes |
|---|---:|
| `himbaechel/uarch/xilinx/chipdb-xc7a100t.bba` | 168,517,632 |
| `himbaechel/uarch/xilinx/chipdb-xc7a100t.bin` | 40,108,032 |
| `share/himbaechel/xilinx/chipdb-xc7a100t.bin` | 40,108,032 |
| **Potential allocation ceiling** | **248,733,696 (237.2 MiB)** |

This ceiling is not verified reclaimable Btrfs space. All candidates and other
protected evidence remain PROTECT; no deletion, archive, rebuild or further
investigation is authorized by closure. Reconsider only alongside separately
authorized backend maintenance with preservation and ownership checks resolved.
RET-4 HOLD is not a dependency for CPU qualification, GPU bring-up, simulator
conformance or separately authorized bounded architectural research. No new
hardware attempt or frozen campaign budget is authorized by this priority order.
