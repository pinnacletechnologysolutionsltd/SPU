# Current Project Status

Date: 2026-07-16

This file is the short source of truth for current board roles and near-term
bring-up direction.

## Architecture Identity

SPU-13 is a deterministic exact-arithmetic geometric field processor for
bounded control, graphics, simulation, and rational topological classification.
It is not a general CPU/GPU replacement, LLM/tensor accelerator, stochastic
neuromorphic processor, quantum computer, or certified safety controller as
delivered by this repository.

Canonical semantic boundary: `docs/SPU13_IDENTITY_AND_BOUNDARIES.md`.

## Board Roles

| Board | Role | Use for | Do not use for |
|---|---|---|---|
| Tang Primer 25K | Closed regression/probe target | SPI/RP2350 link checks, QLDI/QSUB QR commit readback, RPLU2 table hydration, math/ROTC/Lucas/robotics/SOM/neuro slice probes, risky PMOD wiring | Full concurrent RPLU2/SPU-13 integration, wide SDRAM confidence, architecture decisions driven by LUT starvation |
| Wukong Artix-7 100T | Artix silicon-evidence and constrained integration target | Reproducible Artix builds, LUCAS/SU3/ROBOTICS/RPLU2CORE/RPLU2PADE J11 proofs, shared-multiplier integration baseline, lean RPLU2 live-evaluator experiments, tensegrity admission-guard proofs | Full concurrent live RPLU2 plus all sidecars/safety layers, or first-pass risky wiring without a small smoke test; **J11's top-row pins (CS/SCK/MOSI) are permanently damaged from an RP2350 backfeed incident — remapped to the bottom row 2026-07-13, confirmed working in silicon 2026-07-14; `hardware/boards/artix7/spu_a7_100t.xdc` is the source of truth for per-pin status** |
| Colorlight i9 (ECP5-45F) | Open-toolchain ECP5 portability target | Routed lean RPLU2 ECP5 proof (Yosys/nextpnr-ecp5/ecppack), SDRAM, Ethernet, cheap warm spare | Full concurrent core integration — current RPLU2 probe already uses 72/72 DSPs |
| Kintex-7 K7-480T PCIe (YZCA-00338) | Full-integration + PCIe proof target | Full concurrent SPU-13/RPLU2/sidecar/safety images, PCIe host interface, 4GB DDR3 SDRAM, massive headroom for all arithmetic pipelines | Early bring-up — wait until Artix probe ladder and host-PC requirements are closed |
| Raspberry Pi Pico 2 | RP2350 southbridge reference board | Cleaner RP2350 wiring, PIO transport development, repeatable USB CDC/SPI/JTAG experiments | Replacing the Wukong/FPGA proof path; it is a transport upgrade, not a larger FPGA |

## Proven Hardware Path

- RP2350 SPI southbridge to Tang 25K is verified.
- RP2350 SPI-mode SD card path is verified.
- SD/RP2350/FPGA RPLU2 hydration is verified for corrected 149-record table
  profiles.
- Tang 25K `rplu2_arith_probe` verifies RPLU2 config hydration plus QLDI/QSUB
  QR commit readback in silicon.
- Tang 25K split builds keep the proven pieces reproducible without forcing the
  full live RPLU2 evaluator into an undersized device.
- Tang 25K `lucas_mac_probe` is SRAM-load/UART verified for the Lucas
  `FAST_ONLY=1` PSCALE/PCHIRAL paths and a 100-period PSCALE zero-drift
  marathon.
- Tang 25K `lucas_phslk_probe` is SRAM-load/UART verified for coherent,
  mismatched, and zero-divisor-denominator PHSLK cases, then continues a
  dynamic live-operand loop (`PHSLK:P` on `/dev/ttyUSB2`).
- Tang 25K `rotc_probe` is SRAM-load/UART verified for corrected ROTC angles
  0-5, including canonical VM/RTL trace matching and period closure.
- ROTC angles 0-35 are gated as the verified VM/RTL surface; angles 0-5 are
  silicon-verified, while 6-35 remain testbench/trace-equivalence verified.
- Tang 25K `irotc_probe` is SRAM-load/UART verified for IROTC probe vectors
  idx 16, idx 36 main catalog, and the BADIDX/UNTAGGED/CATMIX fault matrix
  (`IROTC:P E=00`). Full 60 x 2 catalog behavior is testbench-verified.
- Tang 25K `som_bmu_probe` is SRAM-load/UART verified for deterministic
  weighted SOM/BMU classification over the BRAM-backed 7-node fixture.
