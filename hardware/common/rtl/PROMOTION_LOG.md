# RTL Promotion Log
**Date:** 2026-04-02  
**Source:** `reference/synergeticrenderer/Laminar-Core/hardware/archive/`  
**Destination:** `hardware/common/rtl/`  
**Context:** Systematic archive promotion following ISA v1.2 completion + Gowin FPGA pivot.
The architecture is substantially more complete than when the archive was last active:
- ISA v1.2 (23 opcodes, EQUIL/IDNT/JINV/ANNE VE group) now stable
- Standalone assembler v3.0 and 10-test verification suite operational
- Hardware target changed from iCE40UP5K → Gowin GW1NR-9 (Tang Nano 9K) + GW2A-18 (Tang Primer 20K)

---

## Summary

| Category | Files Promoted | Destination |
|----------|---------------|-------------|
| Core ALU | 11 | `core/` |
| Primitives | 18 | `prim/` |
| Graphics | 18 | `graphics/` |
| Bio/Physics | 18 | `bio/` |
| Memory | 4 | `mem/` |
| I/O | 11 | `io/` |
| Testbench | 2 | `tb/` |
| **Total** | **82** | |

---

## core/ — Core ALU Modules

| File | Module | ISA Opcode | Board Target | Notes |
|------|--------|-----------|--------------|-------|
| `spu13_rotor_core.v` | spu13_rotor_core | ROT, QROT | All | Thomson Rotor ALU; circulant a+b√3 arithmetic |
| `spu_execution_unit.v` | spu_execution_unit | All | All | 3-cycle DSP pipeline; SovereignBus interface |
| `spu13_scoreboard.v` | spu13_scoreboard | — | All | Pipeline hazard detection |
| `spu_identity_monad.v` | spu_identity_monad | IDNT | All | Rational guard gate; backs IDNT opcode |
| `spu_tensegrity_balancer.v` | spu_tensegrity_balancer | EQUIL | All | Geometric Laplacian + Laminar threshold; backs EQUIL |
| `spu_core.v` | spu_core | All | All | Integrator: fluidizer+trig+fluid solver+annealer; 5.9K lines |
| `spu_light_core.v` | spu_light_core | — | Nano 9K | Lightweight ALU; fits iCE40/small-LUT targets |
| `spu_nano_core.v` | spu_nano_core | — | Nano 9K | Stress-ready minimal core for embedded targets |
| `spu_command_processor.v` | spu_command_processor | — | All | Instruction decode + dispatch |
| `spu_folded_alu.v` | spu_folded_alu | MUL, ADD | All | TDM-folded tetrahedral ALU |
| `spu1_alu.v` | spu1_alu | ADD,SUB,MUL | All | Unified isotropic ALU for RationalSurd |

---

## prim/ — Arithmetic Primitives

| File | Module | ISA Opcode | Notes |
|------|--------|-----------|-------|
| `spu_smul.v` | spu_smul | MUL | a+b√3 surd multiplier |
| `spu_sadd.v` | spu_sadd | ADD | SIMD parallel surd adder |
| `spu_sqr_rotor.v` | spu_sqr_rotor | ROT | SQR chiral rotor |
| `spu_quadrance_calc.v` | quadrance_calc | SNAP | Wildberger Quadrance/Spread — backs SNAP opcode |
| `spu_quad_adder.v` | quad_adder | QADD | Asymmetric Quadray adder |
| `phi_rotor_scaler.v` | phi_rotor_scaler | QROT | Golden ratio rotation scaling |
| `spu_rational_trig.v` | spu_rational_trig | SPREAD | Rational trig; backs SPREAD opcode |
| `spu_rational_snap.v` | spu_rational_snap | HEX | Cartesian-to-Quadray bridge; backs HEX |
| `spu_rational_log.v` | spu_rational_log | LOG | Bit-position gate logarithm |
| `spu_sin_lut.v` | spu_sin_lut | — | Rational sine LUT (no transcendentals) |
| `spu_rational_lut.v` | spu_rational_lut | — | Rational reciprocal LUT |
| `quadray_rotor.v` | quadray_rotor | QROT | GLU primitive for Quadray rotations |
| `surd_multiplier.v` | surd_multiplier | MUL | Rotor core surd multiplier |
| `spu_impressionist_rotor.v` | spu_impressionist_rotor | ROT | Rational rotor with convergent rounding |
| `spu_rotary_gate.v` | spu_rotary_gate | — | Gate logic for rotation |
| `spu13_rotary_gate.v` | spu13_rotary_gate | — | SPU-13 specific rotation gate |
| `spu_quadray_vec.v` | spu_quadray_vec | QLOAD,QNORM | Quadray vector datapath |
| `spu_ecc.v` | spu_ecc | — | ECC for manifold integrity |

---

## graphics/ — Display & Rendering Pipeline

