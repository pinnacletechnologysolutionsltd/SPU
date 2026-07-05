# SPU-13 Publication & Promotion Strategy — Complete Index

**Created:** 2026-06-29 10:22 UTC+12:00
**Last audited:** 2026-07-05
**Status:** Active strategy index. Older tactical estimates remain in the
linked documents, but current claims must be checked against
`CURRENT_STATUS.md`, `hardware_evidence.md`, and
`SPU13_MARKET_AND_GRANT_POSITIONING.md`.

## Master Documents (Session Artifacts)

### 0. Architecture Identity And Boundaries
**File:** `SPU13_IDENTITY_AND_BOUNDARIES.md`
**Scope:** Canonical statement of what SPU-13 is and is not
**Key Sections:**
- One-sentence architecture identity
- What SPU-13 is / is not
- Application pillars
- Native rational AI boundary
- Guarded non-von-Neumann interface boundary
- Claim ladder from software oracle to certified product

**Use This For:**
- Keeping publication language precise
- Avoiding GPU/LLM/quantum/neuromorphic overclaims
- Separating proven hardware, RTL proof, and future research directions

---

### 1. Publication & Promotion Strategy (21.8 KB)
**File:** `publication_and_promotion_strategy.md`
**Scope:** Comprehensive strategic framework for academic publication + community launch
**Key Sections:**
- Current status assessment (gaps to close)
- IEEE publication track (venues, paper completion checklist)
- ArXiv submission guide
- OSHWA certification requirements & procedure
- Community promotion strategy (4-track approach)
- Risk mitigation & success criteria
- Publication venue reference table

**Use This For:**
- Understanding publication strategy at high level
- Identifying what metrics/measurements are needed
- Planning 8-week paper finalization process
- Understanding OSHWA certification steps
- Market positioning & audience reach targets

---

### 1.5 Market And Grant Positioning
**File:** `SPU13_MARKET_AND_GRANT_POSITIONING.md`
**Scope:** High-margin market thesis and cautious grant-language guide
**Key Sections:**
- One-line market pitch
- Best initial markets and required evidence
- Grant/research alignment themes
- Outreach evidence pack
- Safe and unsafe pitch language

**Use This For:**
- Grant draft preparation
- Pitch-deck language
- Deciding which Wukong/Tang evidence to collect next
- Avoiding stale program-name overclaims

---

### 1.6 Public Site And Outreach Plan
**File:** `public_site_and_outreach_plan.md`
**Scope:** Lightweight website, blog, and social-channel plan
**Key Sections:**
- Site structure
- First five posts
- Channel strategy
- Writing rules
- Implementation checklist

**Use This For:**
- Building the public documentation site
- Planning LinkedIn/X updates
- Keeping public promotion evidence-bound

---

### 2. Metrics Collection Plan (10.7 KB)
**File:** `metrics_collection_plan.py` (executable Python script)
**Scope:** Turnkey templates for measurement data collection
**Key Components:**
- Power measurement data structures (JSON template)
- Latency measurement templates
- Area breakdown templates (LUT/DSP/BRAM)
- Test coverage templates
- Comparative baseline templates

**Use This For:**
- Running: `python3 metrics_collection_plan.py --generate-templates`
- Generating 5 JSON template files in `tools/build/`
- Populating with actual measurement data
- Ensuring consistent data format across all metrics

**Output Files Generated:**
```
tools/build/
  ├── power_measurements.json
  ├── latency_measurements.json
  ├── area_breakdown.json
  ├── test_coverage.json
  └── comparative_baselines.json
```

---

### 3. 12-Week Publication Roadmap (15 KB)
**File:** `publication_roadmap_12week.txt`
**Scope:** Historical week-by-week tactical execution plan. Treat as planning
context; the current sequence is paper-first, evidence-freeze, then outreach.
**Key Timeline:**
- **Current:** SPU-13/RPLU/Lucas/SU3 arXiv papers first
- **Then:** evidence tag and resource/timing tables
- **Then:** grant, academic, commercial, and public outreach
- **Later:** IEEE/FCCM/FPL once measurements are strong enough