- Tang 25K `som_hydrate_probe` is SRAM-load/UART verified for SOM BRAM
  write/readback and per-feature byte-enable preservation (`HYD:P T:3 B:6 E:00`).
- Tang 25K `six_step_probe` is SRAM-load/UART verified for the period-6
  rational robotics kinematics harness (`KIN:P P:5 E:00`).
- Tang 25K `neuro_guard_probe` is SRAM-load/UART verified as a standalone
  fixed-epoch neuro sidecar proof.
- Tang 25K `neuro_sidecar_probe` is SRAM-load/UART verified for the
  SPI-visible adapter command path (`0xE0`/`0xE1`/`0xE2`/`0xE3`).
- Tang 25K final closeout soak: 40-second `/dev/ttyUSB2` capture stayed on
  repeated `KIN:P P:5 E:00` from `six_step_probe`.
- Wukong Artix-7 100T JTAG through RP2040 DirtyJTAG is verified, and Wukong
  J11 SPI through RP2350 is silicon-verified for LUCAS, SU3, SU3SHARE, and
  RPLU2CORE smoke images.
- Wukong Artix-7 `ROBOTICS` main-core image is SRAM-load/J11 verified:
  `rp2350_spu_arithmetic_test.uf2` passed QLDI, QSUB, all corrected ROTC
  angles 0-5, and ROTC angle-1 six-step closure (`13/13`, `ARITHMETIC_BLAZE:
  PASS`).
- Wukong Artix-7 `SU3SHARE` image is SRAM-load/J11 verified with one top-level
  shared `spu13_m31_multiplier`: SU3 dense-matrix readback and RPLU2 config/QR
  regression both pass on the same bitstream.
- Wukong Artix-7 `RPLU2PADE` image is SRAM-load/J11 verified for the full
  SPI-visible Thimble-Padé sidecar path: spu13_fp4_inverter,
  rplu_thimble_pade, spu13_rplu2_pade_sidecar, and
  spu13_spi_rplu2_pade all PASS. After removing accidental `% P`
  modular-negation synthesis from the FP4 inverter, the cleaned Artix build
  uses 20,277/126,800 SLICE_LUTX (15%), 6,678 FF, 72/240 DSP48E1 (30%),
  and 0 BRAM. Route closed by iteration 9. Post-route timing reports
  `clk_fast` max 36.54 MHz, passing at the 2 MHz bring-up target. RP2350 J11
  smoke repeatedly reports `RPLU2PADE_J11: PASS` across five rational
  constant Padé cases, with status `raw=7F 2A 13 00`, `crc_error=0`,
  and `busy=0`.
- Full repository regression on 2026-07-16: `python3 run_all_tests.py` reported
  `Total PASS: 161`, `Total FAIL: 0`.
- Tang 25K `irotc_spi` southbridge image is silicon-verified over the real
  RP2350 SPI link, 6/6 PASS, including the conjugate-catalog rotation
  (case 3) and CATMIX no-commit (case 4) — first conjugate-icosahedron
  silicon. Full evidence: `docs/hardware_evidence.md` §3.2k.1.
- Wukong Artix-7 `TENSEGRITYPROBE` image is silicon-verified: `TGR:P V:7
  E:00`, closing silicon evidence for all seven frozen TGR1 admission
  fixtures including the type-uniform Z[φ] equilibrium fault. Full
  evidence: `docs/hardware_evidence.md` §3.2l.
- Wukong Artix-7 `TENSEGRITYLINK` (host/BRAM transport for the tensegrity
  guard, SPI opcodes 0xB2/0xB3) is PnR-clean with a packed bitstream, but
  **not yet board-run** — do not cite as silicon-proven until a real bench
  session exercises B2/B3 and rollback.
- Tang 25K `SOM-SIDECAR`'s own bespoke SPI write/classify path
  (`spu_spi_cfg.v`) was found completely non-functional (a one-cycle-stale
  command-byte comparison meant no write could ever be accepted, in
  simulation or on real silicon) and fixed 2026-07-16. Its formerly unusable
  one-byte result read was also corrected to a two-byte command/response with
  latched valid/busy/label status. The repaired exact-field fixed-434-cycle
  sidecar is now silicon-verified over the real RP2350/Tang SPI link: three
  hydrated single-feature winners returned labels 0/2/3 with raw status bytes
  `80 A0 B0`, and the corrected C3 dock UART returned matching result bytes
  `00 14 1E`. The rebuilt image uses 12,786 LUT4 (55%), 8 BSRAM, 0 DSP and
  closes at 77.61 MHz against the 12 MHz target. Full evidence:
  `docs/hardware_evidence.md` §3.2g.2.

