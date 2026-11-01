# CPU-REPRO-1B result: fresh Vivado reproduction of the Gen-1 CPU configuration payload

**Disposition: PASS-BIT-EXACT for the configuration payload (single reproduction).**
This was a fresh Vivado 2026.1 implementation (synthesis, route, bitstream) from the tracked `cpu_v02/` sources using the portable flow in this directory.
It is **not** a new hardware observation: nothing was programmed, and it adds no entry to `docs/hardware_evidence.md`.

| Item | Value |
|---|---|
| Repository baseline | `86a9274` plus the waiver edit in `preflight.sh` / `run_repro.sh` (diff preserved as `meta/portable_uncommitted.diff`, sha256 `dd9e1c50a23850007f82db05966d47e0a1c52b3419b8c2dad28876961281bdef`) |
| Tool / part | Vivado 2026.1 SW Build 6511674, `xc7a100tfgg676-1`, 2 threads |
| Run | `repro1-b01`, one attempt, detached job unit `spu-repro1-b01-job-20261101T181319Z-313698`, `COMPLETE`, exit 0, 1318 s (limit 5400 s) |
| Evidence (untracked, `build/cpu-repro-1/repro1-b01/` and `repro1-b01-job/`) | 85 and 18 files; tree manifests sha256 `f214ab9bb56a8469edc7b3092338e0f5d16a4608380b1054191f4be02b183c5d` and `8863b670a654cd0d29e828f13ce37c544e95d365e0608006d0d1adca7080a526` |
| Generated `.bin` | `cc259988b32dcd890a25c8a1765c6a28e3fafa280bcaed1aa5073f552dbc156c` = golden payload; `.bit` payload equals the `.bin` |
| Generated `.bit` | `f8f1c9e965e68bf9c1e64497c74ed0d850e49b0c722ee9c8a5ed9443f4f20eef`; golden `442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea`. They differ only in the header build date/time (2026/11/02 07:35:00 vs 2026/10/30 17:17:58) |
| `synth.dcp` / `routed.dcp` | `9c57d35ba7911762f410c8fe9bc138e042847c84277ebe7310bb64036c664449` / `3497bbb3e4e9211b08c1b7801d112334acafdbd3c2554d3d130d7e2720cb583b` (golden `938f0772…` / `48e0e161…`; checkpoint bytes are not expected to match) |
| Implementation checks | 28,107 of 28,107 routable nets routed, 0 routing errors; WNS +6.360 ns, WHS +0.060 ns, 0 failing endpoints (same table as golden); 0 DRC errors (routed and pre-bitstream); 0 errors and 0 critical warnings in all three logs |
| Report comparison | the original run flagged 14 report differences (`COMPARE_RESULT.txt`, unchanged); all were separator-line width, date/command lines or the XDC path. After the comparator correction below, 0 differences |

## Memory waiver (provenance)
The default launch floor is 5 GiB `MemAvailable` and is unchanged. This run started with 4,884,212 kB available and 6,483,908 kB free swap (7,859,196 kB total; MemTotal 8,032,804 kB).
It used the owner's explicit, single-run waiver (`SPU_MEM_WAIVER=OWNER_WAIVER_CPU_REPRO_1B_RAM_SWAP_2026-11-02`, run id `repro1-b01` only), which also requires at least 4 GiB free swap and 3 GiB `MemAvailable`.
Peak resident size was 2.7 GB. The waiver is recorded in the run's `meta/WAIVER.txt`.

## Limitations
- One workstation, one reproduction attempt, Vivado 2026.1 build 6511674 only. Determinism across hosts, installs or Vivado versions is not established.
- Bit-exactness is for the configuration payload (`.bin`). The `.bit` file and the checkpoints differ in embedded metadata by construction.
- The golden artifacts used for comparison are outside the repository (`/home/john/.local/gate/spu-int3b-c3efc18/build/vivado`). The comparison can only be repeated where they are available.
- The run was made with a documented memory waiver; the 5 GiB floor was not met.
- Physical behaviour is covered only by the separate single-run observations in `docs/hardware_evidence.md` §3.40–3.43.

## Comparator correction (CPU-REPRO-1C)
`compare.py` now ignores separator-only lines (their width follows the ignored `Command` line) and treats `cpu_board_3.xdc` at different paths as equal (the XDC bytes are checked through the manifest hash). It takes an optional output path so a finished run directory is not rewritten. Re-comparing the preserved run gives 0 report differences and `PASS-BIT-EXACT`; `selftest.sh` still detects a mutated `.bin` and an altered report line.
