# SPU-13 ECP5 Evaluation Carrier Board Specification v2

**Status:** Evaluation-architecture specification. Not fab-ready.
**Platform:** Lattice ECP5-85F / ECP5-44F (CABGA381 or CABGA256)
**Southbridge:** Raspberry Pi RP2350 (single USB-C debug path)
**Debug path:** RP2350 USB-C only — no FTDI, no separate JTAG pod, no dedicated UART bridge
**License:** CERN-OHL-W-2.0

---

## 1. Design Philosophy

The RP2350 southbridge handles all debug and programming through its single USB-C port:

| Function | Path | Details |
|:---|:---|:---|
| **Bitstream loading** | USB → RP2350 → ECP5 SSPI | RP2350 SPI0 or PIO bit-bangs ECP5's slave-SPI configuration port |
| **UART telemetry** | USB → RP2350 CDC → ECP5 SPI | Telemetry frames forwarded over the existing 0xAC/0xA0 SPI protocol |
| **JTAG debugging** | USB → RP2350 PIO → ECP5 JTAG | PIO bit-bangs TCK/TDI/TDO/TMS (same approach as RP2040 DirtyJTAG, already proven on Wukong) |
| **RPLU table hydration** | USB → RP2350 → SD or direct | microSD slot or host-pushed binary over USB MSC |
| **Power sequencing** | RP2350 GPIO → ECP5 PROGRAM# | RP2350 holds ECP5 in reset until all rails are stable |

This eliminates the FT2232HL entirely and removes the need for a separate UART-USB bridge or JTAG programmer.

---

## 2. ECP5-85F Support Circuits

### 2.1 Configuration Mode — Master SPI

```
MODE[2:0] = 001  (Master SPI: ECP5 reads bitstream from configuration flash)
  MODE2 = GND (10k pull-down)
  MODE1 = GND (10k pull-down)
  MODE0 = VCC_3V3 (10k pull-up)
```

### 2.2 Configuration Flash (U3 — W25Q128JVSQ)

| ECP5 function | ECP5 ball | Flash pin | Notes |
|:---|:---|:---|:---|
| CCLK | — | CLK | ECP5 drives clock in master mode |
| CSO | — | CS# | ECP5 asserts CS# to start read |
| MOSI/SIS1 | — | DI | Data to flash |
| MISO/SIS0 | — | DO | Data from flash |
| PROGRAM# | — | — | 10k pull-up to 3.3V, also driven by RP2350 GPIO |
| DONE | — | — | LED indicator + pull-up to 3.3V |
| INIT# | — | — | Pull-up to 3.3V |

Ball numbers: **to be assigned by EE from LFE5UM-85F CABGA381 datasheet.** Recommended bank: Bank 0 (VCCIO0 = 3.3V).

### 2.3 Slave-SPI Configuration (RP2350 -> ECP5)

For RP2350-pushed bitstream loading (SRAM or flash programming), a separate set of GPIOs on the RP2350 connect to the ECP5's slave-SPI configuration port:

| Signal | RP2350 GPIO | ECP5 function | Notes |
|:---|:---|:---|:---|
| FPGA_CCLK | RP2350 GPx | CCLK | RP2350 drives clock during slave config |
| FPGA_MOSI | RP2350 GPx | MOSI/SIS1 | RP2350 pushes bitstream data |
| FPGA_MISO | RP2350 GPx | MISO/SIS0 | ECP5 sends status/CRC |
| FPGA_CS# | RP2350 GPx | CS#/CSIN | Active-low chip select |
| FPGA_PROGRAM# | RP2350 GPx | PROGRAM# | RP2350 can force reconfiguration |
| FPGA_INIT# | — | INIT# | Open-drain; RP2350 monitors |
| FPGA_DONE | — | DONE | Open-drain; RP2350 monitors |

### 2.4 Clock Input

| Signal | Value | ECP5 pin type | Notes |
|:---|:---|:---|:---|
| CLK_50M | 50 MHz | GPLL input (bank 2 or 5) | 50 MHz crystal oscillator module, 3.3V |
| CLK_12M | 12 MHz | GPIO or PLL input | Optional secondary clock |

Ball numbers: **to be assigned by EE.**

### 2.5 JTAG (RP2350 PIO bit-bang)

| Signal | RP2350 GPIO | ECP5 ball |
|:---|:---|:---|
| TCK | RP2350 PIO GPx | ECP5 TCK |
| TDI | RP2350 PIO GPx | ECP5 TDI |
| TDO | RP2350 PIO GPx | ECP5 TDO |
| TMS | RP2350 PIO GPx | ECP5 TMS |

Use same RP2040 DirtyJTAG pin order (`0:TDI 1:TMS 2:TCK 3:TDO`) for firmware compatibility.

### 2.6 I/O Bank Voltage Assignment