## Open-Toolchain Build Evidence

- Colorlight i9 `spu_colorlight_i9_rplu2_top` synthesis, P&R, and bitstream
  packaging pass with the open ECP5 flow. The 2026-07-06 route reports 6,881 /
  43,848 LUT4 before packing (15%), 7,271 / 43,848 TRELLIS_COMB after packing
  (16%), 1,967 FF, 0 / 108 DP16KD, 72 / 72 MULT18X18D, and 44.05 MHz max core
  clock while passing the 25 MHz build constraint. Packaged bitstream:
  `build/spu_colorlight_i9_rplu2_top.bit` (297 KiB). This is not yet a
  physical Colorlight hardware proof.
- ECP5-85F curated minimal placeholder synthesis, P&R, and bitstream packaging
  pass with `build_ecp5_85k_minimal.sh`. The 2026-07-06 route reports 293 /
  83,640 LUT4 before packing, 97 FF, 0 / 208 DP16KD, 0 / 156 MULT18X18D, and
  273.00 MHz max on the generated internal clock while passing the 50 MHz
  constraint. This validates the source-list/LPF/toolchain path, not a
  functional RPLU2 85F image.


## Current Priority

1. **Drive papers to ArXiv** (central SPU-13, RPLU v2, Lucas MAC, SU3) using existing Artix + Tang silicon evidence. The silicon proof is now good enough for credible preprints; papers are the gate to grant applications and international outreach.
2. **Acquire Raspberry Pi Pico 2** as the low-cost RP2350 reference southbridge. This gives cleaner headers and room for PIO transport work without disturbing the current RP2350-Zero wiring.
3. **Acquire Colorlight i9 (ECP5-45F)** when convenient for physical ECP5 smoke. The open-flow RPLU2 build now routes and packs; the remaining i9 gap is board-level programming/LED/SPI proof.
4. **Defer Kintex-7 K7-480T PCIe board** until budget, host-PC power/slot requirements, and risk tolerance are clear. Buy earlier only if a verified card appears at a price low enough to treat as an experiment.
5. **Prepare NLnet/open-hardware and MBIE/university grant tracks** after
   papers go live, but verify the active calls first. On 2026-07-05 the MBIE
   Endeavour 2026 round is contract-extension only, and NLnet's regular open
   call is temporarily narrowed while it transitions to the Open Internet Stack.
6. Keep the Tang 25K probe ladder buildable as a closed regression harness.
7. Keep the Wukong Artix-7 build regenerating from source without stale artifacts.
8. Treat `SU3SHARE` as the current Artix integration baseline. `RPLU2PADE` is the current Padé pipeline proof.
9. Keep SPI/J11 as the known-good control plane while PIO parallel transport is deferred to Pico 2 / evaluator-board work.

## Safety / Error-Correcting Layers (added June 2026)

All documented in `hardware/rtl/common/prim/spu_hamming_72_64.v` and the
corresponding wrapper modules. Verified with `TB_FILTER=hamming_72_64`,
`TB_FILTER=ecc_wrapper`, and `TB_FILTER=toroidal_regfile_ecc`.

| Layer | Module | Status |
|---|---|---|
| Lucas MAC norm invariant checker | `spu13_lucas_mac.v` | RTL verified |
| M31 RNS mod-3 parity (multiplier residue) | `spu13_m31_multiplier.v` | RTL verified, 6/6 RP2350 tests PASS |
| SPI deadman timer (128-cycle timeout) | `spu_spi_slave.v` | Hardware verified |
| CRC-8-CCITT on 0xB1/0xA5 writes | `spu_spi_slave.v` + `spu_link.c` | Hardware verified |
| QR regfile Hamming(72,64) SECDED | `spu_quadray_regfile_ecc.v` | RTL verified, 68 sub-tests |
| Toroidal regfile XOR checksum | `toroidal_regfile_ecc.v` | RTL verified |
| Fault telemetry → SPI status byte 3 | `spu_a7_top.v` | Wired, silicon test pending |

The ECC wrappers are active by default in all builds (quadray regfile is
always ECC-wrapped; the core `ENABLE_TORUS` gate controls the toroidal
integrity wrapper).

## RPLU Naming

