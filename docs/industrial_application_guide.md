# Industrial Application Guide: SPU Sovereign Gateway
**Target Hardware:** Colorlight 5A-75B v8.2 (Lattice ECP5-25F)

## Overview
The Colorlight 5A-75B is a high-density I/O platform designed for LED control, but its **56 buffered outputs** and **dual Gigabit Ethernet** make it a formidable platform for low-cost industrial automation. When integrated with the SPU Sovereign Cluster, it transforms into an autonomous "Industrial Gateway" for motion control, distributed sensing, and PLC logic.

---

## 1. Hardware Interface Architecture

### HUB75 Pinout Mapping
The 5A-75B provides 8 HUB75 connectors (J1-J8). Each connector has its own 74HC245 buffer.

| SPU Peripheral | Pin Assignment (HUB75) | Industrial Use Case |
| :--- | :--- | :--- |
| **Motion Axis 0-7** | R1, G1 (Pin 1, 2) | Step / Direction pairs for 8 Steppers |
| **PWM Output 0-7** | B1, R2 (Pin 3, 5) | Servo Speed / Heater Control |
| **Serial Bus** | G2, B2 (Pin 6, 7) | Modbus RTU / RS485 expansion |
| **Sync Clock** | LAT, CLK (Pin 14, 13) | Global strobe / Synchronized I/O |

> [!WARNING]
> **Output-Only Buffers:** By default, all HUB75 pins are powered by 74HC245 buffers configured as outputs. You **cannot** use these for input sensors (limit switches, encoders) without hardware modification. 
> **For Inputs:** Use the JTAG/PMOD header pins or modify the board to bypass/replace select buffers.

---

## 2. Industrial Logic (PLC Sentinel)
The SPU-4 clusters can be configured in **PLC Mode**, where they execute a fixed-cycle logic loop ("The Pulse") to manage safety interlocks and discrete I/O state machines.

- **Scan Time:** < 50µs (Deterministic).
- **Distributed PLC logic**: 61.44 kHz scan cycles for safety interlocks.
- **Hybrid I/O**: High-speed outputs via HUB75, sensor inputs via JTAG/PMOD header.
- **Etherbone Integration**: Remote monitoring of industrial status over Gigabit Ethernet.
- **Ethernet Backbone:** Distributed nodes can share "The Whisper" (a low-latency pulse) to synchronize I/O across the factory floor.

---

## 3. Hybrid I/O Strategy
In this mode, we utilize the unbuffered JTAG/PMOD headers for sensor inputs while using the buffered HUB75 connectors strictly for high-power outputs (Motors/Solenoids).

*   **Inputs (Sensors)**: Break out from the 10-pin JTAG header (TCK, TMS, TDI pins).
*   **Outputs (Controllers)**: Drive via HUB75 J1-J8.
*   **Boot Mode**: Configure FPGA to boot from SPI Flash (ROM) for autonomous operation.

---

## 4. Motion Control Profiles
The `spu_industrial_io.v` module provides:
1.  **High-Freq PWM:** 20kHz to 1MHz for precise motor current control.
2.  **Pulse/Dir Engine:** 32-bit position counters with acceleration/deceleration ramping.
3.  **TDM Coordination:** The SPU-13 Mother calculates the next geodesic move and broadcasts it to the SPU-4 satellites for execution.

---

## 4. Deployment Pathways

### Pathway A: Non-Destructive (Off-the-shelf)
- Use HUB75 pins for outputs only.
- Connect SD card and Inputs via the JTAG/PMOD header.
- **Best for:** Low-cost CNC masters or distributed LED/Lighting controllers.

### Pathway B: Hardened Industrial (Modified)
- Desolder 74HC245 buffers.
- Solder 0-ohm bridge resistors or replace with 74LVC245 (3.3V) for bidirectional I/O.
- **Best for:** Full PLC/CNC replacements requiring multiple sensor inputs.
