# Wukong V3 Gen-1 Surd CPU: preserved v0.2 sources

The Verilog, constraints and filelist used to build the bitstream that produced the single-run Wukong observations in
[`docs/hardware_evidence.md`](../../../../../docs/hardware_evidence.md) §3.40–3.43. They are preserved byte-for-byte as a
frozen reference; this directory is not a new design and adds no architecture or instructions.

- Provenance and every hash: [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md). Golden bitstream sha256
  `442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea`.
- Layout: `rtl/` (five silicon-used sources), `constraints/` (XDC), `filelists/` (original and portable), `provenance/` (original flow scripts, hashes, diffs).

## Relationship to `hardware/rtl`
The build used 17 unchanged files from `hardware/rtl/` plus the five files here. `rtl/spu13_core.v` is a **board-local copy** of
`hardware/rtl/core/spu13/spu13_core.v` with a 14-line driver-conflict fix; it is a historical silicon-build dependency, not an architectural fork.
`hardware/rtl` is unchanged, and promoting the fix there needs its own regression. This directory is not scanned by the regression runner, so the duplicate module name `spu13_core` does not collide.

## Build dependencies
Vivado 2026.1 (build 6511674), part `xc7a100tfgg676-1`, top `cpu_board_2r_top`. The recorded flow ran synthesis, route and bitstream as three stages
(`provenance/original_flow/`) with at least 5 GiB free RAM.

## Known limitations
- **Not yet rebuilt from this directory.** The original scripts hard-code the origin clone and Vivado install paths. `candidate_portable.f` has not been through Vivado, and a rebuild that reproduces the golden hash is not established (CPU-REPRO-1).
- The `.dcp`, `.bit` and `.bin` artifacts are not tracked; only their hashes are.
- The testbench used for ROM checking (`board_tb.v`) is not imported.
- Observations are single-run on one board; the limits are in the ledger entries. The XDC LED pins elsewhere in the repo are not used by this design (it has only `sys_clk`, `raw_rst_n`, `uart_tx`).

## Licensing and provenance
`hardware/` is mapped to CERN-OHL-W-2.0 in [`LICENSING.md`](../../../../../LICENSING.md); that is the intended treatment of these files. The files carry no notice of their own,
and none was added, to preserve their bytes. `spu13_core.v` derives from the tracked core and keeps whatever provenance that file has. Authorship of the other four files is not asserted here.
The contributor-terms conflict between `CONTRIBUTING.md` and `LICENSING.md` is unresolved and must be settled before publication.