There are two RPLU generations in the tree:

- Legacy RPLU: `ENABLE_RPLU`, `davis_to_rplu`, and `rplu_exp`. This is the
  older Morse/Padé response-surface path and is kept only for regression and
  historical comparison.
- RPLU2: `ENABLE_CORE_RPLU_V2*`, `rplu_pipeline`, and `rplu_thimble_pade`.
  This is the current A31/M31 Thimble-Padé path. Lean live-evaluator proofs
  target the Artix-7 100T; full concurrent integration belongs on an Artix-7
  200T / Kintex-class board.

## Lucas Sidecar

The Artix `LUCAS` spin instantiates `spu13_lucas_sidecar` beside the SPU-13
core and claims temporary probe opcodes from SPI `CMD 0xB1`:

- `0xD0`: PSCALE, `phi * (a+b phi)`
- `0xD1`: PCHIRAL, `conj(a+b phi)`
- `0xD2`: PMUL, `(a+b phi) * (c+d phi)`
- `0xD3`: PINV, `(a+b phi)^-1`

Instruction fields are `[55:52]=QR lane`, `[51:42]=a`, and `[41:32]=b`.
PMUL also uses `[31:22]=c` and `[21:12]=d`. The result is reported through
the existing SPI `0xAE` QR commit path with component A packed as
`{b[31:0], a[31:0]}` and B/C/D set to zero. The `0x50` range remains reserved
for current RPLU config opcodes.

Current Artix-7 build proof:

- `bash hardware/boards/artix7/build_a7.sh 100t lucas synth` reports Yosys
  `check` clean with estimated 5,073 LCs for the whole SPI-visible profile.
- Inside that profile, the hardened `spu13_lucas_mac` maps to 955 estimated LCs
  and 92 DSP48E1 slices. The SPI-visible sidecar adds CE-paced PMUL/PINV
  sequencing, so the complete LUCAS spin maps to 120 DSP48E1 slices.
- MAC PINV now has a `PINV_MAX_ITERS=64` watchdog, a registered multiply stage
  before the final Barrett reduction, active-opcode latching for multi-cycle
  operations, and runtime norm checks for PMUL/PINV.
- The Wukong V02 XDC is schematic-derived: 50 MHz oscillator on M21, reset on
  KEY0/H7, SPI on J11 PMOD, UART TX on the CP2102 RX path, and LED/fault outputs
  on board/header pins.
- The J11-PMOD remap of the LUCAS image routes at `A7_FREQ=2` with a final
  max frequency of 4.41 MHz. The same profile does not meet 50 MHz; the
  CE-paced sidecar paths are for bench bring-up, not final timing closure.
- `pack` emits `build/spu_a7_100t_LUCAS.bit` through Project X-Ray
  `fasm2frames.py` and `xc7frames2bit`.
- Wukong JTAG is now visible through the corrected RP2040 DirtyJTAG low-pin
  adapter. The old `build/pico_dirtyjtag_zero/dirtyJtag.uf2` reported the
  upstream Pico default pins (`16:TDI 17:TDO 18:TCK 19:TMS`), but the corrected
  2026-07-02 rebuild reports `0:TDI 1:TMS 2:TCK 3:TDO 4:RST 5:TRST`.
  With Wukong J1 wired `1=3V3 reference, 2=TCK, 3=TDO, 4=TDI, 5=TMS`,
  `openFPGALoader -c dirtyJtag --freq 1000000 --detect -v` finds one Xilinx
  Artix-7 XC7A100T device: IDCODE `0x03631093`, IR length 6.
- SRAM load of the pre-J11-remap `build/spu_a7_100t_LUCAS.bit` through RP2040
  DirtyJTAG at 1 MHz completed: `Load SRAM 100%`, `isc_done 1`, `init 1`,
  `done 1`.
  A passive 4-second `/dev/ttyUSB0` capture at 115200 baud produced no UART
  bytes; this is expected unless the loaded top receives SPI activity that
  generates `hex_valid`.
- On 2026-07-03 the Artix SPI pins were moved from the Wukong J12 20x2
  expansion header to the physical J11 PMOD (`H4/F4/A4/A5` for
  CS/SCK/MOSI/MISO), P&R completed, and `build/spu_a7_100t_LUCAS.bit` was
  repacked. SRAM load through DirtyJTAG completed with `Load SRAM 100%`,
  `isc_done 1`, `init 1`, `done 1`.
