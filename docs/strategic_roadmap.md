# SPU-13 Strategic Roadmap

## Current Status (June 22, 2026)

### Phase 2 Complete — Next-Gen ISA RTL All Written

| Component | Status | Tests | LUTs |
|:---|---|:---:|:---:|
| `spu_isa_defines.vh` | ✅ Completed | — | — |
| `spu_isa_decoder.v` | ✅ Completed | 34 iverilog PASS | ~200 |
| `spu_twin_regfile.v` | ✅ Completed | 16 iverilog PASS | ~50 |
| `spu_rau.v` | ✅ Completed | 16 iverilog PASS | ~100 |
| `spu_pipeline_ctrl.v` | ✅ Completed | 10 iverilog PASS | ~50 |
| **Total new RTL** | **✅ All written** | **76 tests PASS** | **~400** |

The remaining work is **hardware bring-up** (SPI link test, SD card, RPLU) which is blocked on dupont cables, SD card reader, and replacement Tang 25K.

### Phase 1: Southbridge Bring-Up (Hardware-Dependent, ~2-4 weeks)

### Step 1.1: Physical Link (dupont cables day 1)
```
Wire RP2350-Zero GP0-3 → Tang 25K PMOD J4
Load existing bitstream (no decoder needed yet)
Flash spu_link_test.uf2
→ Verify LED[2] flash = SPI alive
→ USB CDC shows status/manifold reads
```
*Risk:* Pin mapping wrong, SPI mode mismatch. *Mitigation:* Already documented in CST.

### Step 1.2: SD Card Storage (SD reader day 1-2)
```
Format SD FAT32, copy build/*.tbl + manifest.txt
Flash spu_sd_test.uf2
→ Verify file create/write/read/delete
→ If pass: spu_storage_hydrate_from_sd() loads RPLU tables
```
*Risk:* Card init fails (voltage, timing). *Mitigation:* `sim_sd_card.v` already validates the SPI protocol.

### Step 1.3: New ISA Decoder on FPGA (day 2-3)
```
Flash build/tang_primer_25k_spu13_fpga.fs (includes decoder)
RP2350 sends PHSLK chord over SPI
→ FPGA decodes, sets coherent flag
→ Telemetry confirms phase-lock status
```
*Risk:* Decoder has bug not caught in sim. *Mitigation:* 34 Verilog tests pass, but real SPI timing differs.

### Step 1.4: RP2350 Southbridge Complete (day 3-5)
```
Full rp2350_spu_interface:
  - Core 0: USB CDC console (diag commands)
  - Core 1: SPI poller at 1 kHz, chord forwarder
  - SD card hydration at boot
  - Health telemetry every 1s
```
*Deliverable:* Boot RP2350 → auto-hydrate from SD → stream chords → FPGA responds.

**Phase 1 Success Criteria:** RP2350 reads file from SD, sends "hello" chord over SPI, LED blinks.

---

## Phase 2: Next-Gen ISA Validation (4-8 weeks)

### Step 2.1: Twin-Register File RTL
```
New module: spu_twin_regfile.v
  - 32 entries × {O:64, C:64} = 512 bytes
  - Dual-port reads (Offer .O, Confirmation .C in parallel)
  - Single-port write
  - SPU-4 mode: only banks 0-7 active (power-gate rest)
```
*Key decision:* BRAM vs distributed RAM. BRAM is denser (1 block = 512 bytes fits in 1 BRAM), but distributed gives 0-wait read. GW5A-25 has 56 BRAMs — using 1 is negligible.

### Step 2.2: RAU Integration
```
Map new opcodes to existing spu_unified_alu_tdm.v:
  QADD → existing ADD path (3-cycle TDM → needs widening)
  QMUL → existing MUL path (RationalSurd multiply exists)
  SPRD → new: quadrance ratio computation
  PHSLK → new: cross-multiply + RATIO_CMP trigger
  INVJ → existing sign_flip (1 cycle, trivial)
```
*Effort:* ~300 LUTs for the new datapaths. SPRD and PHSLK need ~100 LUTs each for the rational comparator.

