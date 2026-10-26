# RET-1: restoration qualification and dependency review

Date: 2026-10-18. Status: ACTIVE.
Spec author, halt-and-flag implementer and auditor: Codex, sequential roles.

## Pre-execution review

```bash
cat docs/BUILD_ARCHIVE_RESTORATION_REVIEW_2026-10-07.md
cat docs/research/surd_lorentz_20261011/evidence/REVIEW.md
git worktree list --porcelain
```

External legacy verifier still lacks directory parity and permits missing Git
metadata. Retain it unchanged. Replace its acceptance path with repository-owned
JSON manifests; explicitly reject unsupported relocation/external dependencies.
Do not interpret qualification as authorization for production pruning.

## Scoped implementation

1. Add `tools/retention_tree.py`, `tools/retention_git.py`,
   `tools/verify_restore.py`, and `tools/retention_archive.py`. Inventory exact
   path/type/mode/hash/link sets, preserve empty directories, validate confined
   Git administrative paths, HEAD, NUL-delimited status and staged index state.
   Reject special files, external/absolute links, Git alternates, ambiguous
   paths, archive duplicates and traversal. Never mutate a restored tree to
   make it match. Require the externally pinned package/manifest digests.
2. Add isolated negative-control tests in
   `software/tests/test_retention_restore.py` and
   `software/tests/test_retention_git.py`. Cover corruption/substitution,
   missing/extra members of every supported type, mode changes, Git dirty/clean
   parity, relative/broken pointers, detached HEAD and staged-only objects.
3. Add `tools/retention_dependencies.py` and `tools/audit_build_storage.py`.
   Inventory Surd metadata with allocated blocks and inode/link identities.
   Scan bounded text inputs for explicit paths; record skipped inputs and
   unresolved references. Never claim static scanning proves graph completeness.
   Produce `PROTECT`, `ARCHIVE_THEN_REVIEW`, `ELIGIBLE_FOR_APPROVAL` outcomes;
   leave every current candidate protected, with no eligible deletions.
   Add allocation/graph controls in `software/tests/test_retention_storage.py`.
4. Add `tools/retention_rehearsal.py`. Copy only hash-verified Lorentz inputs
   into a fresh staging tree, package and independently restore into another
   fresh tree; compile restored sources and replay positive/poisoned streams.
   Audit compiled source identities. Preserve all original sources and results.
5. Add `docs/RET1_RESTORATION_REVIEW_2026-10-18.md`; link it from the policy.
   Report package hashes, exact scope, unresolved dependencies and allocation
   limitations. Archive disk selection, two-copy recovery and pruning remain held.

## Verification commands

```bash
python3 software/tests/test_retention_restore.py
python3 software/tests/test_retention_git.py
python3 software/tests/test_retention_storage.py
python3 software/tests/test_build_artifact_inventory.py
python3 tools/build_artifact_inventory.py --help
python3 tools/audit_build_storage.py --help
python3 tools/verify_restore.py --help
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- tools/retention_tree.py tools/retention_git.py tools/verify_restore.py tools/retention_archive.py tools/retention_dependencies.py tools/audit_build_storage.py tools/retention_rehearsal.py software/tests/test_retention_restore.py docs/BUILD_ARTIFACT_RETENTION.md docs/RET1_RESTORATION_REVIEW_2026-10-18.md spu_strategy/contract_ret1_2026-10-18.md
```

Use fresh evidence directory `build/repository_cleanup/ret1_20261018_01/`.
Run the rehearsal with a 55-second subprocess limit. Launch the complete
read-only dependency/allocation scan via `tools/run_detached_job.sh` with a
900-second external timeout if expected to exceed 60 seconds; record the unit
and end the turn immediately after LAUNCHED, per root contract §4.2. Do not
poll, extend timeout, or relaunch a timed-out scan without owner authorization.

## Stop conditions and limits

Stop on historical hash mismatch; do not substitute today's source. Refuse
existing output paths. No production moves, deletions, compression, worktree
administration, toolchain changes, FPGA builds or qualification-claim upgrades.
Restrict all generated outputs to fresh build children or temporary test fixtures.
This is retention-specific tooling; no RTL, arithmetic or shared runner changes.

## Recorded execution

Focused verification passed (17 tests including existing inventory controls).
Lorentz restored replay passed with 853 retirements and expected poisoned-stream
rejection. Detached scan completed with exit 0 in 79 seconds under the frozen
900-second limit; unit `spu-scan_job-20261017T194554Z-1081228`. Exactly one
terminal marker was checked in the next invocation. Dependency closure,
independent storage copies and production-pruning qualification remain held.
