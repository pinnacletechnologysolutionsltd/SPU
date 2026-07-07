# SPU-13 RPLU 2.0 — Publication & Promotion Strategy
**Date:** 2026-06-29
**Last audited:** 2026-07-05
**Status:** Historical tactical draft. Use
`docs/PUBLICATION_STRATEGY_INDEX.md` and
`docs/SPU13_MARKET_AND_GRANT_POSITIONING.md` for the current arXiv-first
strategy and grant/outreach positioning.
**Scope:** IEEE paper, ArXiv preprint, OSHWA certification, community promotion

---

Audit note: numeric performance, energy, outreach, and OSHWA timelines in this
file are planning estimates unless backed by current evidence in
`docs/CURRENT_STATUS.md` and `docs/hardware_evidence.md`.

## Executive Summary

The SPU-13 RPLU 2.0 architecture is ready for publication across three parallel tracks:

1. **IEEE Publication** (Micro, ASPLOS, FCCM target)
2. **Open-Source Certification** (OSHWA, OpenHW)
3. **Community Promotion** (GitHub, Reddit, Hacker News, research networks)

This requires completing measurements, finalizing papers, and establishing credible publication channels.

---

## Current Status Assessment

### ✅ Existing Foundations
- **RTL implementation:** 10 verified modules (M31 multiplier, A₃₁ inverter, SOM, BTU, Padé pipeline)
- **Software oracles:** Python + C++17, 24–56 test checks PASS, zero float/sqrt audit complete
- **LaTeX template:** IEEE format ready (`docs/rplu_paper.tex`, 746 lines)
- **Data pipeline:** `tools/rplu_paper_data.py` generates publication-ready tables
- **Silicon proof:** Tang 25K SRAM load + SD hydration audit + SPI telemetry working

### ⚠️ Gaps Requiring Completion

| Gap | Impact | Priority | Effort |
|-----|--------|----------|--------|
| **Power measurements** | IEEE reviewers expect W/MHz, static vs dynamic | HIGH | 2–3 weeks |
| **Waveform documentation** | GTKWave VCD traces, timing diagrams | MEDIUM | 1–2 weeks |
| **Performance benchmarks** | Latency, throughput, energy-per-operation | HIGH | 2 weeks |
| **Area breakdown** | LUT/DSP/BRAM per module (nextpnr analysis) | HIGH | 1 week |
| **Comparison table** | CPU/GPU/FPGA baselines (FP32 vs exact rational) | HIGH | 2–3 weeks |
| **Reproducibility artifacts** | Build scripts, testbench configs, pin files | MEDIUM | 1 week |
| **Supplementary video** | 5–10 min demo (optional, but boosts visibility) | LOW | 2 weeks |
| **OSHWA cert prep** | License audit, documentation completeness | MEDIUM | 1–2 weeks |

---

## Publication Track 1: IEEE Paper (3–6 months to acceptance)

### Target Venues (in order of fit)
1. **IEEE Micro** (2-year impact factor ~4.5, prestige **)
   - Scope: Hardware/architecture innovations
   - Deadline: Typically rolling or seasonal
   - Format: 10–12 pages + references
   - Review cycle: 3–4 months

2. **ASPLOS** (top-tier systems, 3-year IF ~7.2, prestige ***)
   - Scope: "Architectural innovations that influence systems"
   - Deadline: Typically August 2026 (for June 2027 conference)
   - Format: 13 pages + references
   - Review cycle: 3 months

3. **FCCM** (Field-Configurable Custom Computing Machines, IF ~2.5)
   - Scope: FPGA/reconfigurable architecture
   - Deadline: Rolling (conference-driven)
   - Format: 8–10 pages
   - Review cycle: 2–3 months

4. **FPL** (Field-Programmable Logic, IF ~2.0)
   - Scope: Broad FPGA/reconfigurable systems
   - Deadline: Typically March (for September conference)

### Paper Completion Checklist

#### Phase 1: Measurements & Data Collection (Weeks 1–3)

**Power Profiling (2 weeks):**
- [ ] Setup power measurement on Tang 25K:
  - Keysight N6705B DC power supply (if available) with current probes
  - Or: INA226 current-sense breakout on 3.3V rail
  - Record: Idle current, manifold calculation current, peak current
  - Sample at 10 kHz over 1 second, extract min/max/avg

