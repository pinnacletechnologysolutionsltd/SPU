# SPU-13 ECP5-85F Power Tree & PDN Analysis

**Status:** Concept / OpenEE handoff document
**Simulator:** ngspice (open-source SPICE)
**Board:** SPU-13 ECP5 OSHWA Carrier
**FPGA:** Lattice ECF5-85F CABGA381
**Target:** Input 5V DC (USB-C or external) → multi-rail regulated delivery

---

## 1. Power Rail Requirements

| Rail | Voltage | Tolerance | Typical Current | Max Current | Ripple (pk-pk) | Notes |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| VCC_CORE | 1.1V | ±30 mV | 800 mA | 1.5 A | < 10 mV | ECP5 core, highest load |
| VCC_IO_3V3 | 3.3V | ±165 mV | 200 mA | 500 mA | < 30 mV | Bank 0, 2, 3 (SPI, GPIO, PMOD) |
| VCC_IO_1V8 | 1.8V | ±90 mV | 100 mA | 200 mA | < 20 mV | Bank 1 (PLL reference, configuration) |
| VCC_PLL | 2.5V | ±125 mV | 20 mA | 50 mA | < 5 mV | Clean analog supply for PLLs |
| VCC_BATT | 3.0V | ±150 mV | 1 µA | 10 µA | relaxed | Backup battery for config RAM |
| VCC_RP2350 | 3.3V | ±165 mV | 50 mA | 150 mA | < 50 mV | RP2350 southbridge |
| VCC_SD | 3.3V | ±165 mV | 50 mA | 100 mA | < 50 mV | microSD slot |
| VCC_FLASH | 3.3V | ±165 mV | 10 mA | 30 mA | < 50 mV | SPI flash (config + RPLU tables) |

**Total estimated load:** ~1.23 A typical, ~2.5 A peak on 5V input.

---

## 2. Power Architecture

```
USB-C (5V, 3A)
  │
  ├─ [LDO] AP2112K-3.3 ── 3.3V rail ──┬─ VCC_IO_3V3 (ECP5 banks 0,2,3)
  │     3.3V, 600 mA                    ├─ VCC_RP2350 (QFN60)
  │     ˄ fixed LDO                     ├─ VCC_SD (microSD)
  │     ˄ low-noise                     ├─ VCC_FLASH (SPI config + table)
  │                                     └─ VCC_BATT via diode-OR to CR2032
  │
  ├─ [Buck] TPS62082 ── 1.1V rail ── VCC_CORE (ECP5 core)
  │     1.1V, 2.0 A
  │     ˄ high-efficiency synchronous buck
  │     ˄ 2 MHz switching frequency (above SPI/audio bands)
  │
  ├─ [Buck] TPS62232 ── 1.8V rail ── VCC_IO_1V8 (ECP5 bank 1)
  │     1.8V, 500 mA
  │
  └─ [LDO] LP5907-2.5 ── 2.5V rail ── VCC_PLL (ECP5 PLL)
        2.5V, 250 mA
        ˄ ultra-low-noise LDO post-filter
        ˄ dedicated ferrite bead + 10µF + 100nF pi-filter
```

### 2.1 Sequencing
ECP5 requires VCC_CORE to ramp before or simultaneously with VCC_IO:
- Assert FPGA PROGRAM# low until VCC_CORE and VCC_IO_3V3 are valid
- Use a reset supervisor (e.g., TPS3808G33) on 3.3V rail to hold FPGA_CONFIG# low
- RP2350 can reset FPGA via GPIO if needed (existing SPI CS# idle-high path)

### 2.2 Decoupling Network (per rail)

| Rail | Bulk (10-22µF) | Mid (1-4.7µF) | HF (100nF) | Placement |
|:---|:---:|:---:|:---:|:---|
| VCC_CORE | 2 × 22µF 0805 | 2 × 4.7µF 0603 | 8 × 100nF 0402 | Under BGA, inside via ring |
| VCC_IO_3V3 | 1 × 22µF 0805 | 1 × 4.7µF 0603 | 4 × 100nF 0402 | Near each IO bank |
| VCC_IO_1V8 | 1 × 10µF 0805 | 1 × 4.7µF 0603 | 2 × 100nF 0402 | Near bank 1 |
| VCC_PLL | — | 1 × 4.7µF 0603 | 1 × 100nF 0402 | Directly at PLL pin, ferrite bead before |

---

## 3. ngspice PDN Simulation

Simulate the target impedance of the VCC_CORE PDN from 100 kHz to 10 MHz.

### 3.1 Run the simulation

```bash
ngspice -b tools/pdn_simulation.cir
```

### 3.2 Expected output

The simulation produces `pdn_z11.txt` (impedance magnitude vs frequency).
Target: **Z_PDN ≤ 0.15 Ω** from 100 kHz to 10 MHz for VCC_CORE.

### 3.3 Interpretation

| Frequency Band | Dominant Element | Target Z |
|:---|:---|:---:|
| < 100 kHz | Voltage regulator | < 1 Ω |
| 100 kHz – 1 MHz | Bulk caps (22µF MLCC) | < 0.15 Ω |
| 1 MHz – 10 MHz | Mid + HF caps (4.7µF + 100nF) | < 0.15 Ω |
| > 10 MHz | PCB plane capacitance + package | < 0.1 Ω (estimated) |

If Z_PDN exceeds 0.15 Ω in any band:
- Add more paralleled MLCCs in the affected frequency range
- Reduce mounting inductance (shorter via distance to BGA balls)
- Increase PCB plane capacitance (thinner dielectric between power/ground)

---

## 4. PCB PDN Layout Constraints

To meet the target impedance:

1. **BGA via-in-pad** — Place 100nF 0402 caps on bottom layer directly opposite BGA power vias, with 0.3 mm via-in-pad to minimize loop inductance.
2. **Solid power planes** — In1.Cu = VCC_CORE (1.1V), In2.Cu = GND. No splits or cutouts under the FPGA.
3. **Via stitching** — Place GND vias within 0.5 mm of every power via to minimize current loop area.
4. **Bulk caps on edges** — Place 22µF 0805 caps within 10 mm of the FPGA power balls.
5. **Ferrite bead for PLL** — Use BLM18PG221SN1 (220Ω at 100 MHz, 500 mA) to isolate the VCC_PLL rail from digital noise.

---

## 5. Regulator BOM

| Ref | Part | Type | Package | Input | Output | Max I |
|:---|:---|:---|:---|:---|:---|:---:|
| U5 | AP2112K-3.3 | LDO | SOT-23-5 | 5V USB | 3.3V | 600 mA |
| U6 | TPS62082 | Sync Buck | QFN-8 3×3 | 5V USB | 1.1V | 2.0 A |
| U7 | TPS62232 | Sync Buck | QFN-8 3×3 | 5V USB | 1.8V | 500 mA |
| U8 | LP5907-2.5 | LDO | SOT-23-5 | 3.3V | 2.5V | 250 mA |
| U9 | TPS3808G33 | Supervisor | SOT-23-5 | 3.3V | RESET# | — |

**Alternate (simpler):** Replace TPS62082 buck with LTM8065 µModule (4A, 5V→1.1V) if layout density permits — reduces external inductor/cap count.
