# RET-2B: dependency-path correctness

Status: normalization regression gates and graph-only regeneration passed.
All seven retention candidates remain **PROTECT**. See the
[RET-2C reassessment](RET2C_REASSESSMENT_2026-10-18.md).

## Repair and tested behavior

The earlier extractor began matching inside absolute checkout paths at the
`hardware/` directory component. Consequently, valid references in
`capture.json` became missing `hardware/SPU/build/...` targets. RET-2B repairs
this behavior in [retention_paths.py](../tools/retention_paths.py) and uses it
from [retention_dependencies.py](../tools/retention_dependencies.py).

The extractor recognizes the known absolute repository prefix first and strips
that exact prefix to obtain a repository-relative target. It consumes external
absolute paths without extracting misleading internal suffixes. Repository-root
relative and `./` relative forms are recognized at token boundaries. Lexical
`..` components remain visible for the graph's unsafe/ambiguous classification.
Repository prefix collisions and embedded `notbuild/` tokens are not promoted
to local dependencies.

Eight new regression tests cover the actual `hardware/SPU` checkout layout,
absolute/relative/dot-relative forms, external paths, prefix collisions, roots
with spaces and regex characters, traversal, actual-capture-shaped JSON, skipped
inputs and source-identity drift during fixed-input regeneration. Existing
storage fixtures (2) and build-inventory fixtures (2) also pass: **12 tests**.

The fixed-input regeneration fixture retains an unchanged source with three
deliberately wrong old edges, changes another source and removes a third. It
checks that the old graph stays byte-identical, corrected edges are attributed
only to unchanged source content, and changed/missing source identities are
reported separately. Existing output directories are refused.

## Actual known-reference gate

Before launching regeneration, a focused pass read the existing
`integrated_context_candidate_01/capture.json`. It recovered exactly these
three repository-relative paths, all resolving to existing files:

```text
build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/stdout.log
build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/stderr.log
build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/tool.log
```

No `hardware/SPU/build/...` targets remained in that focused result. Evidence:
[known-reference result](../build/repository_cleanup/ret2b_20261018_01/actual_capture_gate.json)
and [preflight](../build/repository_cleanup/ret2b_20261018_01/preflight.json),
including exact tool/test and previous-graph SHA-256 identities.

The [RET-2A direct validator evidence](RET2A_LOG_DEPENDENCY_REVIEW_2026-10-18.md)
continues to establish the semantic dependency on both log paths. Extracting
their references correctly does not replace that evidence.

## Graph-only regeneration and provenance

The [regeneration command](../tools/regenerate_retention_graph.py) reuses the
union of the prior graph's inspected and skipped input paths. It discovers no
new files and runs no metadata, allocation or Btrfs inventory. Original reports
are preserved. Version 2 graph output retains per-input SHA-256 identities,
skipped-input reasons, pinned tooling and the hash of the prior graph.

Source content may have changed since RET-1. The regeneration records those
changes, newly inspected prior inputs and inputs no longer inspected in
`source_identity_changes.json`. Its edge comparison is restricted to sources
whose hashes are unchanged, separating extraction changes from content drift.
No historical source content is silently substituted or represented as frozen.
The actual-capture gate must also pass inside the regeneration before outputs
are written, and the prior graph/tool identities must remain unchanged during
execution.

Executed once after preflight success (historical command; do not relaunch):

```bash
tools/run_detached_job.sh --output build/repository_cleanup/ret2b_20261018_01/graph_job --timeout 900 --notify-desktop -- python3 tools/regenerate_retention_graph.py --prior-graph build/repository_cleanup/ret1_20261018_01/surd_review/dependency_graph.json --out build/repository_cleanup/ret2b_20261018_01/regenerated
```

The later invocation checked exactly one `COMPLETE` marker and the
[terminal result](../build/repository_cleanup/ret2b_20261018_01/graph_job/result.json):
exit 0 after 96 seconds within the 900-second cap. The unit was
`spu-graph_job-20261017T202902Z-1085990`. No regeneration was repeated.

The [regeneration result](../build/repository_cleanup/ret2b_20261018_01/regenerated/regeneration_result.json)
records 38,638 unchanged inspected sources and five changed-content sources.
The 602 skipped inputs remain inspection exclusions, not newly missing files:
550 symlink/size-limit exclusions and 52 non-UTF-8 inputs. The actual capture
source was unchanged and its three-reference gate passed inside regeneration.
The corrected graph has 395,382 edges; no classification changes were made.

## Limits and disposition

The graph remains a conservative explicit-reference aid, not a complete
qualification dependency closure. Source-local names such as `stderr.log`,
dynamically constructed paths, whitespace inside artifact names and external
absolute dependencies still require direct review. Missing or skipped inputs
cannot establish disposability. Live source observations are hash-pinned but
do not establish a quiescent snapshot or independent recovery copy.

RET-2C reviews the regenerated graph's terminal result and source drift.
No archival, compression, deduplication,
deletion, retention reclassification, research campaign or hardware evidence
change accompanies this tranche. Confirmed reclaimable space remains unknown.
