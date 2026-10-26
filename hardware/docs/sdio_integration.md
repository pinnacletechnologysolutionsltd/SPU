SDIO Integration — microSD slot & RP2350 wiring spec

Overview
--------
This document specifies the electrical, PCB routing, and firmware requirements for adding a micro‑SD slot in 4‑bit SDIO mode to the main board and wiring it to the RP2350 controller. SDIO (4‑bit) is REQUIRED for GhostOS large ROM/LUT loads and high‑throughput ROM streaming. The SD slot also supports SPI mode as a fallback.

Key signals
-----------
- VCC_3V3, GND
- SD_CLK (clock)
- SD_CMD (command)
- SD_DAT0, SD_DAT1, SD_DAT2, SD_DAT3 (data lines)
- CD (card detect, optional; active low preferred)
- WP (write protect, optional)

RP2350 (suggested) pin mapping example
--------------------------------------
(Note: these are recommended defaults; final pinout depends on board routing)
- SD_CLK -> GP10
- SD_CMD -> GP11
- SD_DAT0 -> GP9
- SD_DAT1 -> GP8
- SD_DAT2 -> GP7
- SD_DAT3 -> GP6
- SD_CD  -> GP5
- SD_WP  -> GP4
- SD_VCC -> 3.3V (same domain as RP2350)

Electrical recommendations
--------------------------
- Voltage domain: entire SD interface must be 3.3V. If any host runs at a different voltage, use proper bidirectional level shifters (FET-based) or TXS* series.
- Pull-ups: 10 kΩ pull-ups to 3.3V on CMD and DAT[0..3] as recommended by SD specification. For CMD and DAT lines consider 10k–47k depending on bus capacitance.
- Series damping resistors: 22–33 Ω series resistors near the SD host on SD_CLK, SD_CMD and each DAT line to reduce ringing.
- Decoupling: 100 nF + 1 µF decoupling close to the socket VCC pin.
- ESD protection: small TVS diodes on the CMD/DAT lines referenced to 3.3V.
- Card detect / WP: route these to GPIOs with optional pull-ups; CD active‑low preferred.

Layout & routing guidelines
---------------------------
- Place the microSD socket near the board edge to ease insertion.
- Keep SD_CLK as the shortest, cleanest route to the host; avoid stubs and minimize vias.
- Match DAT0..DAT3 trace lengths to within a few millimetres (2–5 mm) where possible. CMD may be slightly shorter than DAT lines.
- Use series resistors near the host to damp reflections and avoid placing them near the socket if possible.
- Avoid running the SD traces over splits in the ground plane. Keep continuous ground under the route where feasible.
- Use 50 Ω controlled impedance if the board stackup supports it, otherwise focus on short routes and clean return paths.

BOM (recommended)
-------------------
- MicroSD push‑push socket (surface mount)
- TVS diodes for ESD protection on data/command lines
- 4 × 10 kΩ pull-up resistors
- 4 × 22–33 Ω series resistors
- 1 × 100 nF + 1 × 1 µF decoupling capacitors
- Optional: FET-based bidirectional level shifter (e.g., for 1.8V host domains)

Firmware & driver expectations
------------------------------
- Driver must initialize SDIO 4‑bit mode (preferred) and support high throughput DMA transfers for large LUT/ROM streaming.
- Provide an atomic staging area in flash/SD: stage files, verify checksum, then commit (rename or update pointer to avoid partial updates).
- Provide a robust fallback path to SPI mode when SDIO is unavailable.
- Expose an API for GhostOS/firmware to read blocks, stream files, enumerate directories, and perform checksum reads.

Validation checklist
--------------------
- Card insert/remove detection works and the driver handles hot‑insertion gracefully.
- Mount and read a known test file and verify its checksum.
- Run a throughput test (4‑bit SDIO) and confirm bandwidth near expected (board/SD card dependent).
- Verify power consumption, thermal profile, and EMI signature during sustained reads.

Notes
-----
- SDIO 4‑bit requires careful board routing to reach high throughput; if layout constraints prevent matching, use SPI mode and document the performance tradeoffs.
- Provide jumper or solder‑bridge options to route SD signals to RP2040 for debug/visualizer flows if needed.