| Bank | Voltage | Signals |
|:---|:---:|:---|
| Bank 0 | 3.3V | Configuration flash, MODE straps, PROGRAM#, DONE |
| Bank 1 | 1.8V | Optional: PLL reference, SDRAM (if fitted) |
| Bank 2 | 3.3V | 50 MHz clock input, general purpose |
| Bank 3 | 3.3V | SPI southbridge, UART telemetry |
| Bank 4 | 3.3V | PIO parallel bus (DATA[7:0], STROBE, READY, DIR) |
| Bank 5 | 3.3V | JTAG, general purpose |

---

## 3. RP2350 Support Circuits

### 3.1 Boot Mode

| Signal | RP2350 pin | Connection |
|:---|:---|:---|
| BOOT (GPIO8) | QFN-60 pin 29 | 10k pull-up to 3.3V + tactile switch to GND |
| RUN | QFN-60 pin 30 | 10k pull-up to 3.3V + optional tactile switch to GND |

Press BOOT during USB plug-in for UF2 mass-storage bootloader mode.

### 3.2 USB

| Signal | RP2350 pin | Connection |
|:---|:---|:---|
| USB_D+ | QFN-60 pin 36 | USB-C J1 DP with 27 ohm series |
| USB_D- | QFN-60 pin 37 | USB-C J1 DN with 27 ohm series |
| VBUS | QFN-60 pin 35 | USB-C VBUS via voltage divider to GPIO24 |
| GPIO24 | QFN-60 pin 38 | VBUS detect (5V -> 2x 10k divider -> 2.5V) |

USB-C connector: GCT USB4110-GF-A (16-pin, through-hole, CC resistors for 5V/3A).

### 3.3 Crystal

| Signal | RP2350 pin | Component |
|:---|:---|:---|
| XI | QFN-60 pin 48 | 12 MHz crystal + 18pF load cap to GND |
| XO | QFN-60 pin 49 | 12 MHz crystal + 18pF load cap to GND |

Crystal: 12 MHz parallel-cut, 20pF CL, ±50ppm (ECS-120-20-30B-TR).
**Not** a canned oscillator. Two 18pF ±5% COG/NP0 0402 caps required.

### 3.4 ADC Reference

| Signal | RP2350 pin | Connection |
|:---|:---|:---|
| ADC_VREF | QFN-60 pin 42 | 3.3V via ferrite bead + 10uF + 100nF |

### 3.5 SWD Debug (optional, for firmware development)

| Signal | RP2350 pin | Debug header |
|:---|:---|:---|
| SWCLK | QFN-60 pin 21 | 3-pin header or test points |
| SWDIO | QFN-60 pin 22 | 3-pin header or test points |

---

## 4. Bus Lane: SPI Southbridge (RP2350 -> ECP5)

### 4.1 Pin Assignments

| Signal | RP2350 GPIO | ECP5 ball | ECP5 bank | Series R | Notes |
|:---|:---|:---|:---:|:---:|:---|
| SPI_CS# | GP1 | TBD by EE | Bank 3 | 33 ohm near FPGA | Pull-up to 3.3V on ECP5 side |
| SPI_SCK | GP2 | TBD by EE | Bank 3 | 22 ohm near RP2350 | Matched to 50 ohm trace |
| SPI_MOSI | GP3 | TBD by EE | Bank 3 | 22 ohm near RP2350 | |
| SPI_MISO | GP0 | TBD by EE | Bank 3 | 33 ohm near FPGA | RP2350 input |

SPI mode: 0 (CPOL=0, CPHA=0), 2-12 MHz.

### 4.2 Termination Strategy

| Net | Driver | R_series | Placement | R_pull |
|:---|:---|:---:|:---|:---:|
| SPI_SCK | RP2350 | 22 ohm | within 5mm of RP2350 pin | — |
| SPI_MOSI | RP2350 | 22 ohm | within 5mm of RP2350 pin | — |
| SPI_MISO | ECP5 | 33 ohm | within 5mm of ECP5 ball via | — |
| SPI_CS# | RP2350 | — | — | 10k to 3.3V |

---

## 5. Bus Lane: PIO Parallel (RP2350 -> ECP5)

### 5.1 Pin Assignments (Tentative)

| Signal | RP2350 GPIO | ECP5 ball | ECP5 bank | Series R | Notes |
|:---|:---|:---|:---:|:---:|:---|
| PIO_D0 | GP4 | TBD by EE | Bank 4 | 22 ohm | Contiguous GPIO block |
| PIO_D1 | GP5 | TBD by EE | Bank 4 | 22 ohm | |
| PIO_D2 | GP6 | TBD by EE | Bank 4 | 22 ohm | |
| PIO_D3 | GP7 | TBD by EE | Bank 4 | 22 ohm | |
| PIO_D4 | GP8 | TBD by EE | Bank 4 | 22 ohm | |
| PIO_D5 | GP9 | TBD by EE | Bank 4 | 22 ohm | |
| PIO_D6 | GP14 | TBD by EE | Bank 4 | 22 ohm | |
| PIO_D7 | GP15 | TBD by EE | Bank 4 | 22 ohm | |
| PIO_STROBE | GP16 | TBD by EE | Bank 4 | 22 ohm | |
| PIO_READY | GP17 | TBD by EE | Bank 4 | 22 ohm | Input to RP2350 |
| PIO_DIR | GP18 | TBD by EE | Bank 4 | 22 ohm | 1=FPGA drives data |

