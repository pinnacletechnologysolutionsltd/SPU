# Build artifact retention policy

Preserve discoveries and reproducibility, not every temporary file created
while making them. `build/` is a working area, but existing contents remain
protected until individually reviewed. This policy authorizes no deletion.

See the [RET-1 restoration and dependency review](RET1_RESTORATION_REVIEW_2026-10-18.md)
for the qualified verifier scope, focused rehearsal and completed Surd scan.
The [RET-2 candidate review](RET2_CANDIDATE_REVIEW_2026-10-18.md) provides an
initial exact-path manifest; every candidate remains protected.
The [RET-2A log review](RET2A_LOG_DEPENDENCY_REVIEW_2026-10-18.md) confirms both
duplicate log pathnames are consumed by retained checks and flags an absolute-
path extraction defect in the preliminary dependency graph.
The [RET-2B correctness tranche](RET2B_GRAPH_CORRECTNESS_2026-10-18.md) repairs
that extraction and qualifies known-reference regressions before regeneration.
The [RET-2C reassessment](RET2C_REASSESSMENT_2026-10-18.md) records the completed
regeneration, corrected candidate references and unchanged PROTECT decisions.
The [RET-3 draft contract](../spu_strategy/contract_ret3_focused_archive_2026-10-18.md)
defines the proposed focused package. Archival writes remain unauthorized until
the exact closure, stopped-source boundary and two independent destinations
are confirmed.

| Class | Retain | Disposition |
|---|---|---|
| A — Qualified evidence | Qualification manifests, exact sources, commands, hashes, reference outputs and limitations | Preserve compact evidence permanently |
| B — Hardware milestones | Known-good bitstreams, constraints, timing and route reports, scene packets, tool/chipdb identities | Preserve milestone packages |
| C — Diagnostic evidence | Failure summaries, source identities, selected telemetry and diagnostic samples | Select samples after diagnostic review; retain unresolved comparison inputs |
| D — Disposable intermediates | Reproducible objects, caches, redundant frames and reconstructed build trees | Eligible only after dependency review, restoration verification and explicit owner approval |

Classify individual artifacts, not whole campaigns. A failed route may contain
unique class C data; a passing build may contain the only exact source overlay.
Age, size, filename, a passing test, and equal name/size pairs establish neither
redundancy nor permission to prune. Unknown dependencies remain protected.

## Inventory and review

Run from the repository root. Choose a fresh output suffix on subsequent runs:

```bash
df -h .
du -h --max-depth=2 build | sort -h | tail -40
find build -type f -printf '%s %p\n' | sort -nr | head -40
python3 tools/build_artifact_inventory.py --root build --out build/repository_cleanup/retention_inventory_20261018_01
git worktree list --porcelain
```

The existing inventory includes hidden paths, sizes, terminal marker counts,
worktree candidates and repeated-name/size candidates without following
symlinks. It writes only a new report. It does not read manifests, resolve
dependencies, prove quiescence, or calculate reclaimable space. Complete those
steps during review; do not treat its totals as a deletion manifest.

Interpret a detached job only with exactly one terminal marker: `COMPLETE`,
`FAILED`, or `TIMEOUT`. Missing or conflicting markers protect the run pending
investigation. `COMPLETE` records command exit zero, not qualification.
Terminal markers alone do not prove that no process still uses the directory.
Protect active, incomplete, unqualified and unresolved campaigns, registered
worktrees, and source snapshots until their owner resolves their disposition.

## Evidence graduation and archive index

Use a separately provisioned archive with `releases/`, `evidence/symbolic/`,
`evidence/gpu/`, `evidence/simulator/`, `evidence/fpga/`, and `diagnostics/`.
The archive location is not yet selected. A sibling directory on the same
filesystem saves no space by moving data alone. Verify storage identity and
available capacity before transfer; record independently recoverable copies.

For each milestone, keep a compact repository index entry recording:

- Milestone ID, class, qualification status and exact scope, source commit(s),
  dirty source overlay identity, evidence paths and dependency relationships.
- Archive location(s), package SHA-256, member manifest, scripts and exact
  reproduction commands, tool versions and necessary external dependencies.
- Independent restoration report, verification date, copy/failure-domain
  identities, review decision and explicitly approved redundant paths.

Freeze sources at an owner-controlled quiescent or snapshot boundary. Preserve
index/worktree differences, required untracked/ignored files, detached commits
and any Git objects needed for recovery. A commit hash alone cannot reproduce
a dirty experiment. Include licenses and referenced inputs, not just their hashes.

Create a compact package and SHA-256 manifest; independently restore it without
access to the original source and check member paths/types, contents, modes,
links and required Git state. Execute its declared reproduction checks. Keep
two independently recoverable verified copies for valuable qualifications
before pruning originals. A checksum check alone does not qualify restoration.

The [restoration review](BUILD_ARCHIVE_RESTORATION_REVIEW_2026-10-07.md)
identified verifier defects and holds production pruning. Resolve its applicable
negative controls and acceptance requirements before relying on that verifier.
No archive restoration has been newly qualified by this policy.

## Current campaign dispositions

| Campaign | Initial disposition |
|---|---|
| SG-0 focused software qualification | Class A: [local source/evidence package](../research/sg0_baseline_20261018/README.md) and RET-1 member restoration verified; two restored 31-file bundle manifests match; runtime replay/external independent copies pending; all originals protected |
| SSM-0/1/2 | Preserve source/evidence baselines; review redundant builds separately |
| SSM-3 | Qualified bounded software; preserve [Class A package/index and scoped restored replay](../research/ssm3_baseline_20261018/README.md); external archive and independent storage copies pending; no pruning approved |
| GPU W1-A/B/C | Preserve pinned scenes, packet hashes, source overlays and qualification summaries |
| SIM-G1 | Preserve source archives, overlay, manifests, historical comparison, commands and reference outputs; review reconstructed trees only after independent restoration |
| CPU routing timeouts | Protect unique telemetry, source manifests and audit summaries; select diagnostic samples before considering large-log removal |
| Router-F1 | Protect fixture/comparison inputs until controlled comparisons close |
| FPGA milestones | Preserve known-good bitstreams, constraints, route/timing reports and identity manifests |

These are retention instructions, not fresh qualification claims. SIM-G1's
recorded PASS covers three frozen T1d packet comparisons, not FPGA qualification.
Silicon claims must cite the [hardware evidence ledger](hardware_evidence.md).

## Approval boundary

Prepare an exact-path proposal with measured allocated/apparent bytes, proposed
class, reason, evidence dependencies, preserved replacements and their verified
hashes, restoration result and blockers. Separate protected evidence from
proposed removals even when they share a directory. Reject overlapping removal
paths and recheck identity and quiescence immediately before any approved action.

The owner must explicitly approve that concrete manifest before deletion.
Approval applies only to its frozen paths and identities. Neither this policy
nor an inventory authorizes automatic pruning. Record the final disposition in
the index and preserve the approval and execution receipt permanently.
