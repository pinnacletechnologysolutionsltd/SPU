# Source manifest: Wukong V3 Gen-1 Surd CPU (v0.2)

Maps the files in this directory to the build that produced the golden bitstream. It records identity only; it is not evidence of
timing, routing margin or board behaviour (see `docs/hardware_evidence.md` §3.40–3.43).

## Build identity
| Item | Value |
|---|---|
| Origin clone | `/home/john/.local/gate/spu-int3b-c3efc18` (not part of the repository) |
| Origin git head | `c3efc1878e5ae35601ec01a9e87e52ef032a7fc7` |
| `hardware/rtl` tree at origin head and at import | `d4135460dd52185ccadf5619e435c9088b69c992` |
| Tool | Vivado 2026.1 (lin64) Build 6511674 |
| Part / top | `xc7a100tfgg676-1` / `cpu_board_2r_top` |
| Bitstream properties | `COMPRESS=FALSE`, `UNUSEDPIN=PULLNONE`, `USR_ACCESS=0x48E0E161`, `CFGBVS=VCCO`, `CONFIG_VOLTAGE=3.3` |

## Build chain (artifacts are NOT tracked; hashes only)
| Stage | Artifact | sha256 |
|---|---|---|
| Phase S synthesis | `build/vivado/board3_01/synth/synth.dcp` (23,989,756 B) | `938f0772eb82f5f4bcbdb33def00b4363b11bfdb8749a257d592aab2ffd42f20` |
| Phase P route | `build/vivado/board3p_01/route/routed.dcp` (10,854,516 B) | `48e0e1613a76315592852d8462bf2f91680c2ed87bfa5575ea690a941988a5c8` |
| Phase 4B bitstream (golden) | `build/vivado/board4b_01/bit/cpu_board_2r_top.bit` (3,826,011 B) | `442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea` |
| Phase 4B binary | `build/vivado/board4b_01/bit/cpu_board_2r_top.bin` (3,825,788 B) | `cc259988b32dcd890a25c8a1765c6a28e3fafa280bcaed1aa5073f552dbc156c` |

The Phase S `run_manifest.txt` (preserved in `provenance/build_identity/`) lists every source read by synthesis with its sha256.

## Silicon-used sources in this directory (byte-identical to the origin; three renamed to match their module)
| Path here | Origin path (clone, `experiment/`) | sha256 |
|---|---|---|
| `rtl/spu13_core.v` | `cpu-integrate-4/rtl/spu13_core.v` | `e5701e5e0f267531726268fe2f52e7b1dede5eac04d3e532aecfd585828fcc3b` |
| `rtl/cpu_fetch_1b.v` | `cpu-integrate-4/frontend.v` | `d1f1cb408ba59f02b3faf8256d491b54b4661faeb5c536cdf658be34fe9b7780` |
| `rtl/cpu_rst_1b_supervisor.v` | `cpu-integrate-4/combined/supervisor.v` | `f441cee63e704f58e29b9f0a096b0acddac6aa4181d1ac69e17b162bda150f1c` |
| `rtl/cpu_integrate_1_top.v` | `cpu-integrate-4/top.v` | `59b6acac60ecbab402b6c12ddbc1546a29ed1022e4e5c9af21dc4e58cf08276c` |
| `rtl/board_top.v` | `cpu-board-3/board_top.v` | `f11f72f75ea4856b9f4f1494625f3dc505fc32d85c2358ea02569df177689c30` |
| `constraints/cpu_board_3.xdc` | `cpu-board-3/cpu_board_3.xdc` | `9449d1c79e8819a39ae64246076ff5fd2d468c493f1ab9030e05cdb9c6030500` |
| `filelists/candidate_original.f` | `cpu-board-3/candidate.f` | `cc5a035924cc87f750292ca5124dac611dd262c4a09d38e85a0f262cd6e5e600` |

## Other synthesis inputs: already tracked, unchanged
17 files under `hardware/rtl/` (all paths in `filelists/candidate_original.f` that begin `hardware/`), the four headers
`hardware/rtl/arch/spu_arch_defines.vh`, `hardware/rtl/arch/spu_isa_defines.vh`, `hardware/rtl/core/spu13/fpga_chain_arith.vh`,
`hardware/rtl/core/spu13/spu13_regen_arith.vh`, and `tools/vivado/spu_vivado_flow.tcl`
(`9aa1e17c5064a242187b4059a370851f6c3109348b5f4a433871ae73abd092f0`). Their hashes match the Phase S manifest.

## Core-fix relationship
`rtl/spu13_core.v` differs from `hardware/rtl/core/spu13/spu13_core.v` (sha256 `27559099e59143f2ca65d203b97945fa4e45c9fd498cc80f79ece99c6a39ed19`)
by 14 changed lines in three hunks (`provenance/diff/core_fix_cumulative.diff`; `core_fix_4.diff` is the INTEGRATE-4 increment):
the no-QR-file branch no longer drives `rote_F/G/H` and `regen_debug_status`, and `regen_debug_status` gets one driver
(`HAS_QR_FILE ? regen_debug_status_int : 16'd0`). The tracked core is not modified.

## Derived and provenance files (not silicon-build inputs)
- `filelists/candidate_portable.f`: same entries and order as the original, five paths rewritten; its hash differs from the golden `filelist_sha256`.
- `provenance/original_flow/`: scripts and PREFLIGHT hash files exactly as run; they contain absolute paths to the origin clone and are not runnable here as-is.
- `provenance/build_identity/`, `provenance/diff/`: recorded hashes, manifests, diffs.

`.gitattributes` (added at import) disables end-of-line conversion and the trailing-space check under `provenance/`, whose files keep tool-output whitespace.
`PACKAGE_SHA256.txt` lists the sha256 of every file in this directory except itself; verify with `sha256sum -c` from this directory.

## Not included
`board_tb.v` and `build/cpu-board-2r-isolated/` (deferred); the `.dcp`, `.bit` and `.bin` artifacts; the build logs and reports.