**Use This For:**
- Understanding earlier planning assumptions
- Mining checklist items for current plans
- Avoiding copy/paste of stale numeric targets

---

## Critical Path Dependencies

```
Week 0–2: PAPER FOUNDATION
  ├─ SPU-13 central paper
  ├─ RPLU v2 paper
  ├─ Lucas MAC paper
  └─ SU3 coprocessor paper
       ↓
Week 2–3: EVIDENCE FREEZE
  ├─ Git tag
  ├─ Full regression log
  ├─ Wukong/Tang resource and timing tables
  └─ Hardware evidence summary
       ↓
Week 3–4: ARXIV SUBMISSION
       ↓
Week 4+: GRANT / ACADEMIC / COMMERCIAL OUTREACH
  ├─ NLnet/open-hardware draft after current-call verification
  ├─ MBIE/university partner-led draft
  ├─ NZ robotics/agritech evaluation outreach
  └─ Quantum/photonic research note with narrow Lucas/PHSLK scope
       ↓
IEEE/FCCM/FPL submission follows once measurement tables and references are
strong enough for peer review.
```

---

## Target Venues (Priority Order)

### Tier 1 (Prestige Impact Factor ~5)
1. **IEEE Micro** — Top-tier hardware venue
   - Deadline: Rolling (submit August 2026)
   - Format: 10–12 pages
   - Review: 3–4 months
   - Why: Architectural innovation focus fits determinism angle

2. **ASPLOS 2027** — Top-tier systems venue
   - Deadline: August 2026 (check if open)
   - Format: 13 pages
   - Review: 3 months
   - Why: Broader audience, highest prestige (but higher barrier)

### Tier 2 (Impact Factor ~2.5)
3. **FCCM 2027** — FPGA-focused venue
   - Deadline: Rolling (check 2026)
   - Format: 8–10 pages
   - Why: Natural fit, good acceptance rate

4. **FPL 2027** — Field-Programmable Logic
   - Deadline: March 2027
   - Format: 10 pages
   - Why: European venue, exact arithmetic friendly

---

## Measurement Targets

Audit note: the numeric targets below are historical planning estimates. Do not
quote them in papers, grants, or outreach unless regenerated from current
Artix/Tang/ECP5 builds and measured power data.

### Power Consumption
- **12 MHz:** Idle 5 mA, Active 15 mA, Peak 25 mA
  - Active: 49.5 mW @ 3.3V
- **24 MHz:** ~100 mW active (estimated)
- **50 MHz:** ~200 mW active (estimated)
- **Energy per operation:** ~3 µJ (from latency × power)

### Latency
- **M31 multiplier:** 2 cycles = 0.17 µs @ 12 MHz
- **A₃₁ inverter:** 76 cycles = 6.3 µs @ 12 MHz
- **SOM BMU:** 7 cycles = 0.58 µs @ 12 MHz
- **Full RPLU pipeline:** ~150 cycles = 12.5 µs @ 12 MHz

### Area (Tang 25K GW5A-25A)
- **LUT4:** ~7,900 / 8,256 = 96% utilization
- **DSP:** ~16 / 16 = 100% utilization
- **BRAM:** ~10 / 32 = 31% utilization
- **Max frequency:** ~70 MHz (5.8× headroom over 12 MHz spec)

### Comparative Advantage
- Quote only measured comparisons.
- The defensible current advantage is deterministic exact replay, not unmeasured
  speed or energy superiority.

---

## OSHWA Certification Checklist

Audit note: OSHWA is not ready as a completed custom ECP5 board claim. The
current ECP5 package is a concept/pre-certification package; see
`hardware/docs/ecp5_oshwa_deliverable_audit.md`.

**Timeline:** Week 7–8 (2-week process)

**Documentation to Create:**
- [ ] HARDWARE.md (500–1,000 words)
  - BOM, schematic, assembly, test procedure
