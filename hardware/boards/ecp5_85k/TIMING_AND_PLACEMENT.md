# Historical Note

This file contains early ECP5-85F timing and placement notes. For current
measured build status, use `docs/ecp5_85k_curated_source_strategy.md`. The
current executable flow is `build_ecp5_85k_minimal.sh`, which uses
`nextpnr-ecp5 --um5g-85k --package CABGA381` and passes P&R/bitstream
packaging for the minimal placeholder target.

# ECP5-85K Minimal Spin — Timing & Placement Constraints

**Date:** 2026-07-05
**Target:** SPU-13 + RPLU 2.0 on ECP5-85F (CABGA381)

---

## Overview

This document guides P&R iteration for the ECP5 minimal spin, addressing potential routing congestion, timing failures, and resource conflicts.

## 1. Target Specifications

| Parameter | Value | Justification |
|---|---|---|
| **Clock frequency** | 50 MHz | ECP5-85 grade 8 supports 50+ MHz with margin |
| **Clock source** | 50 MHz crystal on sys_clk (pin E2) | CABGA381 config pin; requires PULL_MODE=NONE |
| **Internal clocks** | clk_12mhz (÷4), clk_1mhz (÷50) | Derived from 50 MHz via simple divider |
| **ALU pipeline** | 6–8 cycles per rotation | TDM ALU Q12 scaling (input Q12×Q12 → Q24 → Q12) |
| **Rotor vault** | 6 cycle latency | Pell orbit lookup + DSP multiply |
| **Device utilization** | <60% LUT, <80% slice | Healthy margin for debug/future enhancements |

---

## 2. Critical Paths & Timing

### Path A: Boot → BRAM Write
```
spu_laminar_boot.sck → SPI state machine → bram_we
Expected latency: ~100 cycles (Flash read overhead)
Slack requirement: >0 ns @ 12 MHz (internal clock, no timing pressure)
```

### Path B: ALU Start → ALU Done (TDM)
```
spu_unified_alu_tdm.start → ROT_S1..S4 → done pulse
Expected latency: 6 cycles (pipelined)
Required slack: >2 ns @ 50 MHz (external clock, but routed internally)
Note: ALU uses 12 MHz internally, but system clock is 50 MHz
```

### Path C: Vault Rotor → ALU
```
spu_rotor_vault.alu_rotor → spu_unified_alu_tdm.{F_rat, F_surd, ...}
Expected latency: 2 cycles (registered output)
Slack: >1 ns @ 12 MHz
```

---

## 3. Known Hotspots (Resource Density)

### 3.1 M31 Multiplier (spu13_m31_multiplier.v, if included in full RPLU2)
- **LUTs:** ~1,200 (16 parallel 32×32 products + Mersenne reduction)
- **DSPs:** 16 (one per partial product)
- **Issue:** Will crowd into a single slice cluster; may trigger congestion
- **Mitigation:** Use `(* keep *)` on multiplier outputs; allow nextpnr to spread across device

### 3.2 BTU Collision Resolver (spu_btu_collision_resolver.v)
- **LUTs:** ~600 (priority encoder 64→6, backlog queue)
- **BRAM:** 2–4 (64-entry queue buffer)
- **Issue:** Distributed throughout device; may conflict with rotor vault BRAM
- **Mitigation:** Place BTU near output registers; keep BRAM entries separate in address space

### 3.3 SOM BMU (`spu_som_bmu.v`, if included)
- **Architecture:** serial scan of the writable prototype BRAM
- **Resources:** use the current synthesis report; the former ~1,400-LUT
  parallel-array estimate described archived RTL
- **Issue:** exact `Q(sqrt(3))` comparison includes wide integer squares
- **Mitigation:** constrain and pipeline only after measuring the canonical
  serial path; do not reintroduce the archived WTA tree implicitly

---

## 4. Placement Constraints (.cst)

The file `spu_ecp5_85k.cst` defines pin assignments. Key lines:

```
# Clock (E2 is special config pin — PULL_MODE=NONE required)
IO_PORT "clk_50m" PULL_MODE=NONE;

# LEDs (active low, different banks to avoid simultaneous switching)
IO_PORT "led[0]" IO_TYPE=LVCMOS33 DRIVE=8;  # L6
IO_PORT "led[1]" IO_TYPE=LVCMOS33 DRIVE=8;  # E8
IO_PORT "led[2]" IO_TYPE=LVCMOS33 DRIVE=8;  # D7

# UART (separate banks to avoid crosstalk)
IO_PORT "uart_tx_telemetry" IO_TYPE=LVCMOS33 DRIVE=8;  # B11
IO_PORT "uart_tx"           IO_TYPE=LVCMOS33 DRIVE=8;  # C3

# SPI Flash J4 (all in one bank for timing coherence)
IO_PORT "flash_cs_o"   IO_TYPE=LVCMOS33 DRIVE=12;  # G10
IO_PORT "flash_clk_o"  IO_TYPE=LVCMOS33 DRIVE=12;  # D10
IO_PORT "flash_mosi_o" IO_TYPE=LVCMOS33 DRIVE=12;  # C10
IO_PORT "flash_miso_i" IO_TYPE=LVCMOS33 DRIVE=4;   # B10
```

