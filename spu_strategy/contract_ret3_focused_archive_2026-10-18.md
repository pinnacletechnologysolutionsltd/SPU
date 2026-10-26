# RET-3: independently recoverable integrated-context clock evidence

Date: 2026-10-18. Status: DRAFT — archival writes NOT AUTHORIZED.
Roles: owner confirms scope/storage/freeze; Codex authors and implements;
auditor verifies independent copies. Perform roles sequentially.

## 0. Review-only commands authorized now

```bash
python3 -m json.tool docs/ret3_members_proposed_20261018.json > /dev/null
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/BUILD_ARTIFACT_RETENTION.md docs/ret3_members_proposed_20261018.json docs/ret3_review spu_strategy/contract_ret3_focused_archive_2026-10-18.md
```

Read [the proposed exact member list](../docs/ret3_members_proposed_20261018.json).
Review the [31-member closure packet](../docs/ret3_review/README.md), including
the three authored replay files, storage observations and recovery checklist.
Draft/source-file preparation is authorized; staging source artifacts or running
the adapter, packaging or restoring remains prohibited. Syntax/structure checks
only have been performed on the new replay code.
Preserve all original campaigns and seven PROTECT dispositions. Execute no
package, transfer, restore, compression, deduplication or deletion operation
under this draft. Treat observed proposal hashes as review data, not a freeze.

## 1. Required owner decisions before archival writes

Record each decision in a revised, explicitly authorized contract:

| Decision | Required value | Current state |
|---|---|---|
| Exact dependency closure | Approved member-list SHA-256 and focused replay scope | Proposed; unconfirmed |
| Primary destination | Exact mounted external disk path and physical device identity | Unselected |
| Secondary destination | Exact independent disk path or private remote destination | Unselected |
| Failure-domain independence | Development drive, primary and secondary physically/recoverably distinct | Unverified |
| Stopped-source boundary | Owner-controlled stopped writers or approved consistent snapshot; responsible owner and interval | Unconfirmed |
| Execution allocation | Frozen exact argv, output paths, per-phase/cumulative wall-clock limits and attempt count | Unallocated |

Verify device parentage, physical identities and mount identity before writing.
Reject two directories, partitions, subvolumes or snapshots on one physical disk
as independent copies. Reject an unmounted destination falling back to a local
directory. For remote storage, confirm private access, independent recovery of
credentials/keys and restore availability without the development machine.
Record storage identities without embedding secrets in manifests or logs.

## 2. Exact scope and dependency roles

Freeze the 28 source members listed in the proposal. Retain both original
repository-relative log names and empty stdout; capture/invocation/launch and
dirty-source identity records; selected candidate result/closeout records;
bindings and historical input identities; validator/tests and frozen XDC;
four repository restoration/verification modules.

Execute only `clock_application.validate(xdc, relocated_capture)` for the claim.
Its nonstandard runtime inputs are the validator source, XDC and three streams
declared by capture.json. Record Python version and required standard library
modules (`hashlib`, `re`, `decimal`, `pathlib`). Treat other included historical
scripts/catalogs as provenance only; do not import or execute the placement
worker/checker, or treat every path in its identity catalog as a replay input.
Label omitted external historical references as outside this focused scope.

Author and review three additional payload members before arming execution:
`RET3_REPLAY.py`, `relocation.json`, `REPRODUCE.md`. Record their hashes and exact
commands in the revised contract. Pin the expected validator return value to
the retained candidate's clock-application record, including 40 ns/sys_clk and
`timing_qualified=false`. Claim focused constraint-application replay only;
claim no full placement, route, timing signoff, bitstream or silicon result.

## 3. Freeze and reproducible payload gates — execute only after authorization

Establish the confirmed stopped-source boundary. Rehash every source member,
including both large logs and empty stdout. Compare with approved identities,
capture hashes, historical XDC/validator pins and closeout pins. Halt on mismatch;
do not regenerate historical records or substitute current source.