### Step 2.3: Pipeline Controller
```
New module: spu_pipeline_ctrl.v
  - 7-stage (1 Janus + 3 Tetrahedron A + 3 Tetrahedron B)
  - Stage 0: Fetch from chord FIFO
  - Stages 1-3: Forward path (decode, read, compute)
  - Stages 4-6: Return path (confirm, lock, writeback)
  - Hazard detection: RAW on twin-registers
```
*Architecture note:* This replaces the current 3-cycle TDM controller. The TDM DSP is still used — just wrapped in a deeper pipeline.

### Step 2.4: Assembler + Toolchain
```
spu13_asm.py --arch wf (already works)
Need:
  - Linker: resolve labels across .tbl + .sas files
  - Simulator GUI: visualize PHSLK handshake in real-time
  - .sas standard library: common material routines
```

**Phase 2 Success Criteria:** PHSLK instruction executes on FPGA with real RPLU material tables, returns coherent/non-coherent flag, observable via telemetry.

---

## Phase 3: Artix-7 Wukong Port (8-16 weeks after start)

### Why Wukong?
- **Xilinx ecosystem:** Vivado, Vitis, broader community
- **More resources:** Artix-7 200T has 33K LUTs, more BRAM, DSP48
- **PMOD + Raspberry Pi header:** Easier to prototype with multiple peripherals
- **The user has one already** — no purchase delay

### What Changes

| Component | Tang 25K (Gowin) | Wukong (Xilinx) |
|-----------|-------------------|------------------|
| Primitive stubs | `spu_gowin_prim.v` | `spu_xilinx_prim.v` (exists in `rtl/common/prim/`) |
| DSP macro | `gowin_mult18.v` | `xilinx_dsp48.v` (wider: 18×18 → 25×18) |
| PLL/clock | Internal OSC → BUFG | MMCM → BUFG |
| SDRAM | GW5A internal | External DDR3 on Wukong |
| Toolchain | Yosys + nextpnr + gowin_pack | Vivado |

### Effort Estimate
| Task | Effort | Dependencies |
|------|--------|--------------|
| Primitive mapping | 2 days | None — `spu_xilinx_prim.v` exists |
| Synthesis script | 1 day | Vivado installed |
| SDRAM controller | 2 weeks | DDR3 datasheet + MIG |
| Debug with ILA | 3 days | Vivado logic analyzer |
| **Total** | **~3-4 weeks** | |

### Tradeoff
Wukong has more resources but **no RPLU** without external DDR3. Tang 25K has RPLU via internal BRAM. Ideal split:
- **Tang 25K:** RPLU + material table development (math proving ground)
- **Wukong:** Cluster communication + Whisper Bridge + video out (system integration)

**Phase 3 Success Criteria:** Same SPU-13 bitstream loads on both Gowin and Xilinx, produces identical manifold output for the same input chords.

---

## Phase 4: Cluster + Communication (8-16 weeks)

### Step 4.1: Whisper Bridge (PWI 1-wire)
```
Already in rp2350_spu_interface.c (guarded by SPU_ENABLE_WHISPER)
  - RP2350 GP7 → PWI TX to FPGA
  - Pulse-width encodes dissonance + cubic leak events
  - Enable in firmware: cmake -DSPU_ENABLE_WHISPER=ON
```
*Purpose:* One-wire telemetry from FPGA to RP2350 without SPI overhead.

### Step 4.2: Artery Link (SPU-to-SPU)
```
Existing: hardware/rtl/peripherals/artery/spu_artery.v
  - Bidirectional 2-chord protocol (header + data)
  - Daisy-chain topology for cluster
  - Works over LVDS pairs
```
*Need:* Another FPGA or RP2350 as the peer. Wukong + Tang 25K = 2-node cluster.

### Step 4.3: Piranha Pulse (Heartbeat)
```
Already in rp2350_spu_interface.c (guarded by SPU_ENABLE_PIRANHA)
  - RP2350 GP6 → 61.44 kHz heartbeat to FPGA
  - PIO-based, no CPU overhead
  - Scope to verify timing
```