| File | Module | Notes | Board Target |
|------|--------|-------|--------------|
| `spu_gpu_top.v` | spu_gpu_top | Top-level GPU orchestrator; unifies all rendering primitives | Primer 20K |
| `spu_rasterizer.v` | spu_rasterizer | Bit-exact 64-bit isotropic edge-function rasterizer | All |
| `spu_bresenham_killer.v` | spu_bresenham_killer | Rational lattice line draw; phase-locked 61.44 kHz | All |
| `spu_hal_vga.v` | spu_hal_vga | VGA 640×480 @ 60Hz HAL | Primer 20K |
| `spu_hal_cartesian.v` | spu_hal_cartesian | Cartesian display translator (SDP HAL_Cartesian) | All |
| `spu_fragment_pipe.v` | spu_fragment_pipe | Fragment pipeline; barycentric pixel energy interpolation | Primer 20K |
| `spu_affine_raster.v` | spu_affine_raster | Rational barycentric rasterizer | All |
| `spu_harmonic_vis.v` | spu_harmonic_vis | Harmonic field visualization engine | All |
| `spu_hal_vector.v` | spu_hal_vector | Vector display HAL (SDP HAL_Vector) | All |
| `spu_lithic_overlay.v` | spu_lithic_overlay | Dynamic geometry command overlay | All |
| `HAL_Native_Hex.v` | HAL_Native_Hex | Native 60° hex display HAL (SDP HAL_Native_Hex) | All |
| `spu_synergetic_buffer.v` | spu_synergetic_buffer | Entity store (Chords in SDRAM lattice; no framebuffer) | Primer 20K |
| `vector_to_parabola.v` | vector_to_parabola | Parabolic projection HAL | All |
| `spu_oled_visualizer.v` | spu_oled_visualizer | Dual-hemisphere OLED visualizer | All |
| `spu_ssd1306_driver.v` | spu_ssd1306_driver | SSD1306 I2C OLED driver (complete) | Nano 9K |
| `spu_eink_waveshare_driver.v` | spu_eink_waveshare_driver | Waveshare e-ink SPI driver | Nano 9K |
| `spu_manifold_mirror.v` | spu_manifold_mirror | Manifold reflection/inversion display op | All |
| `spu_sierpinski_nav.v` | spu_sierpinski_nav | Sierpinski-lattice navigation/fractal render | All |

---

## bio/ — Bio-Laminar & Physics Modules

| File | Module | Notes |
|------|--------|-------|
| `spu_fluid_solver.v` | spu_fluid_solver | Deterministic Navier-Stokes; 12-neighbour IVM divergence + Laminar Equilibrium Guard |
| `spu_bio_pulse.v` | spu_bio_pulse | 61.44 kHz Piranha Pulse generator; biological entrainment |
| `spu_bio_gateway.v` | spu_bio_gateway | Bio-Laminar Gateway; real-time human/machine manifold sync |
| `spu_bio_filter.v` | spu_bio_filter | CIC resonant bio-signal filter |
| `spu_active_inference.v` | spu_active_inference | Active Inference Kernel; hardware predictive processing + error suppression |
| `spu_hardware_inference.v` | spu_hardware_inference | Hardware-level inference engine |
| `spu_resonance_gen.v` | spu_resonance_gen | Resonance oscillation generator |
| `spu_soul_metabolism.v` | spu_soul_metabolism | Energy balance + metabolic state manager (Safety Valve Edition) |
| `spu13_anneal_stabilizer.v` | spu13_anneal_stabilizer | Sub-pixel entropy → Sovereign Stillness; backs ANNE opcode |
| `spu_annealer.v` | spu_annealer | Isotropic simulated annealer |
| `spu_proprioception.v` | spu_proprioception | Thermal-aware self-regulated homeostasis |
| `spu_viscosity_monitor.v` | spu_viscosity_monitor | Fluid viscosity/damping tracker ("Surfer's Logic") |
| `spu_geometry_fluidizer.v` | spu_geometry_fluidizer | Rational vertex convergence; removes Z-fighting/Lego-brick jitter |
| `spu_thermal_entropy.v` | spu_thermal_entropy | Thermal noise model |
| `spu_qfs_pour.v` | spu_qfs_pour | Laminar fluid pour (QFS Euler step) |
| `spu_dream_log.v` | spu_dream_log | Dream-state logger (bio-cycle telemetry) |
| `spu_soul_snapper.v` | spu_soul_snapper | Soul-state snapshot capture |
| `spu_metabolic_sense.v` | spu_metabolic_sense | Metabolic sensing front-end |

---

## mem/ — Memory HALs (additions to existing)