Copy the confirmed inputs into private fresh staging while retaining exact
member paths and required modes/types. Reject unsupported external links,
special files or Git dependencies. Freeze a sorted JSON tree manifest and pin
its SHA-256 separately. Create an uncompressed deterministic payload archive
with fixed member order and normalized archive header timestamps/owners while
preserving declared modes. Build twice from the same frozen staging and require
equal archive digests. Do not include runtime receipts in the frozen payload.

Keep a separate envelope containing payload-manifest/archive digests and
append-only qualification/copy receipts, each with its own digest. Retain the
trust-anchor digests in the repository index and both recovery locations.
Avoid circular hashes or modifying a qualified payload to add its own result.

## 4. Fresh restore and replay gates

Restore into a fresh private directory using the pinned archive and manifest.
Verify exact member sets, file bytes, types, modes and supported links with the
RET-1 verifier. Require both log names and stdout to reappear independently;
permit identical contents but never omit either pathname.

Preserve historical absolute paths in capture, invocation and closeout records.
Use an explicit allowlisted old-path-to-restored-path map. Produce a separate
derived capture object in memory, changing only stream paths; preserve lengths,
hashes and all other fields. Resolve each target inside the restore root and
reject missing, escaping, unexpected or substituted mappings. Execute the
retained validator on restored XDC/streams with original locations unavailable.
Verify its return value against the pinned historical clock-application record.

Require positive replay plus negative controls for either missing log, altered
same-size log bytes, wrong XDC, and escaping/substituted relocation. Run controls
on private fixtures only. Reverify the restored tree after replay. Record exact
commands, tool identities, exit codes, outputs, isolation method and claim limits.

## 5. Two independently recoverable copies

Transfer the identical pinned payload/envelope to each designated destination.
Read back and hash each copy independently. Restore separately from each copy,
with the other copy, local staging and original evidence unavailable. Run the
same tree verification and focused replay from each restored copy. Recover any
necessary remote credentials/keys through the designated independent route.
Record the source medium/location, package pins and positive/negative results.
Require an independent recovery host/boot environment; record how the original
development disk and both other data sources were unavailable. Do not claim
disk-independent recovery from path checks on the running development machine.
Do not equate transfer success, two pathnames or two same-drive copies with
independent recovery. Retain failed controls and keep all artifacts protected.

## 6. Completion and stop conditions

Record two verified recovery copies and the qualified focused workflow in a
compact repository index. Document the exact reusable procedure and stop active
storage-infrastructure development after this milestone; apply it selectively
to later campaigns. Do not launch a new broad inventory or hardware campaign.

Keep originals unchanged even after PASS. Advance only separately reviewed
artifacts to ARCHIVE_THEN_REVIEW after all gates; never infer deletion or extent
deduplication approval. Keep other five candidates PROTECT. Retain unknown
reclaimable-space estimates. Halt on unconfirmed destinations/closure/freeze,
mount identity change, source/hash drift, unsafe relocation, failed replay,
copy dependence or exhausted execution allocation. Require renewed owner
authorization before any retry or scope expansion. Use root detached-job rules
for authorized work expected to exceed 60 seconds; end the turn after LAUNCHED.

## 7. Review preparation status

The complete proposed closure contains the original 28 sources plus the adapter,
relocation map and recipe. Their SHA-256s are in the separate review sidecar;
changing any reviewed source requires a new closure pin and owner review.
Proposed sidecar SHA-256:
`1e962d84f3b4b8bb66ab7a34d68bcef5347746c4da2d2aa84d78b8f27069192c`.
This is a proposed review identity, not owner confirmation of closure or execution.
The draft sidecar sets `execution_authorized=false`; the adapter enforces it.
This does not establish runtime correctness or authorize any future operation.

The observed development drive is sdb. A separate unmounted sda contains existing
EFI/NTFS partitions; no ownership, capacity-for-use or destination approval is
established. No eligible mounted external archive or private remote destination
was designated. Both destination decisions remain open.

The stopped-source plan remains proposed: identify responsible owners and stop
writers to all approved sources for a recorded interval before freeze/copy.
No declaration of quiescence, snapshot creation or archival execution occurred.
Use the packet's per-copy independence checklist in the later execution record;
leave every unchecked item NOT RUN. All seven current artifacts remain PROTECT.