**Phase 4 Success Criteria:** Two FPGAs exchange SPU manifold state over Artery link at >100 Hz.

---

## Phase 5: Promotion (Start Week 2-4, After Hardware Proven)

### Step 5.0: GitHub Organisation
```
1. Create GitHub org: github.com/spu13 (or similar name)
2. Create repos:
   spu13-hardware    → RTL, synth scripts, board files (LGPL)
   spu13-software    → VM, assembler, toolchain (MIT)
   spu13-docs        → ISA spec, roadmap, whitepapers (CC-BY)
   spu13-southbridge → RP2350 firmware (LGPL)
3. Enable Discussions tab = built-in forum
4. Enable Wiki tab = documentation
5. GitHub Pages from spu13-docs = website
6. Your LLC owns the org
```

### Step 5.1: arXiv Preprint (After Hardware Proven)
Target: 5-10 page technical paper
```
arXiv.org → cs.AR (Architecture) or cs.ET (Emerging Technologies)
Title: "SPU-13: A Deterministic Geometric Computer Using Rational Quadray Arithmetic"
Sections:
  1. Introduction — problem with IEEE-754 / Von Neumann for geometry
  2. Mathematical Foundation — Q(√3), Quadrays, Wheeler-Feynman absorber theory
  3. ISA Design — twin-registers, temporal opcodes, 4-stage pipeline
  4. Implementation — RTL, synthesis results on GW5A-25 (11K LUTs)
  5. Verification — 76 simulation tests across Python/C++/Verilog
  6. Conclusion — applications, next steps
```

### Step 5.2: Funding — NZ-Specific Paths
Since you're in New Zealand, US grants (NSBIR, DOE, DARPA) are not directly accessible. Better options:

| Source | Type | Amount | Fit |
|--------|------|--------|-----|
| **NZ Callaghan Innovation** | R&D Grant | $25-100K NZD | Deep tech hardware, 40% of R&D costs |
| **NZ MBIE Endeavour Fund** | Research Grant | $500K-5M NZD | "Space/depth" science applications |
| **NZ Ministry of Defence** | Local SBIR equivalent | $50-200K NZD | Technology readiness programs |
| **KiwiNet** | Commercialisation | $50-150K NZD | Pre-seed for uni-connected startups |
| **Deep Tech VC (Aus/NZ)** | Equity investment | $500K-2M NZD | Blackbird, Icehouse, Movac |
| **International VC** | Equity investment | $1-5M USD | Lux Capital, DCVC (US); Possible via NZ Inc connections |
| **Open-source sponsorship** | Donations/grants | $10-100K/yr | NLNet (EU), Mozilla, ARDC (AU) |

**Recommendation path:**
1. **Prove southbridge** (this week) → credibility
2. **arXiv paper** (next week) → establishes priority globally
3. **Callaghan Innovation R&D grant** (apply within 1-2 months) — best NZ-specific option for deep tech
4. **KiwiNet pre-seed** if you can partner with a NZ university
5. **arXiv + GitHub presence** → international VCs can find you regardless of location

### Step 5.3: Conference Papers (After arXiv)

| Conference | Deadline | Location | Focus |
|------------|----------|----------|-------|
| **arXiv** | Any time | Online | Priority establishment |
| **FPGA** (ACM) | September | Monterey, USA | RTL implementation |
| **HEART** | April | Europe | Heterogeneous computing |
| **FPT** | June | Asia/APAC | FPGA technology — closest geographically |
| **IEEE Micro** | Rolling | Online | Architecture overview |

### Step 5.4: Demo Video (After Hardware Proven, Day 1)
```
60-second demo:
  0:00 RP2350 boots, LED blinks
  0:20 Sends PHSLK chord over SPI → LED flash
  0:35 USB CDC shows "COHERENT" / "NOT COHERENT"
  0:50 Manifold state displayed
  1:00 End
```
Platforms: YouTube, Twitter/X, Hacker News, r/FPGA, r/RISCV

