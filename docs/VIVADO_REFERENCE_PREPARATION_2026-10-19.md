# Vivado reference: isolated Artix-7 preparation

Date: 2026-10-19. Status: PREPARATION ONLY; implementation NOT RUN.
No tool installation, licence generation, FPGA programming or purchase occurred.

The [source reconciliation](VIVADO_SOURCE_RECONCILIATION_2026-10-19.md) now
explains the core change, separates historical H0 from prospective C1 and
supersedes the initial inventory with a 35-file static include-closed packet.
The original 33-file packet and unexecuted Tcl are retained as preparation
history; they are not a complete-input or source-matched implementation claim.
The [environment check](VIVADO_ENVIRONMENT_READINESS_2026-10-19.md) records the
unsupported local distro and resource headroom. Next steps are separately
authorized supported-environment/licence setup and C1 RTL elaboration, not
the proposed full implementation campaign below.

## Verified tool availability and licensing

AMD's current [licensing options](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado/vivado-licensing-options.html)
list BASIC as free with annual renewal, Linux support and all 7-series devices.
The [licensing FAQ](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/licensing-faq.html)
requires a valid annual free licence file for BASIC starting with 2026.1.
The [nextpnr project](https://github.com/YosysHQ/nextpnr) still describes its
Project X-Ray-based 7-series support as experimental. Checked 2026-10-19.
The local PATH and bounded searches of conventional installation locations
found no Vivado executable. Product eligibility is not an installed/licensed
tool, a Linux distribution compatibility result or a successful implementation.

## Concrete preserved inputs

Prepared `build/vivado_reference/preparation_01/source_manifest.json` and copied
33 source/include/memory/constraint inputs below its `inputs/` directory.
Top: `spu_a7_surd_cpu_bench_top`, ENABLE_SURD_CPU=1, candidate part
`xc7a100tfgg676-1`, sys_clk period 40 ns (25 MHz). Source list originated in
the existing `focused_01/cpu/rtl_source_list.txt`, plus the wrapper and XDC.
These are source snapshots, not a completed Vivado elaboration/project.
The packet's `project.tcl` is a concrete, unexecuted in-memory-project recipe
using 19 captured RTL inputs, the captured include directory and XDC. It
requests a new isolated run directory, four threads, the frozen top/part,
synthesis, optimization, placement, physical optimization, routing, checkpoints
and reports. It has not been validated by Vivado and is not a launch authority
or a substitute for an approved resource-enforcing wrapper/source guard.

One captured RTL source, `hardware/rtl/core/spu13/spu13_core.v`, differs from
the historical `build_repair_freeze_03/sources.sha256`. The other captured inputs
match that old guard. Therefore this packet cannot silently be described as
the identical historical open-backend design. Before implementation, choose
and independently verify a matched RTL/constraint baseline; identify which
preserved open-backend artifact uses it. Include transitive module/include/
memory dependencies discovered during elaboration; 33 files is a preparation
inventory, not yet a proven complete elaboration closure.

The existing Yosys script also deliberately maps REGEN multipliers to soft
logic while retaining Surd DSP allocation. An unconstrained Vivado synthesis
need not make the same choices. Record that policy difference, resources and
functional configuration; a direct RTL implementation is an independent
end-to-end flow comparison, not a controlled router-only experiment.

## Proposed separately approved campaign

Proposed budget: one attempt, 3,600 seconds total synthesis plus implementation,
four threads and 16 GiB maximum memory. This proposal is NOT a frozen approved
budget. Do not launch, retry, extend or substitute another device without the
owner's separate campaign approval and a concrete reviewed invocation.

After installation/licence and source reconciliation, prepare a batch Tcl
project confined to a new `build/vivado_reference/` child. Freeze:

1. Tool build, full part/package/speed grade, top, parameters, source hashes,
   include paths, memory initializations and XDC hash.
2. Synthesis, opt_design, place_design, physical optimization policy and
   route_design directives, without production RTL/pipeline changes.
3. Clock, input/output delay assumptions and reset exceptions. Preserve the
   existing 40 ns clock; do not invent I/O timing or false-path exceptions to
   obtain a passing timing summary. Missing external timing remains explicit.
4. Reports after synthesis and route: LUT/FF/DSP/BRAM, hierarchy, DRC,
   report_route_status, report_timing_summary, unconstrained paths and
   report_methodology; preserve placed and routed checkpoints and complete logs.
5. Success requires completed routing with no unrouted nets and reviewed routed
   setup/hold timing, WNS/TNS and timing coverage for the declared constraints.
   Missing constraints, waived failures or incomplete implementation are not PASS.

Use the repository detached runner for the approved long job; preserve command,
resource enforcement, all logs and exactly one terminal marker. End the agent
turn on LAUNCHED. Do not program the board as part of this diagnostic.
This document supplies no executable implementation command while Vivado and
matched source identity are unresolved.

## Interpret independently

Successful Vivado routing at the required timing would establish realizability
of its named implementation; it would not prove every prior failure was a
backend defect, nor qualify unchanged I/O or physical board operation.
Failure in both flows likewise would not establish that the RTL cannot fit:
inspect constraints, mapping, resource use and diagnostics before attribution.
Retain the open flow and existing Gowin platforms. Defer a board purchase until
the tool comparison provides a demonstrated need. QSG software progress has
its own lightweight budget and is not contingent on this hardware campaign.
