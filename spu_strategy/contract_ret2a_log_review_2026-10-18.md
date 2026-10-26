# RET-2A: log dependencies and storage sharing

Date: 2026-10-18. Status: COMPLETE (read-only review).
Roles: Codex author, implementer and auditor, in sequence.

## Scope and exact commands

```bash
cat build/spu_surd_register/backend_compatibility_20261012/integrated_context_preparation_04/worker.py
cat build/spu_surd_register/backend_compatibility_20261012/integrated_context_preparation_04/check_cpu.py
cat build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/capture.json
btrfs filesystem du --raw -s build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/tool.log build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/stderr.log
filefrag -v build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/tool.log build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/stderr.log
```

Review existing RET-1 graph inputs and direct candidate/preparation scripts;
retain exact read-only commands, stdout/stderr, inode/link metadata and hashes
under `build/repository_cleanup/ret2a_20261018_01/`. Do not broaden the inventory
or rerun experimental commands found in historical launch records.

Write `docs/RET2A_LOG_DEPENDENCY_REVIEW_2026-10-18.md` and
`docs/ret2a_dispositions_20261018.json`. Record dispositions for the pair first,
then the other five candidates, with exact evidence references and unresolved
archival/restoration requirements. Keep all original RET-2 entries PROTECT.
Link the new review from the retention policy. Preserve prior manifests.

## Constraints

Read-only review of existing artifacts. No archive creation/transfer, source
mutation, deduplication/reflink, deletion, snapshot changes, filesystem sync,
hardware jobs or research-campaign changes. A shared extent indication is not a
space-recovery promise. Independent storage copies and a two-path restore are
required before any future pruning proposal; no storage destination is selected.
Stop if an evidence identity changes, a required input is absent, or inspection
would require a mutating filesystem operation. Mark unavailable facts unknown.

## Verification

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/BUILD_ARTIFACT_RETENTION.md docs/RET2A_LOG_DEPENDENCY_REVIEW_2026-10-18.md docs/ret2a_dispositions_20261018.json spu_strategy/contract_ret2a_log_review_2026-10-18.md
```

Validate JSON path identities, evidence pins, unique seven-entry coverage,
PROTECT-only outcomes and no approvals. Check untracked documentation links and
whitespace explicitly. This tranche modifies documentation/review artifacts only.

## Completion record

Both log names are consumed by the retained validator. Three synthetic controls
passed. Distinct inodes and link counts 1 were confirmed; read-only Btrfs/FIEMAP
commands exited 0 with no sharing reported and encoded extents present.
All seven dispositions remain PROTECT. Direct audit/toolchain records refine
their preservation requirements. Flagged the earlier graph's absolute-prefix
extraction defect; no repair or graph regeneration was performed.
JSON/evidence-pin/link/whitespace validation passed. The documentation audit ran
with existing tracked-document findings. No source artifact, archive, extent
mapping, qualification record or research campaign was changed.