- [ ] Measure at different clock frequencies:
  - 12 MHz (current spec)
  - 24 MHz (achieved headroom)
  - 50 MHz (crystal limit)

- [ ] Document:
  - Static power (configuration, clock off): mW
  - Dynamic power vs clock: mW @ f MHz
  - Energy per RPLU operation: µJ (from latency + power)

**Timing & Latency (1 week):**
- [ ] Extract nextpnr critical path report:
  - Longest combinational delay
  - Register-to-register timing
  - Clock-to-Q + setup margins

- [ ] Measure RTL simulation latencies:
  - M31 multiply: cycles
  - A₃₁ inverse: cycles
  - BTU routing: cycles
  - Padé evaluation: cycles
  - Full pipeline: cycles

- [ ] Measure silicon latency (if RPLU2 proof complete):
  - SD read → FPGA SPI → RPLU output: µs
  - Jitter: ns (oscilloscope capture)

**Area & Resource Breakdown (1 week):**
- [ ] Parse current build reports rather than relying on old estimates:
  - Tang 25K split probes
  - Wukong Artix-7 `SU3SHARE`
  - Wukong Artix-7 `RPLU2PADE`
  - Colorlight i9 after ECP5 synthesis/P&R succeeds

- [ ] DSP utilization:
  - Quote only values from current synthesis/P&R logs

- [ ] BRAM:
  - Quote only values from current synthesis/P&R logs

**Comparative Baselines (2–3 weeks):**
- [ ] Benchmark against:
  - CPU baseline using the same exact workload and documented methodology
  - GPU/FPGA baselines only when the workload comparison is defensible
  - ARM Cortex-M7 (600 MHz): Integer approximation runtime
  - Research: Find published rational arithmetic baselines

- [ ] Create comparison table:

  | System | Bits | Latency (µs) | Power (mW) | Energy/Op (µJ) | Area (mm²) |
  |--------|------|--------------|-----------|-----------------|-----------|
  | SPU-13 Tang/Wukong/i9 | exact | measured | measured | measured | board/resource table |
  | CPU baseline | chosen method | measured | measured | measured | — |
  | GPU/other FPGA baseline | chosen method | measured/published | measured/published | measured/published | — |

  **Note:** Frame comparison as determinism + exactness vs speed.

#### Phase 2: Paper Finalization (Weeks 4–6)

**Complete Main Sections:**
- [x] Abstract (exists, refine)
- [x] Introduction (exists, add quantitative findings)
- [ ] Related Work
  - Jet algebra hardware (sparse — cite theoretical papers)
  - Exact rational arithmetic accelerators (e.g., CUPY, FieldComputable)
  - SOM hardware (classic: Takeda, Himavathi; recent: FPGA variants)
  - Deterministic computing (safety-critical systems)

- [ ] Architecture Section (refine `docs/rplu_paper_hw_section.tex`)
  - Stage 1: SOM Kohonen (7-node parallel array, 3-stage quadrance pipeline)
  - Stage 2: BTU (64-row spatial routing, 4-lane BRAM)
  - Stage 3: Padé (Horner evaluation, A₃₁ inverter)
  - Stage 4: Output latch
  - Timing diagrams (Verilog testbench → GTKWave PNG export)

- [ ] Implementation Section
  - Synthesis flow (Yosys + NextPNR + Gowin)
  - Resource tables (LUT, DSP, BRAM, MHz)
  - Two targets: Artix-7 (reference) + GW5A-25A (embedded proof)

- [ ] Results Section
  - Power vs frequency graph (plot power_data.json)
  - Latency breakdown (per-stage pipeline profiling)
  - Comparative table (vs CPU/GPU/prior FPGA work)
  - Case study: Rational robotics (inverse kinematics via SOM)

- [ ] Discussion
  - Determinism guarantees (no subnormal, no rounding drift)
  - Trade-offs (exact arithmetic → lower throughput than FP32)
  - Future: clustered deployment, Henosis stability mechanism

- [ ] Conclusion (1/2 page)