- Wukong J11 + RP2350 smoke silicon proof now passes external SPI commands:
  baseline status `00 FF 00 00`, PSCALE `D0200C0500000000` commits lane 2
  `A=0x0000000800000005`, PCHIRAL `D1C00C0500000000` commits lane 12
  `A=0x0000020400000008`, and PMUL `D2300C0500807000` commits lane 3
  `A=0x0000004200000029`. PINV `D3400C0500000000` commits lane 4
  `A=0x0000000500000201`. Each checked status returned idle
  `00 FF 00 00`, and repeated runs reported `LUCAS_J11: PASS`.
  The same J11 smoke proof passes after SRAM-loading the hardened rebuild.

Current Tang 25K fast-path silicon proof:

- `bash build_25k_spu13_lucas_mac_probe.sh` routes the `FAST_ONLY=1` probe at
  696 LUT4 / 216 DFF / 416 ALU, with 0 BRAM and 0 DSP.
- SRAM load of `build/tang_primer_25k_spu13_lucas_mac_probe.fs` reports
  `LUCAS:P` over UART.
- This covers PSCALE, PCHIRAL, and a 100-period PSCALE zero-drift marathon.
  It does not claim Tang silicon coverage for PMUL/PINV.

PSCALE/PCHIRAL remain zero-multiplier fast paths. PMUL and PINV are now
silicon-verified on Wukong through the CE-paced SPI sidecar sequencer.

## Artix Main Core

The Artix `ROBOTICS` spin instantiates the main `spu13_core` with MATH and
gatekeeper enabled, using the same physical Wukong J11 SPI path as the LUCAS
and SU3 sidecar images.

Current Artix-7 ROBOTICS build proof:

- `build/spu_a7_100t_ROBOTICS.bit` SRAM-loads through RP2040 DirtyJTAG at
  1 MHz and reports `isc_done 1`, `init 1`, `done 1`.
- On 2026-07-04, `rp2350_spu_arithmetic_test.uf2` drove the Wukong J11
  southbridge at 25 kHz SPI. The full 13-test suite passed:
  QLDI positive/signed loads, QSUB positive/negative/self-zero, corrected ROTC
  angles 0-5, and ROTC angle-1 six-step closure.
- The captured result ended with `=== Results: 13/13 PASSED ===` and
  `ARITHMETIC_BLAZE: PASS`.

## SU3 Sidecar

The Artix `SU3` spin instantiates `spu13_su3_sidecar` and
`spu13_su3_mult` as a sidecar-only Wukong image. It uses existing SPI
`CMD 0xB1` with temporary probe opcodes:

- `0xEA`: `SU3_START`, selects result element `[51:48]`
- `0xE8`: `SU3_LOAD_A`, streams element `[55:52]`, word `[50:48]`,
  data `[31:0]`
- `0xE9`: `SU3_LOAD_B`, same packing for the B matrix
- `0xEB`: `SU3_READ`, commits captured result element to QR A/B/C/D

Current Artix-7 SU3 build proof:

- `build/spu_a7_100t_SU3.bit` SRAM-loads through RP2040 DirtyJTAG at 1 MHz
  and reports `isc_done 1`, `init 1`, `done 1`.
- The current routed snapshot uses 21,092 LUT cells, 9,488 FFs, and 64
  DSP48E1 slices. Post-route timing reports `clk_div[5]` max 51.58 MHz and
  board-clock path max 128.63 MHz, both PASS at the 2 MHz route target.
- `TB_FILTER=spu13_su3 python3 run_all_tests.py` passes the SU3 multiplier
  and sidecar RTL tests plus the focused C++/Python regression subset.
- On 2026-07-04, `rp2350_su3_j11_smoke.uf2` streamed the dense A/B fixture
  over Wukong J11 at 100 kHz with 20 us CS setup, read turnaround, CRC hold,
  and CS recovery delays. The RP host
  checker polls per-chunk sidecar debug status and treats final `LOAD_B`
  completion as `SIDE_IDLE + result_ready`.
- Silicon QR readback matched oracle constants for three result elements:
  elem 0/lane 2, elem 4/lane 5, and elem 8/lane 8. The capture ended with
  `SU3_J11: PASS`; a 40-second capture at 20 us showed thirteen complete
  three-case passes before timing out mid-run 13. A 5 us probe produced an
  intermittent invalid QR read, so 20 us is the current practical margin
  setting.

Current Artix-7 SU3SHARE shared-multiplier proof:

