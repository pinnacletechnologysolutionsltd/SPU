# RET-2B: dependency path normalization

Date: 2026-10-18. Status: COMPLETE (normalization and graph regeneration).
Roles: Codex author, implementer and auditor in sequence.

## Pre-execution review and scope

```bash
cat tools/retention_dependencies.py
cat software/tests/test_retention_storage.py
cat build/repository_cleanup/ret2a_20261018_01/graph_defect.json
```

Repair only reference extraction; preserve original graph and classifications.
Recognize known-root absolute paths before matching relative prefixes. Consume
external absolute paths without extracting misleading internal suffixes. Support
repository-relative and `./` repository-relative forms at token boundaries.
Keep source-local/dynamic references explicitly outside inferred closure.

1. Add `tools/retention_paths.py` and focused tests in
   `software/tests/test_retention_paths.py`: actual checkout layout, absolute /
   relative / dot-relative forms, repo roots containing spaces, external and
   prefix-collision negatives, multiple references and traversal flagging.
2. Update `tools/retention_dependencies.py` to use normalization and accept an
   optional fixed input list. Preserve source SHA-256s and record changed-during-
   read or missing/escaping inputs as skipped, never as unreferenced evidence.
3. Add `tools/regenerate_retention_graph.py`. Regenerate only the original
   graph's inspected/skipped input set; do not run filesystem allocation or
   metadata inventories. Pin original graph, new tooling and each new inspected
   source; record unchanged/changed/missing source identities against the prior
   graph. Separate edge changes on unchanged sources from source-content drift.
4. Qualify against the actual log `capture.json` before launching regeneration:
   recover exact stdout/stderr/tool paths, all resolving to existing files,
   and no `hardware/SPU/build` false references. Preserve fixture/test results.
5. Document execution and limits in `docs/RET2B_GRAPH_CORRECTNESS_2026-10-18.md`
   and link it from the retention policy. No seven-artifact reassessment yet.

## Verification before any regeneration budget

```bash
python3 software/tests/test_retention_paths.py
python3 software/tests/test_retention_storage.py
python3 software/tests/test_build_artifact_inventory.py
python3 tools/build_artifact_inventory.py --help
python3 tools/regenerate_retention_graph.py --help
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- tools/retention_paths.py tools/retention_dependencies.py tools/regenerate_retention_graph.py software/tests/test_retention_paths.py docs/BUILD_ARTIFACT_RETENTION.md docs/RET2B_GRAPH_CORRECTNESS_2026-10-18.md spu_strategy/contract_ret2b_graph_correctness_2026-10-18.md
```

Record preflight results under `build/repository_cleanup/ret2b_20261018_01/`.
After fixture and known-reference gates pass, execute:

```bash
tools/run_detached_job.sh --output build/repository_cleanup/ret2b_20261018_01/graph_job --timeout 900 --notify-desktop -- python3 tools/regenerate_retention_graph.py --prior-graph build/repository_cleanup/ret1_20261018_01/surd_review/dependency_graph.json --out build/repository_cleanup/ret2b_20261018_01/regenerated
```

Use the existing 900-second bound as a cap for this single graph-only
regeneration. After LAUNCHED record the unit and end the turn, per root §4.2.
Interpret only a unique terminal marker in a later invocation. Do not retry or
extend a timed-out run without authorization. A passing normalization test does
not establish full semantic dependency closure.

## Stop conditions

Stop before launch if fixtures or actual-capture checks fail. Refuse existing
output directories. Preserve prior input identities; report source drift rather
than pretending current content equals the old scan. Do not archive, compress,
deduplicate, delete, reclassify, touch research/hardware results or regenerate
allocation data. All seven candidates remain PROTECT.

## Completion record

Twelve focused tests and the actual three-stream reference gate passed before
launch. Regeneration completed with a unique COMPLETE marker, exit 0, 96 seconds
within the frozen 900-second cap. The later invocation checked terminal evidence.
Previous graph and tool pins were verified for RET-2C; source drift and skipped
inputs are retained separately. No classification, archival or cleanup change.