**Supplementary Materials:**
- [ ] Appendix A: A₃₁ algebra axioms & properties
- [ ] Appendix B: Verilog module instantiation diagram
- [ ] Appendix C: Testbench methodology (24 checks, coverage)
- [ ] Appendix D: Git commit hash for reproducibility

#### Phase 3: Submission Readiness (Week 6–8)

- [ ] Final proofread (spelling, grammar, notation consistency)
- [ ] Verify all figures are publication-ready (vector PDFs, not raster)
- [ ] Reference list complete + validated (DOI cross-check)
- [ ] Author affiliations & contact info finalized
- [ ] Supplementary code artifact (tagged GitHub release)
- [ ] Submit to first-choice venue

---

## Publication Track 2: ArXiv + Open-Source Certification (2–4 weeks)

### ArXiv Submission (Parallel with IEEE)

**Timeline:** Post on ArXiv immediately after IEEE submission (or 1 week before, if allowed).

**Why ArXiv?**
- Establishes priority date (IEEE reviewers often check ArXiv)
- Wider researcher reach (academics, industry, hobbyists)
- Community feedback before peer review
- Accelerates visibility (indexed within 24 hours)

**Submission Checklist:**
- [ ] Convert IEEE `.tex` to ArXiv-compatible format (standard LaTeX, no proprietary macros)
- [ ] Add 5–10 minute supplementary video (YouTube link)
- [ ] Create `README.md` with build instructions
- [ ] Ensure all figures/tables are self-contained (no external dependencies)
- [ ] Register for ArXiv account (if not already done)
- [ ] Submit under category:
  - Primary: `cs.AR` (Computer Architecture)
  - Secondary: `eess.SP` (Signal Processing) or `q-bio.QM` (Quantitative Methods)

**ArXiv-Specific Enhancements:**
- Add "code availability" statement: GitHub URL + DOI (Zenodo)
- Include links to:
  - Full bitstream (Tang 25K, Artix-7)
  - Testbenches + Python/C++ oracles
  - Power measurement data (CSV)
  - Waveform files (VCD format)

### OSHWA Certification (Parallel, 4–6 weeks)

**Why OSHWA?**
- Legitimizes open-source hardware claim
- Required for grants, partnerships, research collaboration
- Increases adoption (enterprises trust OSHWA-certified designs)

