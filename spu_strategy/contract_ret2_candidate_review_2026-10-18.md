# RET-2: exact-path candidate review

Date: 2026-10-18. Status: COMPLETE (candidate preparation only).
Roles: Codex as author, implementer and auditor, in sequence.

## Pre-execution review

```bash
ls build/repository_cleanup/ret1_20261018_01/scan_job
cat build/repository_cleanup/ret1_20261018_01/scan_job/result.json
cat build/repository_cleanup/ret1_20261018_01/surd_review/btrfs_allocation.json
```

Exactly one terminal marker is present: COMPLETE. Exit 0, duration 79 seconds,
900-second limit. Do not relaunch the scan or alter its retained outputs.

## Scope and implementation

1. Read existing metadata and dependency graph. Select individual artifacts:
   the frozen Lorentz CPU source, Packet 06 routed JSON/native capture, the
   diagnostic-02 stderr log, integrated-context tool/stderr logs and the
   separately reviewed OSS CAD Suite archive. Do not infer supersession from names.
2. Read their relevant qualification, timeout and publication records. Hash only
   these selected files, compare current inode/size/time identities to the scan
   and retain the result. Equal hashes establish byte identity only.
3. Create a compact repository index in `docs/ret2_candidates_20261018.json`
   with exact paths, measured metadata, content identities, referenced evidence,
   archival requirements and unresolved blockers. Keep every outcome PROTECT;
   approve no deletion and claim no reclamation estimate.
4. Retain preparation code and source-report hashes in a new child
   `build/repository_cleanup/ret2_candidates_20261018_01/`.
5. Update only RET-1/RET-2 reports and the retention-policy navigation. Existing
   campaign contents, qualification ledgers, source snapshots and classifications
   must remain unchanged. Do not launch another scan or hardware campaign.

## Verification

```bash
python3 software/tests/test_build_artifact_inventory.py
python3 tools/build_artifact_inventory.py --help
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/BUILD_ARTIFACT_RETENTION.md docs/RET1_RESTORATION_REVIEW_2026-10-18.md docs/RET2_CANDIDATE_REVIEW_2026-10-18.md docs/ret2_candidates_20261018.json spu_strategy/contract_ret2_candidate_review_2026-10-18.md spu_strategy/contract_ret1_2026-10-18.md
```

Validate every JSON candidate path is exact, unique, hash-pinned and still
PROTECT; verify no deletion approval or reclaimed-byte claim is present. Check
new documentation links and whitespace separately, including untracked files.

## Stop conditions

Stop on absent/conflicting scan markers or evidence corruption. Flag selected
files changed since scan; do not promote them. No archive transfer, compression,
deletion, new scan, or retention reclassification is authorized in this tranche.

## Completion record

Seven exact-path candidates remain PROTECT. All seven metadata identities
match the original scan. Historical source and routed-result hashes match
their evidence records; the integrated-context log pair is byte-identical.
Inventory fixtures (2 tests), CLI help, scoped whitespace and candidate/pin/link
validation passed. The documentation audit ran and reported the existing
tracked-document findings; new report links were checked separately.
Full dependency closure, archival copies and deletion decisions remain open.
