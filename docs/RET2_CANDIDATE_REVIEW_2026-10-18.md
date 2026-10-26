# RET-2: seven protected artifact review candidates

The existing Surd scan completed successfully. This review selects seven exact
files for individual disposition analysis; it launches no scan, changes no
retention classifications and authorizes no deletion.

The compact repository index is
[`ret2_candidates_20261018.json`](ret2_candidates_20261018.json).
Each entry includes an exact path, SHA-256, scan-time identity comparison,
allocation measurements, referenced evidence and its hashes, archival
requirements and unresolved blockers. All seven entries remain **PROTECT**.

## Terminal evidence and storage measurements

Exactly one terminal marker, `COMPLETE`, was present for the original job.
The [result](../build/repository_cleanup/ret1_20261018_01/scan_job/result.json)
records exit 0 after 79 seconds within the existing 900-second limit.
The [RET-1 review](RET1_RESTORATION_REVIEW_2026-10-18.md) now records the scan
outcome and links its retained reports. No scan was repeated.

| Surd measurement | Recorded result |
|---|---:|
| Regular files | 119,907 |
| Apparent bytes by path | 39,812,318,953 (37.08 GiB) |
| Unique regular-inode allocated bytes | 40,095,461,376 (37.34 GiB) |
| Observed hardlinked regular-file inodes | 0 |
| Protected review entries | 475 |
| Explicit text-reference edges | 413,352 |
| Inspected / skipped text inputs | 38,643 / 602 |

The retained [Btrfs report](../build/repository_cleanup/ret1_20261018_01/surd_review/btrfs_allocation.json)
exited 0 and reported `Total=39849799680`, `Exclusive=25799180288`,
`Set shared=2289565696` bytes. These are filesystem-tool extent accounting
fields, not a per-candidate deletion estimate. No candidate-level exclusive
extent measurement, snapshot review or stopped-source boundary was established.
The graph remains incomplete and many edges describe history or commands rather
than required qualification inputs. Its omissions never establish disposability.

## Candidate findings

Sizes below are apparent MiB; exact apparent and allocated bytes are in the JSON.
Paths are fully spelled out there; IDs provide stable review references.

| ID | Artifact | MiB | Finding |
|---|---|---:|---|
| RET2-01 | Frozen decoder snapshot `spu13_core.v` | 0.12 | Matches the historical Lorentz source hash; preserve complete source closure and dirty overlays |
| RET2-02 | Packet 06 `cpu.routed.json` | 137.45 | Hash matches the ledger's independently audited route; timing remains on hold |
| RET2-03 | Packet 06 `native_route_raw.json` | 369.38 | Preserve alongside route and audits; consumer-field review is incomplete |
| RET2-04 | Diagnostic-02 `stderr.log` | 529.54 | Timeout diagnosis says endpoint extraction depends on raw router-debug records |
| RET2-05 | Integrated-context `tool.log` | 195.42 | Same bytes as RET2-06; review filename consumers before proposing redundancy removal |
| RET2-06 | Integrated-context `stderr.log` | 195.42 | Same bytes as RET2-05; neither pathname is approved for removal |
| RET2-07 | OSS CAD Suite distribution `.tgz` | 713.18 | Separate toolchain review; no inference of duplication from its filename |

All seven current inode/size/time identities match their RET-1 scan records.
The paired logs have SHA-256
`3e5d464734fd56dc21da1919d3e1597ac4b1cce592df2a2712d305a1c1d34a3d`,
each with 204,910,029 bytes. Equal content establishes byte redundancy; it does
not establish that either path can be removed, nor how much Btrfs space would
be released. No supersession claim is inferred from campaign names.

Packet 06's classification is **route-integrity PASS; timing qualification
HOLD**, as recorded in [hardware evidence §3.39](hardware_evidence.md).
Its command uses the integrated-context placed input and separately pinned
capture helpers, nextpnr executable and chip database. Those dependencies
remain protected. This is not a silicon or qualified-bitstream claim.

Diagnostic-02 exhausted its 3,600-second route budget. Its retained diagnosis
reports 220,067 routing-arc records and says mapped sink-wire extraction depends
on them. The static graph found no incoming reference for the sampled stderr
file; direct inspection nevertheless establishes its diagnostic importance.
The log cannot be replaced by its compact timeout summary without further review.

The integrated-context terminal command succeeded, but its diagnostic report
qualifies global placement checks only: routing, timing, accepted target trials
and matched private-state causality were not established. Keep those negative
results and limits with any archived log. A later route does not erase them.

## Archival prerequisites and next decisions

Keep all existing classifications unchanged. First complete dependency closure
for the source/route/capture evidence and resolve the two log filenames' readers.
Then propose a compact package containing the exact sources, tool identities,
constraints, diagnostics, acceptance records and executable restoration recipe.
Require a representative restore and the declared audits, plus independently
recoverable storage copies, before asking for a specific deletion approval.
The prior focused Lorentz rehearsal does not qualify these larger campaign
packages or establish off-device recovery.

The toolchain archive needs its own license, upstream identity, patched-build
provenance and chipdb review. No toolchain installation is an ordinary
experiment intermediate in this manifest.

Verified reclamation estimate: **unknown**. Approved reclamation: **zero**.
No entry is `ARCHIVE_THEN_REVIEW` or `ELIGIBLE_FOR_APPROVAL` yet. The seven
samples and their incomplete dependencies cannot authorize whole-directory
cleanup. SIM-G1, SSM and the hardware evidence ledger remain unchanged.

Preparation code and source-report hash identities are retained under
[`ret2_candidates_20261018_01/`](../build/repository_cleanup/ret2_candidates_20261018_01/prepare_candidates.py).
The JSON pins the preparation script and original scan reports for review.

Validation: inventory fixtures (2 tests) and CLI help passed. Candidate schema,
source-report/script pins, historical source/route identities, documentation
links and whitespace passed; the [validation receipt](../build/repository_cleanup/ret2_candidates_20261018_01/validation.json)
pins the candidate manifest. The tracked-document audit ran with existing
repository findings; new report links were checked separately.
