# RET-2C: reassessment with the corrected dependency graph

**All seven artifacts remain PROTECT.** The corrected graph confirms additional
references; it does not establish a disposable artifact in this sample.
No archive, compression, extent operation, deletion or new scan was performed.

The [reassessment index](ret2c_reassessment_20261018.json) pins the corrected
graph, terminal result, original candidate manifest and reviewed evidence.
Full exact incoming edges are retained in
[`candidate_edges.json`](../build/repository_cleanup/ret2c_20261018_01/candidate_edges.json).

## Provenance and source drift

RET-2B completed with exactly one COMPLETE marker, exit 0, after 96 seconds
within its 900-second cap. The prior graph and all four graph-tool hashes match
the regeneration provenance. The graph covers the same 39,245 requested input
paths: 38,643 inspected and 602 skipped. It has 395,382 explicit-reference edges.

The five inputs changed between RET-1 and RET-2B were:

- `docs/BUILD_ARTIFACT_RETENTION.md`
- `docs/README.md`
- `docs/RET1_RESTORATION_REVIEW_2026-10-18.md`
- `spu_strategy/contract_ret1_2026-10-18.md`
- `tools/retention_dependencies.py`

The other 38,638 inspected inputs retained their hashes. The five changes are
documentation and scanner content, not changes to the seven selected campaign
artifacts. No authorship or cause is inferred from those hash differences.
The skipped inputs comprise 550 symlink/size-limit exclusions and 52 non-UTF-8
files; they are not 602 newly missing dependencies.

All seven selected artifacts retain their RET-2 inode, device, link count, size,
allocation and modification/change-time identities. Their previously verified
content hashes are carried forward; this tranche does not rehash all large
artifacts. All **55 distinct source files** providing exact incoming edges were
rehashed and still match their corrected-graph identities. Results are in
[`incoming_source_checks.json`](../build/repository_cleanup/ret2c_20261018_01/incoming_source_checks.json).

## Artifact decisions

Counts below are exact-path text references, excluding ancestor-directory
mentions. They are reference counts, not counts of independent qualifications.

| ID | Artifact | Old → corrected references | Disposition and evidence |
|---|---|---:|---|
| RET2-01 | Frozen decoder `spu13_core.v` | 1 → 33 | PROTECT; Lorentz source identity and other campaign records require complete source/overlay preservation |
| RET2-02 | Packet 06 `cpu.routed.json` | 12 → 14 | PROTECT; launch and audit records consume the route, whose hash is pinned by the all-net audit |
| RET2-03 | Packet 06 `native_route_raw.json` | 15 → 16 | PROTECT; hash-pinned native input to the independent route audit |
| RET2-04 | Diagnostic-02 `stderr.log` | 0 → 0 | PROTECT; direct timeout diagnosis requires raw endpoint records despite no exact incoming edge |
| RET2-05 | Integrated-context `tool.log` | 0 → 5 | PROTECT; capture, invocation, bindings, closeout and timing-estimate review reference this pathname |
| RET2-06 | Integrated-context `stderr.log` | 0 → 2 | PROTECT; capture and closeout pin this pathname independently |
| RET2-07 | OSS CAD Suite `.tgz` | 2 → 2 | PROTECT; separate toolchain comparison pins its identity and preserves the failed stock Artix-7 compatibility result |

The newly recovered
[closeout manifest](../build/spu_surd_register/backend_compatibility_20261012/integrated_context_closeout_01/candidate_capture_manifest.json)
pins both log paths and the identical SHA-256 already established in RET-2A.
The [prior-estimate flags](../build/spu_surd_register/backend_compatibility_20261012/timing_coverage_preparation_01/prior_estimate_flags.json)
also reference `tool.log` and mark its frequency estimate unqualified. Preserve
this interpretation with the raw evidence; do not promote it to timing signoff.

The [RET-2A validator controls](RET2A_LOG_DEPENDENCY_REVIEW_2026-10-18.md)
establish the actual two-path read dependency beyond the textual references.
Packet 06 remains route-integrity PASS with timing HOLD, as recorded in the
[hardware evidence ledger](hardware_evidence.md). No qualification was rerun.

## Remaining boundary and RET-3 prerequisites

No entry advances to ARCHIVE_THEN_REVIEW or ELIGIBLE_FOR_APPROVAL. The graph
still omits source-local/dynamic dependencies, large/binary contents and newly
created inputs outside its fixed scope. Exact paths absent from it are not
proven unreferenced. No complete dependency closure or quiescent freeze is
established by this reassessment.

For a small RET-3 first package, preserve both integrated-context log names,
empty stdout, capture/invocation/closeout records, the clock-evidence validator,
its frozen XDC and an explicit relocated replay recipe. Distinguish a focused
clock-evidence replay from the full placement check, which also needs topology,
region and carry inputs. Preserve original absolute-path records and provide
separate relocation metadata; do not rewrite historical evidence to pass.

Before creating that package, establish the archive destination and independent
recovery locations, define the exact retained dependency set, and freeze sources
at an owner-controlled boundary. Restore both names from the retained package,
verify their hashes and replay the declared checks. Important hardware evidence
requires two independently recoverable copies before any original is expendable.
Storage location, package creation and independent recovery remain outstanding.

All seven existing classifications and prior manifests are unchanged. Approved
reclamation is zero; verified reclaimable space is unknown. Deduplication still
requires its own explicit authorization and recovery plan. SIM-G2A, SG-0, SSM-4
and other research/hardware work were not modified.

Validation: [receipt](../build/repository_cleanup/ret2c_20261018_01/validation.json)
pins the reassessment and review evidence. Exact seven-path coverage, source
checks, direct-evidence pins, unchanged prior manifest, links and whitespace
passed. The tracked-document audit ran with existing findings; new links were
checked separately.
