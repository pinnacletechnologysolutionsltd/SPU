# SPU-13 ECP5 OSHWA Certification Application

**Document:** OSHWA UID Application Draft
**Target:** Open Source Hardware Association (OSHWA) Self-Certification
**License:** CERN-OHL-W-2.0 (Hardware), CC0 1.0 (Documentation), MIT (Software)
**Status:** Pre-certification audit draft. Not ready to submit.

---

## 1. Project Identity

| Field | Value |
|:---|:---|
| **Project Name** | SPU-13 Synergetic Processing Unit — ECP5 Carrier Board |
| **OSHWA UID** | (To be assigned upon submission) |
| **Submitted By** | John Curley |
| **Contact Email** | (Public repository contact) |
| **Project Website** | https://github.com/pinnacletechnologysolutionsltd/SPU |
| **Date** | 2026-07-04 |

## 2. Hardware Description

The SPU-13 ECP5 Carrier Board is an open-source, symmetry-informed evaluator
concept for the SPU-13 deterministic rational-field processor. The intended
board hosts a Lattice ECP5-85F/44F FPGA as an open-toolchain evaluator fabric
and an RP2350 microcontroller as the Southbridge for SPI fallback, PIO parallel
transport, SD card hydration, and USB CDC telemetry.

The board implements a **point-symmetric hexagonal layout** with equalized
25.0 mm radial trace lengths to 12 processing element nodes, minimizing clock
skew without serpentine tuning. The architecture mirrors the structural
efficiency of the Isotropic Vector Matrix (IVM) defined by R. Buckminster Fuller,
translated into defensively designed PCB constraints using KiCad. The exact
KiCad file-version target is still pending because the current generated files
use newer file versions than the original KiCad 8 target.

## 3. Functional Summary

- **Compute:** Lattice ECP5-85F/44F evaluator profile for RPLU v2 table
  hydration, one shared M31 datapath, live Thimble-Pade evaluation over A31,
  and SPI-visible golden-trace readback. Full integrated SPU-13 safety images
  remain Artix-7 200T / Kintex-class targets.
- **Bridge:** RP2350 microcontroller with SPI recovery/control link, reserved
  8-bit PIO/DMA parallel data plane, USB CDC, and microSD host.
- **Memory:** Dual SPI flash (bitstream + RPLU tables), external microSD slot.
- **I/O:** PMOD headers, USB-C (serial/JTAG), UART telemetry at 115,200 baud.
- **Toolchain:** Fully open-source — Yosys + Project Trellis + nextpnr-ecp5.

## 4. Licensing

| Layer | License | File |
|:---|:---|:---|
| Hardware RTL (Verilog) | CERN-OHL-W-2.0 | `hardware/` |
| Board Design (KiCad) | CERN-OHL-W-2.0 | `hardware/pcb/` |
| Software/Firmware (Python, C) | MIT | `software/` |
| Documentation | CC0 1.0 | `docs/`, `knowledge/` |

## 5. Attribution & Third-Party IP

The SPU-13 project builds on prior art published under permissive open licenses:

- **R. Buckminster Fuller** (1975) — Synergetics: IVM geometry — Public Domain
- **Kirby Urner, Tom Ace** (1997) — Quadray coordinates — Public Domain
- **Norman J. Wildberger** (2005) — Rational Trigonometry — CC BY-NC-ND 3.0
- **Andy Ross Thomson** (2026) — Spread-Quadray Rotors — CC BY 4.0
- **Leo Murillo** (2026) — K³ = −K cubic identity — Zenodo (Open Access)

Full credits: `docs/ATTRIBUTION.md`

## 6. Available Files for Certification

- [ ] KiCad source files: `hardware/pcb/spu13_ecp5_carrier.kicad_sch`,
      `hardware/pcb/spu13_ecp5_carrier.kicad_pcb` exist, but the current
      generated files fail ERC/DRC, use newer KiCad file versions than the
      original KiCad 8 target, and are not a complete ECP5 carrier design.
- [x] Board design generation script: `tools/gen_kicad_layout.py`
- [x] Physical routing simulation: `tools/simulate_synergetic_routing.py`
- [x] Test coupon suite: `tools/pcb_coupons/`
- [x] OpenEMS simulation: `tools/pcb_coupons/generate_openems_coupon.py`
- [x] Board spec: `hardware/docs/ecp5_oshwa_carrier_spec.md`
- [x] Current audit: `hardware/docs/ecp5_oshwa_deliverable_audit.md`
- [x] Southbridge transport plan: `hardware/docs/parallel_transport_plan.md`
- [x] EE handoff draft: `docs/ee_handoff.md`
- [x] Build/bring-up guide: `docs/build_and_bringup_guide.md`
- [x] Toolchain setup: `docs/toolchain_setup.md`
- [x] Top-level README with hardware architectural overview
- [x] Contributor guidelines with DCO sign-off: `CONTRIBUTING.md`

## 7. Production Dependencies

The following components are selected from global open distributors:

| Component | Part Number | Distributor |
|:---|:---|:---|
| ECP5-85F FPGA | LFE5UM-85F-8BG381C | DigiKey, Mouser, LCSC |
| RP2350 MCU | RP2350 (QFN60) | Pimoroni, Adafruit (RP2350-Zero) |
| SPI Flash (config) | W25Q128JVSQ (SOIC-8) | DigiKey, Mouser, LCSC |
| SPI Flash (RPLU) | W25Q128JVSQ (SOIC-8) | DigiKey, Mouser, LCSC |
| microSD Socket | 112A-TAAR-R03 (push-push) | DigiKey, Mouser, LCSC |
| LDO Regulator | AP2112K-3.3TRG1 (SOT-23-5) | DigiKey, Mouser, LCSC |
| Decoupling (0402) | 100nF / 10μF multi-layer ceramic | DigiKey, Mouser, LCSC |

## 8. Known Limitations (Filed for Open Disclosure)

1.  **KiCad design incomplete:** The current schematic/PCB package is a
    generated concept artifact. It fails KiCad ERC/DRC and must not be used for
    fabrication until the audit blockers are resolved.
2.  **Physical validation pending:** The point-symmetric trace layout and simulation
    skew metrics (0.0 ps geometric skew @ 166.67 ps time-of-flight) have not yet
    been measured on fabricated hardware. They are structural EDA models under an
    idealized ε_r ≈ 4.0 dielectric model pending VNA/TDR characterization.
3.  **OpenEMS coupling:** The test coupon simulation scripts assume OpenEMS (or an
    equivalent Octave/MATLAB solver) is available. No dedicated license required.
4.  **PCB coupon fabrication:** The test coupons for Sierpinski and 60° routing
    validation have not yet been sent to a fab house.
5.  **Not safety-certified:** This board is an experimental research and
    development platform. It is not certified for safety-critical, medical,
    automotive, or aerospace control applications.