Route DATA[7:0] with matched skew < 0.5 ns. GND guard traces between adjacent lanes.

---

## 6. Evaluation Circuits (On-Board)

### 6.1 Status Indicators

| LED | Color | Driven by | Series R | Purpose |
|:---|:---:|:---|:---:|:---|
| LED_DONE | Green | ECP5 DONE pin | 330 ohm | FPGA configured |
| LED_PWR | Green | VCC_3V3 rail | 1k | Board powered |
| LED_ACT | Red | RP2350 GPIO | 330 ohm | RP2350 activity/heartbeat |
| LED_FAULT | Red | ECP5 GPIO or open-drain | 330 ohm | Error indicator |

### 6.2 User Input

| Item | Connection | Function |
|:---|:---|:---|
| BOOT button | RP2350 GPIO8 to GND | UF2 bootloader entry |
| RUN button | RP2350 RUN to GND | Hard reset RP2350 |
| FPGA_RST button | ECP5 PROGRAM# to GND | Force FPGA reconfiguration |
| 4-pin DIP switch | 4x RP2350 GPIO with pull-ups | Mode selection for evaluation |

### 6.3 Test Points

| TP | Signal | Use |
|:---|:---|:---|
| TP_VCC_CORE | VCC_CORE (1.1V) | Measure core voltage, connect scope |
| TP_VCC_3V3 | VCC_IO (3.3V) | Measure I/O voltage |
| TP_GND | GND | Scope ground reference |
| TP_SPI_CS | SPI_CS# | SPI protocol analysis |
| TP_SPI_SCK | SPI_SCK | SPI clock measurement |
| TP_PIO_STB | PIO_STROBE | PIO bus timing measurement |

### 6.4 microSD Slot

| Signal | RP2350 | microSD | Pull-up |
|:---|:---|:---:|:---:|
| SD_CLK | GP10 | CLK | — |
| SD_CMD | GP11 | CMD | 10k to 3.3V |
| SD_DAT0 | GP12 | DAT0/MISO | 10k to 3.3V |
| SD_CS# | GP13 | DAT3/CS# | 10k to 3.3V |

---

## 7. Power Architecture

See `hardware/docs/power_tree.md` for full analysis.

| Rail | Regulator | Voltage | Max I |
|:---|:---|:---:|:---:|
| VCC_CORE | TPS62082 (buck) | 1.1V | 2.0 A |
| VCC_3V3 | AP2112K-3.3 (LDO) | 3.3V | 600 mA |
| VCC_1V8 | TPS62232 (buck) | 1.8V | 500 mA |
| VCC_PLL | LP5907-2.5 (LDO) | 2.5V | 250 mA |

Sequencing: RP2350 GPIO holds ECP5 PROGRAM# low until VCC_CORE and VCC_3V3 are stable.

---

## 8. BOM Changes from v1

| Change | Part | Reason |
|:---|:---|:---|
| REMOVE | U6 = FT2232HL | RP2350 USB handles all debug |
| ADD | Tactile switch ×2 | BOOT + RUN buttons |
| ADD | 18pF 0402 COG ×2 | RP2350 crystal load caps |
| ADD | 27 ohm 0402 ×2 | USB D+/D- series termination |
| ADD | LED 0603 ×3 | DONE/PWR/ACT indicators |
| ADD | 4-pin DIP switch | Evaluation mode select |

---

## 9. Ball Assignment Notes for EE

The ECP5-85F CABGA381 balls must be assigned from the Lattice datasheet
(`FPGA_DS_02012_2_4_ECP5_ECP5G_Family_Data_Sheet-1022822.pdf` in repo root).
The Lattice hardware checklist (`FPGA-TN-02038-2-0-ECP5-and-ECP5-5G-Hardware-Checklist.pdf`)
covers decoupling, configuration, and PCB design rules.

A partial pin constraints file with placeholder assignments exists at
`hardware/boards/ecp5_85k/spu_ecp5_85k.cst`. Replace every `# TBD by EE` comment
with real ball coordinates from the datasheet.

The build script `hardware/boards/ecp5_85k/build_ecp5_85k.sh` runs the full
yosys + nextpnr-ecp5 + ecppack flow for the `LFE5UM5G-85F` in CABGA381.