- [ ] TESTING.md (300–500 words)
  - Functional test, bring-up, troubleshooting
- [ ] MAINTENANCE.md (200–400 words)
  - Known issues, contributions, roadmap
- [ ] SPDX license headers
  - Add to all source files: `SPDX-License-Identifier: CC0-1.0`

**Certification Process:**
1. Visit https://certification.oshwa.org/
2. Fill form (hardware category, description, GitHub URL)
3. Upload documentation PDFs
4. Pay $50 (Stripe)
5. Receive OSHWA # only after the hardware package is actually accepted
6. Add badge to GitHub README

---

## Community Promotion Channels

### Week 7: Research Networks
- **ArXiv:** cs.AR + eess.SP (immediate indexing, 24 hours)
- **Email:** Delft QuTech, Jiuzhang, Wildberger community
- **Reach:** ~500 researchers (direct contact)

### Week 10: Maker & Tech Communities
- **Hacker News:** Submit 9 AM Eastern for peak engagement
  - Headline: "RPLU 2.0: Deterministic Arithmetic Hardware (No Floating-Point)"
  - Target: 200+ upvotes, 100+ comments
- **Reddit:** 4 subreddits
  - r/FPGA, r/electronics, r/math, r/RaspberryPi
- **Reach:** ~10,000 makers/enthusiasts (organic)

### Week 11: Long-Form Content
- **Medium:** 2 blog posts (1,000–2,000 words each)
- **Dev.to:** Technical post (FPGA synthesis walkthrough)
- **YouTube:** 5–10 min hardware demo video
- **Reach:** ~1,000 developers/researchers (organic)

### Week 12: Industry + Press
- **Xilinx/AMD:** Innovation program outreach
- **Gowin:** Academic board donations
- **SparkFun:** Featured product
- **Podcast:** Embedded.fm or FPGA Design Mag
- **Reach:** ~500 industry professionals

**Total Projected Reach:** 12,000+ people across academia/industry/maker communities

---

## Success Metrics (12-Week Targets)

### Academic Track
- [ ] IEEE paper submitted (Week 6)
- [ ] ArXiv published + indexed (Week 7)
- [ ] 1,000+ ArXiv downloads (Month 1)
- [ ] 5+ research collaboration inquiries
- [ ] 5–10 citations (Year 1 baseline)

### Open-Source Track
- [ ] OSHWA concept package audited without claiming certification
- [ ] Public source release/tag tied to arXiv papers
- [ ] Community issues/discussions opened after papers are live
- [ ] Independent build reports or reproduction attempts tracked

### Promotion Track
- [ ] Targeted academic/industry outreach sent with paper links
- [ ] One technical blog post published after arXiv
- [ ] Demo video recorded if the current bench setup is stable
- [ ] Public feedback captured as issues or discussion threads

### Overall Impact
- [ ] Tier-1 journal publication path established
- [ ] Research interest validated
- [ ] Grant/partner conversations grounded in evidence, not projection

---

## Resource Checklist

### Existing Assets
- ✅ RTL code (10 verified modules)
- ✅ Full regression baseline is tracked in `docs/CURRENT_STATUS.md`
- ✅ LaTeX paper template + sections
- ✅ GitHub repository (public)
- ✅ Python/C++17 oracles and hardware evidence are tracked in
  `docs/hardware_evidence.md`

### To Acquire / Set Up
- 📦 INA226 current-sense module ($10, AliExpress)
- 📦 Oscilloscope + current probe (for jitter measurement)
- 📹 YouTube account (free)
- 📝 Medium / Dev.to accounts (free)
- 🔑 ArXiv account (free)

### Effort Estimate
- **Total:** 50–60 person-hours over 12 weeks
- **Per week:** ~4–5 hours
- **Critical path:** Measurements (Week 1–3) → Paper (Week 4–6)

