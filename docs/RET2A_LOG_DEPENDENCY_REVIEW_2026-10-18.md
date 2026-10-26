# RET-2A: both identical log paths are required evidence

**Disposition: retain both log paths; all seven RET-2 artifacts remain PROTECT.**
The pair has identical bytes but distinct inode identities. Direct inspection
confirms that the retained replay checker consumes both paths. No archive,
deduplication, deletion or research campaign was performed in this tranche.

The [seven-entry disposition record](ret2a_dispositions_20261018.json) pins the
original RET-2 manifest, records unchanged metadata identities, and adds findings
without changing any prior classification or qualification record.

## Pathname dependency review

Both files are under
`build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/`:

| Artifact | Inode | Link count | Apparent bytes | Allocated bytes (`st_blocks * 512`) |
|---|---:|---:|---:|---:|
| `tool.log` (RET2-05) | 6197633 | 1 | 204,910,029 | 204,910,592 |
| `stderr.log` (RET2-06) | 6197629 | 1 | 204,910,029 | 204,910,592 |

Both are on device 49 and retain SHA-256
`3e5d464734fd56dc21da1919d3e1597ac4b1cce592df2a2712d305a1c1d34a3d`.
Hashes were rechecked; all seven candidates' inode/size/time identities still
match RET-2. The log pair consists of separate regular files, not hardlinks.

Confirmed dependencies:

- [Invocation](../build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/invocation.json)
  and preparation bindings direct nextpnr's `--log` to `tool.log`.
- [Worker](../build/spu_surd_register/backend_compatibility_20261012/integrated_context_preparation_04/worker.py)
  captures stderr separately, hashes both paths and requires the stdout, stderr
  and tool-log stream records before recording its diagnostic pass.
- [Capture manifest](../build/spu_surd_register/backend_compatibility_20261012/integrated_context_candidate_01/capture.json)
  declares both absolute pathnames, lengths and hashes separately.
- [Post-check](../build/spu_surd_register/backend_compatibility_20261012/integrated_context_preparation_04/check_cpu.py)
  calls the [clock-evidence validator](../build/spu_surd_register/backend_compatibility_20261012/preparation_05/clock_application.py).
  That validator reads every declared stream, verifies its length/hash, checks
  the clock-application event in `tool_log`, and compares the event with stderr.

Three isolated synthetic controls exercised that exact retained validator:
three-stream positive PASS; missing stderr rejected; missing tool-log rejected.
Only private temporary fixtures were changed. The historical placement or
clock qualification was not rerun or extended. The tests demonstrate that
removing either pathname breaks this validator even when their bytes match.

Direct reference search command/output and inspected-source hash identities are
retained in [RET-2A evidence](../build/repository_cleanup/ret2a_20261018_01/direct_reference_command.json)
and the disposition JSON. This is a confirmed dependency chain, not proof that
every consumer throughout the repository has been found.

## Storage sharing

Read-only `btrfs filesystem du --raw -s` reports, for each log:
`Total=204910592`, `Exclusive=204910592`, `Set shared=0` bytes.
`filefrag -v` reports no `shared` flags across the two files and reports 3,144
`encoded` extent records. The mount uses Btrfs with `compress=zstd:3`.

These observations show no sharing reported by those interfaces at inspection
time. Their extent lengths are not a measurement of independently recoverable
physical bytes on compressed storage. Snapshot references, allocation metadata,
writers and compression remain relevant. Do not add encoded FIEMAP physical
ranges or infer 195.4 MiB of release from the logical duplicate.

Exact commands, stdout/stderr and exit codes are retained in
[commands.json](../build/repository_cleanup/ret2a_20261018_01/commands.json).
No FIEMAP sync flag, dedupe ioctl, reflink, snapshot change or filesystem write
was requested against the source files. Confirmed reclaimable space: **unknown**.

## Dependency-graph defect: flag before further reliance

The existing graph extracts valid absolute checkout paths as
`hardware/SPU/build/...` instead of `build/...`. In `capture.json`, all three
stream references were recorded as missing or patterned paths. This explains
the earlier lack of incoming edges for the exact log filenames.

[Defect evidence](../build/repository_cleanup/ret2a_20261018_01/graph_defect.json)
retains the three erroneous edges. Negative reference results are unreliable;
the graph cannot establish that an artifact is unreferenced. The minimal repair
is to normalize known repository-root absolute paths before extracting relative
references and add a regression fixture for this checkout layout. That repair
and graph regeneration were not performed in this read-only tranche. Direct
inspection supplied the dependencies above; no artifact was reclassified.

## Remaining five candidates

| ID | Documented disposition and next requirement |
|---|---|
| RET2-01 | PROTECT frozen Lorentz source; preserve full source/overlay closure, not just the sampled CPU file |
| RET2-02 | PROTECT routed JSON; the all-net audit explicitly pins its path/hash; retain input, route/audit and tool/chipdb closure |
| RET2-03 | PROTECT native capture; the same audit explicitly pins its path/hash, confirming it is source evidence |
| RET2-04 | PROTECT timeout stderr; diagnosis says endpoint extraction depends on router-debug records; no compact replacement is qualified |
| RET2-07 | PROTECT toolchain archive under separate review; its comparison report pins the archive and records lack of Xilinx support, so it cannot replace the patched Artix-7 backend |

The [all-net audit](../build/spu_surd_register/backend_compatibility_20261012/packet06_audit_reconciliation_01/packet06_all_net_audit_20261015.json)
directly lists both Packet 06 artifacts in `source_evidence`. Route integrity
remains PASS with timing HOLD as recorded in the [hardware ledger](hardware_evidence.md).
The [toolchain comparison](../build/spu_surd_register/oss_cad_suite_20261013_preparation_01/compatibility/run_01/comparison_report.json)
records stock-tool rejection before JSON import and no usable Artix-7 chipdb;
preserve this negative result and its distinction from the patched backend.

## Archival and future approval boundary

No log archive or two-path restoration rehearsal was created here, and no
independently recoverable copy exists for this proposed package. Those are open
requirements. A future package must retain both original logical pathnames,
their hashes, capture metadata, scripts, bindings, constraints and complete
reviewed dependencies. Independently restore both paths and verify content and
the declared replay checks using relocated paths, preserving original records.
Verify independently recoverable storage copies before treating originals as
expendable; important hardware evidence requires two recovery copies.

Extent deduplication is a separate future action requiring explicit authorization,
a stopped-source boundary, verified recovery copies and a recovery plan. No
permission for it is inferred from this review. Deletion would additionally
need an exact-path approval and must preserve required replay pathnames.
All seven entries remain **PROTECT**; no new broad scan was launched. SIM-G2A,
SSM, symbolic-to-GPU work and hardware evidence were not modified.

Validation: [receipt](../build/repository_cleanup/ret2a_20261018_01/validation.json)
pins the disposition manifest and review evidence. Seven PROTECT-only entries,
unchanged prior RET-2 manifest, inspected-source hashes, the three controls,
storage-command success, links and whitespace passed. The tracked-document
audit ran with existing findings; new documentation links were checked separately.