---

## Phase 6: Funding (Weeks 4-52, Continuous)

### Track A: Grants (Low equity dilution, slow)

| Program | Amount | Fit | Deadline |
|---------|--------|-----|----------|
| **NSF SBIR Phase I** | $275K | "Novel geometric coprocessor architecture" | Rolling |
| **DOE SBIR** | $200K | "Deterministic simulation for materials science" | Annual |
| **DARPA YFA** | $500K/yr | "Beyond Von Neumann computing" | Annual |
| **NIH SBIR** | $300K | "Rational geometry for molecular dynamics" | Rolling |

*Strategy:* Position as "deterministic alternative to quantum computing for molecular simulation" — this is the current hot funding area.

### Track B: Deep Tech VC (Faster, more dilution)

| Firm | Thesis | Check Size |
|------|--------|------------|
| **Lux Capital** | Hard science, frontier tech | $2-5M seed |
| **DCVC** | Deep tech, climate/simulation | $1-3M seed |
| **MFV Partners** | Semiconductor, open source | $1-2M seed |
| **Acequia Capital** | FPGA, hardware | $500K-1M pre-seed |

*Pitch:* "Custom silicon for rational geometry — 1000x more efficient than GPUs for physics simulation, exact arithmetic, no floating-point drift, deterministic by construction."

### Track C: Open Source + Services (Sustain, not scale)

| Revenue Model | Annual Potential | Effort |
|---------------|-----------------|--------|
| Consulting: custom SPU-13 cores for specific materials | $50-100K | High (client work) |
| Paid: bitstream licenses for commercial use | $10-50K | Low (GitHub + license) |
| Training: workshops on rational geometry computing | $20-40K | Medium (curriculum) |
| Hardware: selling RP2350+FPGA boards as kits | $30-60K | High (manufacturing) |

### Track D: Academic Partnership
- Find a professor working on: non-Von-Neumann architectures, rational geometry, or quantum simulation alternatives
- Publish jointly — they bring credibility, you bring the silicon proof
- Target: MIT CSAIL, Stanford EE, CMU ECE, UC Berkeley ADEPT lab

---

## Phase 7: Custom Hardware (Months 6-12)

After the FPGA split is proven, consolidate:

```
┌──────────────────────────────────┐
│  Custom PCB (4-layer minimum)    │
├──────────────────────────────────┤
│  RP2350 (QFN-60)                 │
│  + SPI flash (boot + cache)      │
│  + SD card slot                  │
│  + USB-C (CDC + power)           │
│  + PMOD headers (expand)         │
│  + Artery LVDS pairs (cluster)   │
└──────────────────────────────────┘
```

*Why custom:* The RP2350-Zero + Tang 25K PMOD wiring is fragile. A single PCB with both chips, voltage regulation, and connectors is more reliable and demonstrable.

*Cost:* ~$50-100/board at prototype qty 10. ~$20-30 at qty 100.

---

## Timeline Summary

```
Week  1-2:  Hardware arrives → SPI link test → SD card test (Phase 1)
Week  2-4:  New ISA on FPGA → twin-register RTL (Phase 2)
Week  4-6:  GitHub org → demo video → arXiv paper (Phase 5)
Week  6-10: Wukong port starts (Phase 3)
Week  8-12: SBIR/VC conversations begin (Phase 6)
Week 12-16: Cluster demo (Phase 4)
Week 16-20: Custom PCB design (Phase 7)
Week 20-24: Tape-out / final prototype
```

## Key Risks

| Risk | Probability | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Tang 25K replacement delayed | High | Medium | Broken board works for SPI bring-up |
| SD card init fails in practice | Low | Medium | sim_sd_card.v protocol validated |
| PHSLK not useful for real problems | Medium | High | Test with actual Morse potential data |
| No funding found | Medium | High | Open-source + consulting as fallback |
| Artix-7 port takes longer than expected | Medium | Low | Tang 25K is primary target |