| File | Module | Notes | Board Target |
|------|--------|-------|--------------|
| `HAL_SDRAM_Winbond.v` | HAL_SDRAM_Winbond | **Critical** — Winbond W9864G6KH-6 SDR-SDRAM controller, 640×480 framebuffer capable | Primer 20K DDR3 |
| `spu_dma_manifold.v` | spu_dma_manifold | DMA engine for manifold data streams | Primer 20K |
| `spu_laminar_ram.v` | spu_laminar_ram | Laminar block RAM abstraction | All |
| `spu_fractal_compressor.v` | spu_fractal_compressor | Sierpinski-based lossless manifold compressor | All |

---

## io/ — I/O Bridges & Drivers

| File | Module | Notes |
|------|--------|-------|
| `spu_chord_rx.v` | spu_chord_rx | Whisper protocol Chord receiver |
| `surd_uart_tx.v` | surd_uart_tx | UART transmitter that serialises RationalSurd values directly |
| `spu_io_bridge.v` | spu_io_bridge | General I/O bridge |
| `spu_adc_bridge.v` | spu_adc_bridge | ADC interface bridge |
| `spu_serial_davis_gate.v` | spu_serial_davis_gate | Serial Davis Gate — SNAP over UART |
| `spu_sd_controller.v` | spu_sd_controller | SD card SPI controller |
| `spu_artery.v` | spu_artery | Artery data bus module |
| `spu_artery_phy.v` | spu_artery_phy | **FIXED** — was SB_GB (iCE40); replaced with generic `assign`; synthesiser auto-promotes to global clock net on Gowin |
| `spu_niche_logic.v` | spu_niche_logic | Niche/edge-case bus logic |
| `spu_hard_stop.v` | spu_hard_stop | Hard stop / emergency halt |
| `spu_laminar_reset.v` | spu_laminar_reset | Laminar reset sequencer |

---

## tb/ — Testbenches

| File | Notes |
|------|-------|
| `gpu_pipeline_tb.v` | GPU pipeline simulation testbench — run with `iverilog` |
| `spu_whisper_sane.v` | Whisper protocol sanity testbench |

---

## Skipped / Deferred

| File | Reason |
|------|--------|
| `spu_rational_mul.v` | Uses `SB_MAC16` (iCE40 DSP slice) — needs rewrite targeting Gowin `MULT18X18` / `ALU54D`. Deferred to `gowin-dsp` todo. |
| `spu_tang25k_top.v` | Uses `SB_HFOSC` (iCE40 HF oscillator) — board-specific top level; not portable. |
| `HAL_PSRAM_APS6404L.v` | Already present in `mem/` — identical 144-line file. |
| `spu_davis_gate.v` | Already present at `rtl/spu_davis_gate.v` — existing version richer (42 vs 28 lines). |
| `spu_laminar_power.v` | Already present at `rtl/top/spu_laminar_power.v` — current-generation version kept. |
| `spu_permute_13.v` | Already present at `hardware/spu13/rtl/spu_permute_13.v`. |

---

## ISA v1.2 Opcode → RTL Coverage Map

| Opcode | RTL Module(s) |
|--------|--------------|
| LD | spu_register_file.v (existing) |
| ADD | spu_sadd.v, spu1_alu.v |
| SUB | spu1_alu.v |
| MUL | spu_smul.v, surd_multiplier.v |
| ROT | spu13_rotor_core.v, spu_sqr_rotor.v |
| LOG | spu_rational_log.v |
| JMP/COND/CALL/RET | spu_command_processor.v, spu13_scoreboard.v |
| SNAP | spu_quadrance_calc.v (Davis Gate) |
| QLOAD/QLOG | spu_quadray_vec.v |
| QADD | spu_quad_adder.v |
| QROT | spu13_rotor_core.v, phi_rotor_scaler.v, quadray_rotor.v |
| QNORM | spu_quadray_vec.v |
| HEX | spu_rational_snap.v |
| SPREAD | spu_rational_trig.v, spu_quadrance_calc.v |
| NOP/HALT | spu_execution_unit.v |
| EQUIL | spu_tensegrity_balancer.v |
| IDNT | spu_identity_monad.v |
| JINV | spu_janus_mirror.v (existing spu13/rtl/) |
| ANNE | spu13_anneal_stabilizer.v |

---

## Next Steps for Promoted Files

1. **gowin-dsp**: Rewrite `spu_rational_mul.v` using Gowin `MULT18X18` — unblocks TDM-ALU DSP path
2. **nano9k-spu4**: Wire `spu_nano_core.v` + `spu_light_core.v` to Tang Nano 9K CST constraints
3. **sdram-64mb**: Wire `HAL_SDRAM_Winbond.v` to Tang Primer 20K — on-board 128MB DDR3
4. **graphics pass**: Validate `spu_gpu_top.v` pipeline with `gpu_pipeline_tb.v` before synthesis
5. **bio integration**: Connect `spu_bio_pulse.v` (61.44 kHz) as the Piranha Pulse master for all cores
