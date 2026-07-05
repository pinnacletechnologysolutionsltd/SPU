ECP5-85k: discovered files

Historical note, 2026-07-05: this records an early full-tree ECP5 synthesis
attempt. The current ECP5 direction is a curated source list and a lean i9/ECP5
RPLU2 synthesis audit. Use `docs/ecp5_85k_curated_source_strategy.md`,
`docs/colorlight_i9_feasibility.md`, and
`docs/COLORLIGHT_I9_PINOUT_VERIFIED.md` before acting on the recommendations
below.

Current update, 2026-07-06: the curated minimal ECP5-85F placeholder flow now
passes synthesis, P&R, and ecppack. The measured placeholder build uses 293 /
83,640 LUT4 before packing, 97 FF, 0 / 208 DP16KD, 0 / 156 MULT18X18D, and
reports 273.00 MHz max on the generated 12 MHz internal clock while passing the
50 MHz build constraint. The packaged bitstream is
`build/spu_ecp5_top.bit` (278 KiB). This is not a functional RPLU2 85F proof;
it verifies the curated source/LPF/toolchain path.

- docs/ecp5_evaluator_ee_handoff.md
- hardware/pcb/spu13_ecp5_carrier.kicad_pcb
- hardware/pcb/spu13_ecp5_carrier.kicad_prl
- hardware/pcb/spu13_ecp5_carrier_bom.csv
- hardware/boards/ecp5_85k/build_ecp5_85k.sh
- hardware/boards/ecp5_85k/spu_ecp5_85k.cst
- hardware/boards/ecp5_85k/spu_ecp5_top.v
- hardware/pcb/.history/spu13_ecp5_carrier.kicad_pcb
- hardware/pcb/spu13_ecp5_carrier.kicad_sch
- hardware/pcb/spu13_ecp5_carrier.kicad_pro
- hardware/docs/ecp5_oshwa_deliverable_audit.md
- hardware/docs/ecp5_oshwa_carrier_spec.md
- hardware/rtl/common/prim/spu_ecp5_prim.v
- hardware/rtl/peripherals/storage/spu_flash_bridge.v
- hardware/rtl/core/shared/spu_davis_gate.v
- hardware/rtl/gpu/spu4_bram_ip.v
- ECP5UM85Pinout.csv
- tools/pio_timing_budget.py
- tools/gen_kicad_schematic.py
- tools/pdn_analyze.py
- tools/generate_gerbers.sh
- tools/generate_oshwa_compliance.py
- docs/ee_handoff.md
- docs/CURRENT_STATUS.md
- docs/build_and_bringup_guide.md

Summary / Notes

1) Top-level status
- hardware/boards/ecp5_85k/spu_ecp5_top.v is an integration placeholder:
  - Uses a simple clock divider (TODO: replace with PLL/PLL IP).
  - Many control ports are tied off (alu_start, uart_tx, spu4 links) and PIO/SPI bridges are placeholders.
  - Telemetry signals mapped to LEDs for bring-up.

2) Build script
- build_ecp5_85k.sh existed but had invocation issues. In-session fixes were made to the script to pass sources correctly to yosys and to add include directories for the architecture headers.
- Final yosys invocation used read_verilog with -I include paths for hardware/rtl/arch and hardware/common/rtl/include.

3) Synthesis outcomes
- Yosys parsed the source tree and emitted several memory->register replacement warnings for rplu-related FIFOs and BRAMs.
- Synthesis failed due to a syntax issue in hardware/rtl/core/spu13/spu13_jet_mac.v: Yosys reported "syntax error, unexpected '[', expecting ')' or ',' or '='" at a multidimensional array port declaration (SystemVerilog-style packed/unpacked arrays). The module uses SystemVerilog array-of-vector syntax (e.g., input wire [31:0] j_coeff [0:N][0:3]) which Yosys Verilog-2005 front-end does not accept as-is.

4) Recommended next steps
- Priority: make the design parse/synthesize cleanly for Yosys.
  a) Convert problematic SystemVerilog multidimensional ports (e.g., in spu13_jet_mac.v) to Verilog-2005 compatible declarations (flatten arrays or expand into separate signals). This is surgical and recommended for long-term compatibility.
  b) If many SV constructs exist, write a small translation script to rewrite common patterns (array ports) into flattened vectors.
  c) For quick bring-up, blackbox the SV-heavy modules to complete P&R for pin/IO checks.
  d) Alternatively, use a toolchain with broader SystemVerilog support (Verific/Verilator) for initial parsing.

Files edited during session
- hardware/boards/ecp5_85k/build_ecp5_85k.sh (invocation and include-path fixes)

Report location in repo
- docs/ecp5_85k_report.md

Next action suggestions: convert spu13_jet_mac.v array ports, re-run build, then iterate on the next SV errors. If desired, prepare a translation script or produce a partial P&R with blackboxes.