**Actions if routing fails:**
1. Check that all I/O lines are in different I/O banks (ECP5-85 has 8 banks; minimal spin uses ~3)
2. If timing slack < -200 ps, increase output DRIVE (12→16) on flash signals
3. If congestion, move SPI signals to opposite side of device (nextpnr usually does this automatically)

---

## 5. Nextpnr Invocation & Tuning

### Standard invocation (from build_ecp5_85k_minimal.sh):
```bash
nextpnr-ecp5 \
    --85k \
    --json build/spu_ecp5_top.json \
    --lpf hardware/boards/ecp5_85k/spu_ecp5_85k.cst \
    --textcfg build/spu_ecp5_top_out.config \
    --freq 50 \
    --speed 8 \
    --device LFE5UM5G-85F
```

### If routing fails:
**Option A: Reduce frequency**
```bash
--freq 40  # Drop to 40 MHz (easier routing, still ~2 GHz instruction throughput)
```

**Option B: More aggressive optimization**
```bash
--seed 1 --seed 2 --seed 3 ...  # Try multiple placement seeds
```

**Option C: Increase effort**
```bash
--placer heap  # Use heap placer (slower but better quality, ~10–30s overhead)
```

### If timing fails (negative slack):
```bash
nextpnr-ecp5 --freq 50 --slack-redist  # Redistribute timing; may help paths
```

---

## 6. Post-P&R Validation

After nextpnr completes successfully:

1. **Check timing report** (embedded in nextpnr output):
   ```
   Slack histogram:
   ...
   Critical path: <module>.<signal> → <module>.<signal> : X.XX ns
   ```
   Require: All slack > 0 ns at 50 MHz (period = 20 ns)

2. **Check utilization** (nextpnr stdout):
   ```
   Device utilisation:
   LUT4: X%
   SLICE: Y%
   DSP48: Z%
   ```
   Target: LUT <60%, SLICE <60%, DSP <50%

3. **Inspect .config output** (binary; readable via ecppack debug):
   ```bash
   ecppack --verbose build/spu_ecp5_top_out.config
   ```
   Expect: ~50 KB config (reasonable for minimal spin; RPLU2 full build ~150 KB)

4. **Generate bitstream**:
   ```bash
   ecppack --compress build/spu_ecp5_top_out.config build/spu_ecp5_top.bit
   ```

---

## 7. Common Issues & Fixes

| Issue | Symptom | Fix |
|---|---|---|
| **Negative timing slack** | nextpnr reports e.g., `-5.2 ns` on critical path | Reduce freq (--freq 40), or add pipeline stage in critical module |
| **Routing congestion** | nextpnr times out after 10 min or reports "routing failed" | Increase effort (--placer heap), try different seed, or reduce freq |
| **Config too large** | Bitstream generation fails or > 200 KB | Check for unintended module instantiations (BRAM bloat) or large memory tables |
| **LEDs don't blink** | No observable pulse on pins L6/E8/D7 | Verify clock is running (measure 50 MHz on pin E2); check reset (pin R1) is deasserted |
| **Flash reads fail** | JEDEC ID readback garbage (not 0xEF4018) | Verify SPI timing (freq, drive, slew); check J4 solder joints; verify flash chip is present |

---

## 8. Resource Budget

Expected resource allocation for minimal spin:

```
┌─────────────────────────────────────────────┐
│ ECP5-85F Resource Budget (SPU-13 + RPLU2)   │
├─────────────────────────────────────────────┤
│ Total LUT4:     11,270 (84K available)       │
│ Usage:          ~6,500 (58%)                 │
│ ├─ ALU (TDM):   ~1,200                       │
│ ├─ Rotor Vault: ~800                         │
│ ├─ Boot SPI:    ~400                         │
│ ├─ RPLU2:       ~3,100 (M31 mult + BTU)      │
│ └─ Glue/IO:     ~1,000                       │
│                                              │
│ Total SLICE:    2,818 (LUT4 → SLICE÷4)      │
│ Usage:          ~1,625 (58%)                 │
│                                              │
│ Total BRAM:     46 (36 Kb each)             │
│ Usage:          ~4 (14%)                     │
│ ├─ Rotor table: 1                           │
│ ├─ Boot table:  1                           │
│ └─ Queues/scratch: 2                        │
│                                              │
│ DSP48:          132 (85 available)           │
│ Usage:          ~30 (23%)                    │
│ ├─ M31 mult:    16                          │
│ ├─ TDM ALU:     1                           │
│ └─ Accumulators: 13                         │
└─────────────────────────────────────────────┘
```

---

## 9. Next Steps

1. **Run nextpnr** with standard invocation (freq=50, speed=8)
2. **If success:** Proceed to bitstream generation and hardware testing
3. **If routing fails:** Try freq=40, seed=1/2/3, then escalate to --placer heap
4. **If timing fails:** Add pipeline stage to critical path (likely ALU → output register)
5. **Post-silicon:** Measure actual clock jitter and thermal profile; adjust frequency if needed

---

## References

- ECP5 Datasheet: `docs/ECP5_Family_Datasheet.pdf` (if available)
- Nextpnr docs: https://github.com/YosysHQ/nextpnr/blob/master/docs/ECP5.md
- RPLU2 architecture: `knowledge/RPLU2_ARCHITECTURE.md`
- Board constraints: `hardware/boards/ecp5_85k/spu_ecp5_85k.cst`

---

**Last updated:** 2026-07-05. Historical planning note; use the docs listed at
the top for current measured status.
