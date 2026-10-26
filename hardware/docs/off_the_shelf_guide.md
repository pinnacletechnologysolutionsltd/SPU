# 🛠️ SPU Sovereign Cluster: Off-the-Shelf Deployment Guide (Colorlight 5A-75B)

This guide explains how to deploy the SPU Sovereign Cluster onto a stock Colorlight 5A-75B (V7/V8) board without any soldering or destructive hardware modifications.

## 🔌 1. The "No-Solder" JTAG-to-SD Bridge

We use the JTAG header as a general-purpose SPI port for the SD Card. This keeps the HUB75 ports free for 5V high-power outputs.

### Pinout (JTAG Header to SD Card PMOD)
| JTAG Pin | FPGA Pin | SD Card Port |
| :--- | :--- | :--- |
| **TDI** | J32 | **MOSI** |
| **TDO** | J30 | **MISO** |
| **TCK** | J27 | **SCK** |
| **TMS** | J31 | **CS** |
| **VCC (3.3V)** | J33 | **VCC** |
| **GND** | J34 | **GND** |

> [!NOTE]
> Use standard female-to-female jumper wires to connect your SD Card PMOD or adapter to these pins.

---

## 💾 2. Preparing the Internal Flash (ROMs)

The SPU "Inhale" logic expects the Thomson ROMs and RPLU coefficients to be stored in the onboard 4MB SPI Flash starting at the **1MB mark (0x200000)**.

### Merging Bitstream and ROMs
Use the following command to combine the FPGA bitstream with the SPU ROM blob:

```bash
# 1. Generate the raw bitstream
ecppack --compress --freq 38.8 build/ecp5_25f/ecp5_25f.config build/ecp5_25f/spu_main.bit

# 2. Append ROMs at 2MB offset (Safe region)
dd if=hardware/roms/spu_rom_bundle.bin of=build/ecp5_25f/spu_main.bit bs=1k seek=2048 conv=notrunc
```

### Flashing the Board
Use `openFPGALoader` to write the combined image:

```bash
openFPGALoader -b 5a-75b --write-flash build/ecp5_25f/spu_main.bit
```

---

## 🏔️ 3. Memory Manifold Strategy

*   **Internal Flash**: Stores immutable "Sovereign Laws" (Primes, Coefficients).
*   **Onboard SDRAM**: Provides 8MB of high-speed manifold expansion for SPU-13 satellites.
*   **SD Card**: Used for massive datasets, logging, and application-level persistent storage.

---

## 🏁 4. Verification

1.  **Red LED (T6)**: Should pulse twice if the Flash "Inhale" was successful.
2.  **Heartbeat**: The LED will then begin a slow "Piranha Pulse" indicating the SPU cluster has ignited and is in a stable state of Rational Proprioception.
