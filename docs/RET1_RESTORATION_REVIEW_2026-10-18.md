# RET-1: restoration and dependency review

Status: focused restoration rehearsal passed; Surd allocation/dependency scan
completed. No production deletion is approved. Artifact-level follow-up is in
the [RET-2 candidate review](RET2_CANDIDATE_REVIEW_2026-10-18.md).

## Verifier qualification

The repository-owned [verifier](../tools/verify_restore.py) replaces the legacy
text-manifest acceptance path for new RET-1 packages. The external helper and
historical review evidence remain unchanged. The old production-pruning hold
is not lifted by these focused results.

The new JSON manifest pins exact file hashes, types, modes, empty directories,
link targets and Git state. The verifier requires a separately pinned manifest
digest, reconciles the entire member set and never repairs a tree to pass.
Archive restoration also requires the separately pinned archive digest, rejects
duplicate/traversing/unsupported members and extracts without traversing links.

Supported packages contain regular files, directories and relative internal
symlinks. Self-contained Git administration is retained in full, including
detached commits and staged-only objects; Git HEAD, NUL-delimited status and
index parity are checked. Relative internal Git pointers are supported.
External Git administration, config includes, object alternates, absolute links
and absolute Git pointers/backlinks require separate migration and are rejected.
Legacy text manifests and unsupported special files are rejected. There is no
link-relocation or bundle-generation acceptance claim in RET-1.

Qualification controls cover valid independent restores, file corruption and
same-size substitution, missing/extra files/directories/links, changed types,
modes and link targets, traversal, duplicate members/JSON keys, package tampering,
output refusal, dirty index/worktree differences, clean-to-dirty changes,
untracked/ignored files, detached HEAD, staged-only objects, broken/relative/
external Git pointers and external configuration/alternate dependencies.

Results and exact tooling SHA-256 identities are retained in
[`verifier_qualification/results.json`](../build/repository_cleanup/ret1_20261018_01/verifier_qualification/results.json).
The retained test logs distinguish successful controls from rejected damaged
inputs. This tooling requires stopped sources or a snapshot for production
freezes; repeated scans do not establish quiescence. Restore destinations must
be private fresh directories. No concurrent adversarial-writer claim is made.

## Representative restoration rehearsal

The [historical focused Lorentz experiment](SURD_LORENTZ_RESEARCH_MILESTONE_2026-10-11.md)
retains exact sources, positive/poisoned instruction streams and prior results.
All 30 historical input hashes and the selected evidence archive hashes matched.
The rehearsal copied those inputs into a fresh self-contained staging tree,
packaged it, moved staging out of its expected location and restored separately.
It then compiled using only restored input paths and replayed the frozen streams.

Result: **853 instruction retirements; positive replay passed; poisoned
expectation failed with the expected atomic-tuple mismatch.** All 24 compiled
source identities matched the historical compiled-source list under the restore
root. The restored tree still matched its manifest after execution.

Evidence: [rehearsal result](../build/repository_cleanup/ret1_20261018_01/rehearsal/rehearsal_result.json),
[exact commands](../build/repository_cleanup/ret1_20261018_01/rehearsal/replay/commands.json),
and [package digests](../build/repository_cleanup/ret1_20261018_01/rehearsal/package/SHA256.json).

| Artifact | SHA-256 |
|---|---|
| Manifest | `7cc740ec68311fe83672d669fa94253e10cbf9308c3b378a2d3601ff513399ea` |
| Payload tar | `641476de4746bdeb8aac7197efe8695190c1fe31016dd3b74be9231d9baf913d` |

Verify the retained restored tree from the repository root:

```bash
python3 tools/verify_restore.py --root build/repository_cleanup/ret1_20261018_01/rehearsal/restored --manifest build/repository_cleanup/ret1_20261018_01/rehearsal/package/manifest.json --manifest-sha256 7cc740ec68311fe83672d669fa94253e10cbf9308c3b378a2d3601ff513399ea
```

This is a frozen-stream replay of focused dispatch-port RTL simulation. The
oracle generator was not rerun. No full CPU qualification, FPGA timing, physical
model or silicon result is established. Independence is checked through command
paths and compiled-source identities; no OS sandbox isolation is claimed.
The package remains on the same filesystem with zero independently recoverable
storage copies. It does not qualify pruning of the original campaign.

## Surd dependency and allocation review

Executed once through the detached runner, preserving outputs and terminal status:

```bash
tools/run_detached_job.sh --output build/repository_cleanup/ret1_20261018_01/scan_job --timeout 900 --notify-desktop -- python3 tools/audit_build_storage.py --out build/repository_cleanup/ret1_20261018_01/surd_review
```

The next invocation found exactly one terminal marker, `COMPLETE`, and checked
the [terminal result](../build/repository_cleanup/ret1_20261018_01/scan_job/result.json):
exit 0, duration 79 seconds within the 900-second limit, unit
`spu-scan_job-20261017T194554Z-1081228`. No scan was relaunched.

The [retention manifest](../build/repository_cleanup/ret1_20261018_01/surd_review/retention_manifest.json)
records 119,907 regular files, 39,812,318,953 apparent bytes (37.08 GiB), and
40,095,461,376 allocated bytes across unique regular-file inodes (37.34 GiB).
No hardlinked regular-file inodes were observed within this scope. All 475
review entries remain `PROTECT`; no entry is eligible for approval.

The [dependency graph](../build/repository_cleanup/ret1_20261018_01/surd_review/dependency_graph.json)
contains 413,352 explicit text-reference edges from 38,643 inspected inputs,
with 602 skipped inputs. It is an incomplete reference graph, not a verified
qualification dependency closure.

The scanner records exact metadata paths, inode/link identities, apparent bytes
and unique-inode allocated blocks. It retains explicit text-reference graph
edges and the hashes of inspected inputs; oversized/nontext/skipped inputs and
unresolved references remain visible. Scan scope includes bounded text in Surd,
docs, research, strategy and tools. Relative-only and dynamically constructed
dependencies require manual review. Neither a missing edge nor a terminal
marker proves a path disposable. All current entries receive `PROTECT`.

The retention manifest declares three possible outcomes: `PROTECT`,
`ARCHIVE_THEN_REVIEW`, and `ELIGIBLE_FOR_APPROVAL`. Moving between outcomes
requires artifact-level dependency review, a stopped-source boundary, verified
retained replacements and owner disposition. No current entry is eligible.

This filesystem is Btrfs. Hardlink-aware `st_blocks` totals are allocation
measurements, not a reclaimable-space promise. The scan separately records
`btrfs filesystem du --raw -s` output (or its explicit failure) for extent
sharing analysis. Snapshots, reflinks, links outside scope, open writers and
dependency uncertainty prevent converting aggregate sizes into guaranteed
space recovery. The verified reclamation estimate remains **unknown**; approved
reclamation is **zero**.

Remaining work after the initial RET-2 sample: inspect graph roots at qualified results,
resolve required source/route/toolchain dependencies, select diagnostic samples,
then propose exact-path archive/removal splits. Toolchain installations require
their own review. Preserve SIM-G1, SSM, hardware evidence and all source overlays.