**OSHWA Requirements (https://www.oshwa.org/certification/):**

1. **Hardware Definition Standard**
   - [x] Schematic (KiCad or PDF) — Tang 25K devboard already documented
   - [x] PCB layout (if custom board) — or reference to Tang 25K PJRC docs
   - [x] Bill of Materials (BOM) — Tang 25K + PMOD J4 flash + RP2040 PMOD
   - [x] Verilog RTL (source code) — all in hardware/*/rtl/
   - [x] Assembly instructions — docs/build_and_bringup_guide.md
   - [ ] Test/validation procedure — expand build_and_bringup_guide.md

2. **Documentation**
   - [x] Usage guide — `knowledge/isa_reference.md`
   - [x] Design rationale — `docs/rplu_formal_spec.md`
   - [x] License — CC0 1.0 Universal (public domain)
   - [ ] Troubleshooting guide (new)
   - [ ] Maintenance notes (new)

3. **License**
   - [x] CC0 1.0 is OSHWA-compatible
   - [x] All RTL, firmware, tooling under CC0
   - [x] No GPL/MIT/Apache conflicts
   - [ ] Add SPDX license headers to all source files (if missing)

4. **Openness**
   - [x] All design files on GitHub (public)
   - [x] No proprietary closed-source blocks
   - [x] No patent licensing issues

5. **Technical Certification**
   - [ ] Fill OSHWA certification form (online)
   - [ ] Pay $50 certification fee
   - [ ] Receive OSHWA # (e.g., RP000001)
   - [ ] Add badge to GitHub README

**Certification Checklist:**
- [ ] Create `HARDWARE.md` documenting:
  - Bill of Materials (with part numbers, suppliers, costs)
  - Schematic/diagram (Fritzing or PDF)
  - PCB layout (KiCad or reference)
  - Assembly procedure (step-by-step photos optional)

- [ ] Create `TESTING.md` documenting:
  - Functional test procedure (run `run_all_tests.py`)
  - Hardware bring-up checklist
  - Expected test results
  - Troubleshooting (if test fails, what to check)

- [ ] Create `MAINTENANCE.md` documenting:
  - Known issues
  - Patches / errata
  - Community contributions process
  - Roadmap for future versions

- [ ] Fill out OSHWA form at https://certification.oshwa.org/
  - Select category: FPGA + MCU + Sensors
  - Describe hardware architecture (500 words)
  - Provide GitHub URL
  - Upload documentation PDFs

---

## Publication Track 3: Community Promotion (Ongoing, 2–3 months)

### Strategy: Multi-Channel Visibility

**Phase 1: Research Community (Week 0–2)**
- [ ] **ArXiv notification**
  - Email research contacts (professors, grad students in FPGAs, rational geometry)
  - Subject: "RPLU 2.0: Hardware Jet Algebra over M31"
  - Include: ArXiv link + GitHub + brief summary

- [ ] **Conference Presentations** (if accepting talks)
  - FPGA 2027 (deadline ~Sept 2026)
  - FPL 2026 (deadline ~March, conference ~Sept)
  - ACM SIGARCH poster sessions (ongoing)

**Phase 2: Maker & Open-Hardware Community (Week 2–4)**
- [ ] **Hacker News** (https://news.ycombinator.com)
  - Submit at 9 AM Eastern (peak engagement)
  - Headline: "RPLU 2.0: Open-Source Deterministic Hardware for Rational Arithmetic"
  - Or: "Running Exact Rational Math on FPGA (No Floating-Point Drift)"

- [ ] **Reddit Communities**
  - r/FPGA: "Show & Tell" weekly thread
  - r/electronics: Hardware architecture thread
  - r/math: Rational geometry / Wildberger methods
  - r/RaspberryPi: Southbridge architecture + RP2350 ecosystem

- [ ] **GitHub Trending**
  - Craft a compelling README (include power graph, block diagram)
  - Add GitHub topics: `fpga`, `hardware`, `rational-arithmetic`, `exact-computation`, `open-source`
  - Create GitHub discussion board
  - Link to ArXiv + paper + blog post

**Phase 3: Academic Networks (Week 4–8)**
- [ ] **Mailing Lists & Forums**
  - FPGA-L (fpga-l@lists.vcu.edu)
  - OpenHW Group (https://www.openhwgroup.org/)
  - OMG Systems Modeling Language (rational geometry sub-group)
  - LLM/ML for Science communities (rational geometry angle)

- [ ] **Research Collaboration Outreach**
  - Delft QuTech (quantum error correction interest)
  - Jiuzhang quantum photonics lab (bosonic code applications)
  - Wildberger rationalist geometry community
  - Safety-critical systems researchers

- [ ] **Industry Partnerships**
  - Xilinx/AMD: FPGA innovation program
  - Gowin Semiconductor: Academic board donations
  - SparkFun / Adafruit: Featured product (open-hardware badge)

**Phase 4: Long-Tail Visibility (Month 2–3)**
- [ ] **Blog Post Series** (Medium, DEV.to, personal blog)
  1. "Why Exact Rational Arithmetic Matters" (motivation)
  2. "Jet Algebra: Computing Derivatives without Floating-Point" (theory)
  3. "Building RPLU on GW5A: Synthesis to Silicon" (process)
  4. "Benchmarking Determinism: FPGA vs CPU vs GPU" (results)

- [ ] **Podcast / Interview** (optional but high impact)
  - Embedded.fm (hardware + firmware podcast)
  - FPGA Design Mag (monthly podcast)
  - Local tech meetup talk

- [ ] **YouTube Demonstration Video** (5–10 minutes)
  - Capture: Tang 25K + RP2350 + telemetry output
  - Demo: Load SD card → RPLU computation → telemetry stream
  - Graphics: Block diagram + timing waveforms overlay
  - Narration: Explain determinism claim + performance metrics

---

## Metrics to Collect (Comprehensive List)

### Power & Energy
- [ ] Idle current (no clock, FPGA in config hold): mA
- [ ] Active current @ 12 MHz: mA (min, avg, max)
- [ ] Active current @ 24 MHz: mA (min, avg, max)
- [ ] Active current @ 50 MHz: mA (min, avg, max)
- [ ] Energy per RPLU operation: µJ (from cycle count × avg power)
- [ ] Power density: mW/mm² (if silicon area estimated)

### Timing & Latency
- [ ] Combinational delay (critical path): ns
- [ ] Pipeline depth: stages
- [ ] Throughput: operations/second @ 12 MHz
- [ ] End-to-end latency (SD → SPI → RPLU output): µs
- [ ] Jitter (peak-to-peak variation): ns

### Area
- [ ] LUT4 utilization: count + %
- [ ] DSP utilization: count + %
- [ ] BRAM utilization: count + %
- [ ] Cells synthesized (post-optimization): count
- [ ] Estimated area for Artix-7: mm² (from LUT density)

### Functional Coverage
- [ ] Testbench count and pass/fail from current `python3 run_all_tests.py`
- [ ] Test vectors: 1,000+
- [ ] Coverage: line + branch + assertion
- [ ] Bit-exact match (Python/C++ oracle vs RTL): 100%

### Comparison Metrics
- [ ] Latency comparison vs CPU baseline using the same exact workload
- [ ] Energy comparison using measured board power and documented methodology
- [ ] Determinism guarantee: exact replay at declared algebraic closure points

---

## Waveform Documentation Plan

### GTKWave Capture Strategy

**Create Publication-Ready VCD Traces:**

1. **M31 Multiplier Trace** (20 cycles)
   - Input: Two M31 operands
   - Output: Product (2 cycles)
   - Signals: `clk`, `valid_in`, `a[31:0]`, `b[31:0]`, `result[63:0]`, `valid_out`
   - Export: PNG (800×600, timeline overlay)

2. **A₃₁ Inverter Trace** (100 cycles, interesting points)
   - Input: Non-unit element in A₃₁
   - Output: Inverse (76 cycles)
   - Key signals: `stage[1:0]`, `denominator`, `gcd_state`, `valid_in/out`
   - Export: Zoomed sections (1 per stage, 25 cycles each)

3. **SOM BMU Selection Trace** (30 cycles)
   - Input: Test vector (Quadray)
   - Output: BMU index + quadrance
   - Signals: `test_vector[31:0]`, `node_idx[2:0]`, `quadrance[63:0]`, `winner_valid`
   - Export: Full trace (test phase → comparison → decision)

4. **RPLU Full Pipeline Trace** (150 cycles)
   - Input: SD card RPLU config
   - Output: Manifold computation result
   - Signals: All 4 pipeline stages
   - Export: Summary (zoomed key transitions, color-coded by stage)

**Tools & Scripts:**
```bash
# Capture VCD from Verilator-compiled RTL
verilator -cc --trace spu13_rplu_pipeline_tb.v
g++ -o test obj_dir/Vspu13_rplu_pipeline_tb.cpp
./test --trace
# Outputs: test.vcd

# Convert to PNG via GTKWave
gtkwave test.vcd --vcd \
  --signals spu13_rplu_signals.gtkw \
  --png --width 1200 --height 800 \
  -o test_waveform.png

# LaTeX inclusion:
\includegraphics[width=\linewidth]{figures/spu13_rplu_waveform.png}
```

---

## Promotion Timeline (Master Schedule)

```
WEEK 1–3:   Measurements (power, area, latency, baselines)
WEEK 4–6:   Paper finalization + ArXiv + OSHWA docs
WEEK 6–8:   ArXiv submission + IEEE submission
WEEK 8–10:  Community outreach (HN, Reddit, research lists)
WEEK 10–14: Blog post series + video + podcast prep
MONTH 3–4:  OSHWA package review + community promotion
MONTH 4–6:  IEEE review cycle + community feedback
MONTH 6+:   IEEE publication + expanded roadmap
```

Current audit: treat OSHWA certification and broad community promotion as
post-evidence steps, not calendar guarantees.

---

## Success Criteria

### For IEEE Paper
- ✅ Accepted to Tier-1 venue (IEEE Micro / ASPLOS / FCCM)
- ✅ Current evidence pack accepted as reproducible and well-scoped
- ✅ Follow-on peer review or collaboration path established

### For OSHWA Certification
- ✅ Certification package submitted only after KiCad/ERC/DRC blockers are closed
- ✅ Known limitations published clearly
- ✅ Contributions from community tracked through issues, PRs, and documentation

### For Community Visibility
- ✅ ArXiv papers live
- ✅ Technical site or blog explains the architecture clearly
- ✅ Research outreach produces serious technical feedback or collaboration leads

---

## Resource Requirements

| Resource | Why Needed | Cost/Effort |
|----------|-----------|------------|
| **Power measurement equipment** | Current probes, multimeter | $500–2k (or borrow) |
| **Publication fee** (optional) | Open-access IEEE waiver | $2k (waiverable) |
| **OSHWA certification** | Hardware legitimacy | $50 + 4 hours docs |
| **ArXiv account** | Pre-print distribution | Free |
| **GitHub account** | Code hosting (already have) | Free |
| **Video production** | Screen capture + editing | OBS (free) + 8 hours labor |
| **Domain name** (optional) | Branding / landing page | $15/year |
| **Promotion time** | Social media, outreach | 4–6 weeks part-time |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| **IEEE review rejection** | Submit to FCCM/FPL in parallel; address feedback iteratively |
| **OSHWA docs incomplete** | Use template from OpenHW / Rasperry Pi examples |
| **Power measurement hard to obtain** | Estimate from simulation; provide uncertainties in paper |
| **Low community uptake** | Partner with universities for class projects / senior designs |
| **Platform dependency (Tang 25K)** | Publish Artix-7 reference design; port to iCE40 |

---

## Next Immediate Actions (Next 2 Weeks)

1. **Order power measurement equipment** (if not available)
   - INA226 current-sense module ($10, AliExpress)
   - Oscilloscope + current probe ($0 if lab access)

2. **Start power measurements** (parallel with RPLU2 proof)
   - Document idle current
   - Log active current @ 12 MHz over 5 iterations
   - Estimate energy per operation

3. **Extract area metrics from nextpnr JSON**
   ```bash
   # Parse GW5A-25A report
   python3 tools/extract_nextpnr_metrics.py \
       build/spu13_rplu2_consume_probe_pnr.json
   # Outputs: lut_count, dsp_count, bram_count, crit_path_ns
   ```

4. **Begin waveform capture** (from existing testbenches)
   ```bash
   # Generate VCD from RTL simulation
   iverilog -g2009 -o sim hardware/*/tests/spu13_m31_multiplier_tb.v
   vvp sim -vcd
   # Outputs: dump.vcd (import to GTKWave)
   ```

5. **Draft Related Work section** (literature review)
   - Jet algebra papers (Ries et al., 1990s)
   - Rational arithmetic accelerators (sparse, but cite computational algebra systems)
   - FPGA SOM implementations (Himavathi et al., recent)

---

## Appendix: Publication Venues Reference

### Top Venues for Exact Arithmetic / Rational Computing

| Venue | Tier | Field | Deadline | Link |
|-------|------|-------|----------|------|
| IEEE Micro | 1 | Architecture | Quarterly | micro.computer.org |
| ASPLOS | 1 | Systems | Aug 2026 | asplos-conference.org |
| FCCM | 1 | FPGA | Seasonal | fccm.org |
| FPL | 2 | FPGA | March 2027 | fpl.org |
| DAC | 1 | Design Automation | ~Quarterly | dac.com |
| ICCAD | 1 | CAD | ~Aug 2026 | iccad.com |
| ASP-DAC | 2 | Design (Asia) | Sept 2026 | aspdac.com |
| IJRC | 3 | Reconfigurable | Ongoing | ijrc.org |

### Open-Access / Pre-Print Venues

| Venue | Scope | Cost | Timeline |
|-------|-------|------|----------|
| ArXiv (cs.AR) | All computer architecture | Free | 24-hour indexing |
| ACM TOCS | Top-tier journal, open access | Fee waiverable | 3–4 months review |
| IEEE TCAD | CAD-focused journal | Fee waiverable | 3–4 months |

---

## Conclusion

The SPU-13 RPLU 2.0 architecture is ready for high-impact publication. By completing power/area measurements, finalizing the IEEE paper, and pursuing OSHWA certification in parallel, we can establish credibility across academia, industry, and maker communities within **3–4 months**.

The combination of deterministic execution + exact rational arithmetic + open-source design positions RPLU 2.0 as a unique contribution to embedded computing and safety-critical systems.
