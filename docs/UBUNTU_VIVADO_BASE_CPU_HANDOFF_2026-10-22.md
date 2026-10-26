# Ubuntu / Vivado handoff for the Base CPU campaign (2026-10-22)

Audience: the agent working on Ubuntu 22.04.5 with Vivado 2025.2. Status: documentation only. Nothing here is a Vivado result; no timing, placement or board claim is made.
Silicon claims live only in [`hardware_evidence.md`](hardware_evidence.md). This supersedes nothing: [`UBUNTU_VIVADO_HANDOVER_2026-10-21.md`](UBUNTU_VIVADO_HANDOVER_2026-10-21.md) (untracked, other author) describes the older Full-CPU C1 baseline, which is a **different source package**; do not mix them.

## 1. Authorization state (owner decisions, 2026-10-22)
| Item | State |
|---|---|
| Phase 1 (`tools/vivado/`) | accepted provisionally, pending diff review |
| Environment smoke test (`tools/vivado/tests/phase2_smoke.tcl`) | authorized after install; no design, no synthesis |
| Tensegrity-link Vivado synthesis | **GO, conditional on the smoke test passing**: 1 attempt, 0 retries, 900 s, synthesis and reports only, strict gate off |
| Base CPU Vivado synthesis | **HOLD** |
| Place / route / bitstream / hardware / board | **not authorized** |
| Any RTL, XDC or frozen-manifest edit; changing a threshold to make a run pass | **prohibited**; report failures, do not repair |
Long jobs (>60 s) go through `tools/run_detached_job.sh` (AGENTS.md section 4.2). Do not set an address-space limit on Vivado; record real memory use instead.

## 2. Getting the sources (read this first)
This checkout is **not** a clean base. Local `master` is `963a685`; published `origin/master` is `4e0d5b9` and local history is not a descendant of it. The Base CPU also depends on uncommitted work: 9 untracked surd-CPU RTL files, a modified `spu13_core.v` (ENABLE_REGEN plus earlier CPU tranches) and the untracked bench top, Base top, Base XDC and testbench. A plain clone therefore **cannot** build the Base package.
Use the bundle `~/spu-ubuntu-vivado-handover-2026-10-22.tar.gz` (sha256 `57d2654b749383724f91013a8f8b0128b05cfda7a50b810801a4bf255839e57c`, 76,866 bytes). It holds `overlay/` (the exact 30 files for both Vivado packages, at repo-relative paths, with `OVERLAY_SHA256SUMS`) and `evidence/` (small result files, `EVIDENCE_SHA256SUMS`). Extract the overlay over a checkout of this repository state (or onto a copy of this tree) and verify `sha256sum -c OVERLAY_SHA256SUMS` before any run. The Base files must hash to `build/cpu_base_top1_s2r3_prep/source_manifest.json` (copy in `evidence/`).

## 3. Commands
```bash
source /tools/Xilinx/Vivado/2025.2/settings64.sh          # adjust to the real install path
vivado -version
vivado -mode batch -source tools/vivado/tests/phase2_smoke.tcl      # smoke test; expect part_found: 1, commands_missing: none
# only if the smoke test passes (tensegrity-link baseline, conditional GO above):
OUT=build/vivado/tensegrity_link_01; mkdir -p $OUT
tools/run_detached_job.sh --output build/vivado/detached_tensegrity_link_01 --timeout 900 -- \
  vivado -mode batch -log $OUT/vivado.log -journal $OUT/vivado.jou -source tools/vivado/spu_vivado_flow.tcl -tclargs \
  -top spu_a7_tensegrity_link_top -part xc7a100tfgg676-1 -filelist tools/vivado/filelists/tensegrity_link_top.f \
  -xdc hardware/boards/artix7/spu_a7_tensegrity_link.xdc -outdir $OUT -expect_clock sys_clk:20.000
```
Before launch verify: smoke test output, `$OUT` new and empty, part present, sources present (the flow fails on a missing source), free RAM/swap. After: keep the whole transcript, `synth_utilization*.rpt`, `synth_clocks.rpt`, `synth_check_timing.rpt` (record the `no_clock` count: that design divides its own clock and its XDC has no generated clock, so a non-zero count is expected and informative), warnings, `run_manifest.txt`, `structure.rpt` and the single terminal marker (`COMPLETE`/`FAILED`). A clean result qualifies the flow at synthesis level only.

## 4. Part, clocks, pins: facts and open items
- Part: `xc7a100tfgg676-1` (`build_a7.sh`, `docs/VIVADO_REFERENCE_PREPARATION_2026-10-19.md`). The "-1" speed grade comes from build scripts: check against the physical marking. AMD lists XC7A100T under ML Standard (no licence); confirm with `get_parts` locally.
- Clock: `spu_a7_100t.xdc` names the port `clk_100mhz` but constrains 20 ns (50 MHz); the Base and tensegrity XDCs use `sys_clk`, 20 ns.
- UART divisor 217 corresponds to a 25 MHz clock (the GPU path sets 25 MHz and 115200 baud).
- **VGA red pin unresolved:** every VGA XDC in the repo puts `vga_r` on G8; an earlier handover said D7. HSYNC D5, GREEN G7, BLUE G5, VSYNC E5 agree. Resolve against the board schematic before trusting either.
- The Base XDC keeps `create_generated_clock` commented. A flop-divided clock is not derived by Vivado; until a correct generated clock exists the divided domain is unconstrained. `tools/vivado/proposals/base_cpu_generated_clock.xdc.proposal` is a proposal only: confirm the object names in the synthesized netlist first, and note it leaves open the reset-decode glitch hazard, the `rst_n` input policy, the `uart_tx` output policy and fabric-clock skew.

## 5. Base CPU state (Yosys, for comparison; not a Vivado result)
- Package: top `spu_a7_surd_cpu_base_top`, 20 sources in `tools/vivado/filelists/base_cpu_top.f`, XDC `spu_a7_surd_cpu_base.xdc`, `ENABLE_REGEN=0` set by the top's instantiation (no generic needed). Not the Full-CPU C1 package.
- S2-R3 (Yosys 0.63+87): all frozen netlist gates passed: no `spu13_regen`/`fpga_chain`, exactly 2 BUFG with no cascade, raw reset pad reaches only the first synchronizer flop, 2-flop local release synchronizer, workload on the divided clock, `uart_tx` = checksum parity (not serial UART), 80/240 DSP. LUT 21,652, FF 12,867, DSP 80, cells 45,266 (comparison only). No placement, routing or timing exists.
- S1 simulation (zero-delay BUFG): Full 255/0, Base 250/0 (baselines 254/249 plus one test). The 25 MHz release synchronizer and the combinational `rst_n_int` decode driving the async clear are not silicon-proven.
- Open-tool finding, for context: Yosys stalls when the ABC temp path is 80 or more characters (60 or fewer always completed). This is a toolchain issue, not a design issue, and does not apply to Vivado.

## 6. Do not
Modify CPU/GPU RTL or the manifests; alter acceptance thresholds; claim timing closure or readiness from synthesis; run anything on hardware; promote HOLD statuses (T1H H1 and T1r/VGAFIX visual remain HOLD per `CURRENT_STATUS.md`); commit or publish without a separate instruction.

## 7. Owner decisions still open
Schematic check for the VGA red pin; physical speed-grade check; whether to commit the uncommitted surd-CPU RTL set and reconcile the branch with `origin/master`; RAM cap policy for Vivado runs; D6 (the S7 bring-up image must be the Vivado-qualified one); the generated-clock and reset/IO constraint policy; the S3 placement ceiling (open-tool path).