- `SU3SHARE` instantiates the main core, RPLU2 config/QR path, SU3 sidecar, and
  one top-level `spu13_m31_multiplier`. The SU3 sidecar uses external multiplier
  ports; the core/RPLU Padé path is wired to the same instance. For this proof
  `_R2_PIPELINE=0`, so RPLU2 config/QR regression is active while the live Padé
  evaluator remains disabled.
- `TB_FILTER=spu13_su3 python3 run_all_tests.py` passes, and the SPI-level
  external-multiplier testbench `spu13_spi_su3share_tb.v` passes with
  `PASS: SPI SU3 QR2 element 0`.
- `A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t
  su3share synth/pnr/pack` completes. The routed image uses 60,837 LUTX
  cells, 16,478 FFX cells, and 64 DSP48E1 cells; router convergence ended with
  `overused=0`, and post-route timing reports `clk_fast` max 3.67 MHz, PASS at
  the 2 MHz bring-up target.
- Packed bitstream: `build/spu_a7_100t_SU3SHARE.bit`, SHA-256
  `0f886350d43966303aa1c74c38265dd8ee3b8554b71eb531589027db780681cf`.
- SRAM load through DirtyJTAG completed with `Load SRAM 100%`, `isc_done 1`,
  `init 1`, and `done 1`.
- With `rp2350_su3_j11_smoke.uf2`, the shared image repeatedly reports
  `SU3_J11: PASS` for all nine dense-matrix oracle result elements, read back
  through QR lanes 0 through 8. The current expanded smoke UF2 SHA-256 is
  `a6d8f0541fd2cce3a930173b0ee43ba071c92826fc5dc81540674c1e0a9da87d`.
- With `rp2350_rplu2_j11_smoke.uf2` loaded after the SU3 smoke, the same
  `SU3SHARE` bitstream reports `RPLU2_J11: PASS`, `RPLU2CORE_QR: PASS`, and
  `RPLU2CORE_QSUB: PASS`, with `rplu2_sum=0x0AA480E7` and
  `rplu2_status=0xC02E0001`.

## Neuro Epoch Sidecar

`hardware/rtl/core/spu13/spu13_neuro_epoch_sidecar.v` is the first RTL proof
for the safe neuromorphic sidecar idea. It is synchronous by construction:
fixed-length epochs, digital leaky-integrate-and-fire membrane updates,
boundary clamp, token projection into `Z[phi]/L_p`, Lucas norm admission, and
fallback commit on norm mismatch or token counter overflow.

Current status: RTL/testbench verified with focused `neuro` regressions;
standalone Yosys `check` reports zero structural problems. The Tang 25K
`neuro_guard_probe` builds, routes, SRAM-loads, and reports
`N:P T:4 P:003/003 K:009 C:007/008 E:00` over UART. The hardware-verified
Tang image uses `synth_gowin -noalu` and reports 5,016 LUT4 / 358 DFF, 0 BRAM,
0 DSP, 0 ALU carry cells, with a 33.27 MHz post-route max frequency at a
12 MHz target.

The Tang 25K `neuro_sidecar_probe` also builds, routes, SRAM-loads, and
reports `N:P T:3 E:00` over UART. It self-drives the SPI-visible adapter
opcodes `0xE0` config, `0xE1` start, `0xE2` spike, and `0xE3` readback. The
hardware-verified image reports 4,013 LUT4 / 380 DFF, 0 BRAM, 0 DSP, 0 ALU
carry cells, with a 99.53 MHz post-route max frequency at a 12 MHz target.
The next integration step is an Artix `NEURO_SAFE` spin that exposes the same
epoch control and guard telemetry over the existing SPI southbridge path.

## Canonical References

- Build and board commands: `docs/build_and_bringup_guide.md`
- Architecture identity and claim boundaries:
  `docs/SPU13_IDENTITY_AND_BOUNDARIES.md`
- Market and grant positioning: `spu_strategy/` (private, untracked)
- Neuro-safe sidecar plan: `docs/archive/legacy/neuro_safe_sidecar_plan.md`
- SU3 coprocessor plan and paper:
  `docs/SU3_EXTENSION_PLAN.md`, `docs/SU3_COPROCESSOR_PAPER.md`
- Wukong/OpenXC7 setup: `docs/toolchain_setup.md`
- Southbridge protocol and SD/RPLU2 hydration evidence:
  `docs/SOUTHBRIDGE_SPI_PROTOCOL.md`
- Tang 25K regression ladder: `docs/archive/tang25k/tang25k_replacement_bringup_plan.md`
