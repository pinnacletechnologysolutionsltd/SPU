# Retained GPU artifacts: local provenance review

Date: 2026-10-14. Selected inventory; no rebuild, programming or publication.

```bash
python3 -m json.tool docs/gpu_retained_artifacts_2026-10-14.json
git -C build/t1f_clean_qualification_20260922 rev-parse HEAD
git -C build/t1f_clean_qualification_20260922 status --short
sha256sum build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/GPU_RETAINED_ARTIFACT_PROVENANCE_2026-10-14.md docs/gpu_retained_artifacts_2026-10-14.json
```

The [versioned catalogue](gpu_retained_artifacts_2026-10-14.json) records board,
device, format, image length/hash, original command/result/source metadata,
launcher tool versions, recovery profile, physical evidence scope and explicit
missing provenance. Null fields are unresolved, not inferred from current tools.
Record copies and their hashes are retained under
`build/parallel_tranches_20261014/gpu_provenance_01/`.

| Field | T1G rollback reference | T1H diagnostic |
|---|---|---|
| Original build terminal | Exactly one COMPLETE marker, exit 0, 364 seconds | Exactly one COMPLETE marker, exit 0, 967 seconds |
| Recorded source | Clean commit `a64d87c7ae0d96b44d8178c20f2421376a975ac0` | Dirty base `8ea3bc2abeaff97dac5b01ed558ee96008788340` |
| Retained tracked checkout | Present, currently clean, matching recorded HEAD | Dirty patch and untracked historical inputs not retained as a complete source tree |
| Build parameters | 25 MHz, four primitives, T1G B1/S1, seed 1 | 25 MHz, four primitives, scalar scene/diagnostic, T1H B1/S1, seed 1 |
| Constraints | Selected historical tracked XDC identified from script branch and parameters; hash retained | Exact dirty historical constraint/source closure not established |
| Programming bytes | 3,825,930 bytes; SHA256 matches ledger | 3,825,935 bytes; SHA256 matches ledger |
| Physical evidence | Bounded operator-observed A/B/C switching, [ledger §3.37](hardware_evidence.md) | Bounded operator-observed scalar-threshold A/B/C/A replay, [ledger §3.38](hardware_evidence.md); H1 HOLD |

The T1G XDC identity is inferred from the recorded clean script's GPUVGA /
GPU_T1D_UART=1 / GPU_T1D_DIAG=0 branch, not an explicit retained nextpnr argv
transcript. A clean commit identifies tracked sources, but does not establish
that external tools, chipdb, packing databases and generated inputs can be
restored. Neither COMPLETE nor a matching image hash establishes rebuild
reproducibility or complete timing acceptance.

Launcher records identify Yosys 0.63+87, SHA `2f1cdc2df`, and Himbächel
nextpnr-0.9-99-g4ace8952. They also report nextpnr-xilinx missing on the launcher
PATH. The actual build script performs environment setup and invokes
nextpnr-xilinx. Thus those launcher strings do not resolve the executed PNR
binary identity. Historical tool-binary hashes, chipdb hash, packing dependency
identities and durable download URLs remain unavailable in this inventory.

T1H's previously documented reconstruction gap is preserved in the
[source comparison](../build/gpu_evaluation/t1g_t1h_offline_qualification_20261007/source_compare.md).
Current source files cannot replace missing dirty historical inputs. Preserve
the image for its diagnostic/replay role; do not promote it to an independently
rebuildable release or infer that H1 has closed.

Next release work must locate retained external dependency identities and
qualify a restoration package. Publication remains separate. No fresh synthesis,
route or board campaign is proposed by this local catalogue.
