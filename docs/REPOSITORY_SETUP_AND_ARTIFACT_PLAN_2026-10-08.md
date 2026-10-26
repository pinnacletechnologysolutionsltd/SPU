# Repository setup and artifact plan

Date: 2026-10-08. Recommendation and read-only findings; no pruning, relocation,
release upload, merge or hardware campaign is authorized by this document.

## Findings

`git ls-files '*.bit' '*.fs' '*.fasm' '*.pnr.json'` returns no tracked FPGA
images or routing artifacts. Tracked `.bin` files include program images,
boot data and GPU packet fixtures; they are not a complete FPGA release.
`build/` is ignored. Existing build evidence must be retained independently.

The checked Wukong `.bit` files are binary Xilinx programming files. The sampled
`build/tang_primer_25k_spu4_som_edge_probe.fs` is ASCII programming data. A
different extension is not automatically required for flashing; preserve the
loader-compatible artifact and qualify any requested conversion separately.
`build/tang_primer_25k_spu4_probe.fs`, an older documented path, is absent.
This sample is not a complete audit of all historical programming files.

| Retained image | SHA-256 | Role |
| --- | --- | --- |
| `build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit` | `e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5` | Preserve rollback; physical scope is ledger §3.37 |
| `build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit` | `ec600abe73e847f0846bff5429813cc6913a343b235e215cab5298ebb5d126dd` | Diagnostic replay; H1 remains HOLD, ledger §3.38 |

Both hashes were checked against the [hardware evidence ledger](hardware_evidence.md).
Neither filename dates nor modification times select a qualified default image.
There is no completed integrated Surd CPU image established by the retained
[campaign closeout](../build/spu_surd_register/main_cpu_integration_20261007/campaign_closeout_01.json):
fit is unresolved, the last attempt timed out, and routed timing is unmeasured.

`git worktree list --porcelain` identifies numerous registered `stage_b_*`
directories as well as maintenance and gate checkouts. Their names do not imply
standalone snapshots. Four missing `/tmp` worktree entries are marked prunable;
no administrative pruning was performed.

## Recommended sequence

1. Finish review and PR handling for the frozen 23-file newcomer proposal.
   Its anonymous HTTPS checkout passed all 26 commands, including Icarus S2,
   at commit `2a1fcda43070df975d0a6f8dfa1b59cdc99247c5`. The
   [review](../build/newcomer_publication_20261008/remote_walkthrough_01/review_01.json)
   verifies 46 source hashes, 28 output hashes and clean Git state. Default-branch
   publication remains pending. Use the [quickstart](NEWCOMER_SOFTWARE_QUICKSTART.md)
   with isolated Python; distinguish runtime dependencies from optional RTL tools.
2. Keep the dirty engineering checkout intact. Make future reviewable source
   changes in dedicated clean checkouts or registered worktrees. Split CPU tests,
   arithmetic implementation, paper documentation and archive tooling into
   separately reviewed changes. Do not stage the entire working tree.
3. Prepare a small versioned artifact catalogue in Git. For each image record
   board/device, role, file format, byte length, SHA-256, source identity,
   toolchain/constraint identity, evidence classification, recovery image and
   durable download location. Record unavailable provenance explicitly. Resolve
   broken historical paths without replacing old evidence with a newer build.
4. Prepare immutable release packages outside the source history. Include the
   programming image, FASM, synthesized/routed netlists, constraints, tool and
   chipdb identities, reports, logs, evidence waveforms and reproducible commands.
   Bind dirty-source builds to retained source snapshots, patches and untracked
   inputs; a commit hash alone is insufficient. Keep reusable toolchain/chipdb
   dependencies in separately identified durable storage. Verify downloaded bytes
   and instructions before treating a package as a recovery path. Publication
   itself remains an owner decision.
5. Only after broader restoration qualification and durable replication should
   owner-authorized cleanup remove anything. The
   [restoration review](BUILD_ARCHIVE_RESTORATION_REVIEW_2026-10-07.md)
   records unresolved acceptance-gate defects. Restore files, empty directories,
   links, Git administration and exact dirty state before considering deletion.
   Registered worktrees require Git-aware removal. Production pruning remains held.

Archive tooling, research evidence, hardware qualification and newcomer software
publication have separate gates. Passing one does not authorize the others.
Evidence waveform exclusions must be individually justified; no blanket VCD rule.

## Read-only checks performed

```bash
git worktree list --porcelain
git ls-files '*.bit' '*.fs' '*.fasm' '*.pnr.json' '*.bin'
file build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit build/tang_primer_25k_spu4_som_edge_probe.fs
sha256sum build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
```

No cleanup command was executed. Heavy synthesis remains sequential and requires
a new authorized campaign budget. T1I stays offline; H1 HOLD and T1G rollback persist.