### Cost Estimate
- **Minimal:** $60 (equipment + OSHWA fee)
- **With publication fee:** $2,060 (IEEE open-access waiver available)
- **Equipment:** Already available (oscilloscope, multimeter)

---

## Immediate Next Steps (Next 48 Hours)

1. **Review** `docs/spu13_central_paper.tex` as the foundation paper.
2. **Review** companion drafts: RPLU v2, Lucas MAC, and SU3.
3. **Keep** `docs/CURRENT_STATUS.md` and `docs/hardware_evidence.md` aligned
   with paper claims.
4. **Prepare** the evidence-pack checklist in
   `SPU13_MARKET_AND_GRANT_POSITIONING.md`.
5. **Defer** new synthesis work until the paper/grant source of truth is clean.

---

## Related Documents (In Repository)

**Existing Papers:**
- `docs/rplu_paper.tex` (746 lines, main template)
- `docs/rplu_paper_hw_section.tex` (120 lines, architecture)
- `docs/rplu_paper_tables.tex` (272 lines, results tables)
- `tools/rplu_paper_data.py` (data generation script)

**Related Strategy Docs:**
- `docs/RATIONAL_AI_FRAMEWORK.md` (18.5 KB, market positioning)
- `docs/QUANTUM_ERROR_CORRECTION_APPLICATIONS.md` (9.3 KB, QEC angle)
- `docs/MULTIPLATFORM_SOUTHBRIDGE_STRATEGY.md` (18.4 KB, future platforms)
- `docs/hardware_evidence.md` (silicon validation record)

**ISA & Architecture:**
- `knowledge/isa_reference.md` (26 opcodes, 19 hardware-verified)
- `docs/rplu_formal_spec.md` (formal specification)
- `docs/som_temporal_classification.md` (SOM theory)

---

## Glossary & Definitions

| Term | Definition |
|------|-----------|
| **RPLU v2** | Rational Process Logic Unit version 2 (A31 pipeline) |
| **Jet Algebra** | Algebraic structure for higher-order derivatives without floating-point |
| **M31** | Mersenne prime p = 2^31 − 1 (basis field) |
| **A_31** | Split biquadratic algebra F_p[u,v]/(u²−3, v²−5) |
| **Padé [4/4]** | [4/4] rational approximant (4th degree / 4th degree) |
| **SOM** | Self-Organizing Map (Kohonen classifier) |
| **BTU** | Bosonic Transform Unit (spatial routing) |
| **Determinism** | Bit-exact replay across runs, no floating-point rounding |
| **OSHWA** | Open Source Hardware Association (certification body) |

---

## FAQ

**Q: Why 12 weeks for publication?**
A: IEEE review cycle is 3–4 months, plus 3–4 weeks for measurements + paper finalization. ArXiv submission in parallel (Week 7) provides immediate visibility while IEEE review is ongoing.

**Q: Can we compress the timeline?**
A: Partially. Measurements (Week 1–3) are the critical path and cannot be skipped without losing credibility. Paper writing (Week 4–6) could be compressed to 2 weeks if all measurements are done early. Minimum: 8–9 weeks total.

**Q: What if IEEE rejects?**
A: Fallback plan is FCCM/FPL (Tier 2 venues). Both have good acceptance rates for FPGA work. Expected timeline: 2–3 month resubmission cycle.

**Q: Should we do OSHWA before or after IEEE?**
A: Keep the OSHWA documentation audit moving in parallel, but do not submit or claim certification for the custom ECP5 board until the KiCad/ERC/DRC blockers are closed.

**Q: What about GitHub stars and other public metrics?**
A: Treat stars as a byproduct, not an operating metric. The useful signal is serious reproduction attempts, technical feedback, research contacts, and evaluator interest.

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-06-29 | 1.0 | Initial publication strategy + 3 supporting documents |
| 2026-07-05 | 1.1 | Added grant/market source of truth, corrected critical path toward arXiv-first outreach, and marked stale estimates |

---

**Last Updated:** 2026-07-05
**Owner:** Core team (user)
**Status:** Active, audited
