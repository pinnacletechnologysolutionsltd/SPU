# SPU-13 Photonic Compilation Research Track — Document Index

## Quick Links

| Document | Purpose | Status |
| --- | --- | --- |
| **PHOTONICS_QUICKSTART.md** | Start here! TL;DR overview | ✓ Complete |
| **spu_strategy/photonics_research_plan.md** | Full research program spec | ✓ Complete |
| **spu_strategy/photonics_precision_findings.md** | Why Model B fails + fix | ✓ Complete |
| **spu_strategy/SESSION_SUMMARY.md** | Session overview & next steps | ✓ Complete |
| **software/tests/test_photonic_models_smul.py** | Three-model framework | ⚠ Needs fix |
| **software/tests/debug_photonic_models.py** | Precision analysis tools | ✓ Complete |

## Key Commands

```bash
# Run the three-model investigation
python3 software/tests/test_photonic_models_smul.py

# Run precision debugging
python3 software/tests/debug_photonic_models.py

# View research roadmap
cat spu_strategy/photonics_research_plan.md

# View why Model B fails
cat spu_strategy/photonics_precision_findings.md

# Understand the session
cat spu_strategy/SESSION_SUMMARY.md
```

## What Is This?

A parallel research investigation into whether **the SPU-13 algebraic ISA can compile to optical transfer matrices with bounded error recovery**.

**Current Status:** Three-model framework implemented; Model B algorithmic error identified and fix documented.

## The Three Models

1. **Model A (Exact SPU)** — Ground truth oracle using SurdFixed64 arithmetic
   - Status: ✓ Working perfectly
   - Purpose: Baseline for all comparisons

2. **Model B (Ideal Optical)** — Noiseless WDM-encoded optical transformation  
   - Status: ⚠ Bug identified (rescaling formula wrong)
   - Purpose: Verify optical encoding can recover exact result
   - Fix: Remove σ_max rescale on detected power

3. **Model C (Noisy Optical)** — Model B with phase jitter, amplitude noise, loss
   - Status: 🔲 Blocked until Model B works
   - Purpose: Measure recovery probability vs. noise parameters
   - Next: Run 16,000 trials per noise level

## The Bug (In Plain English)

**The Problem:**
Model B was rescaling detected optical power by σ_max, a matrix normalization factor.

**Why It's Wrong:**
- σ_max ensures the transfer matrix is sub-unitary (passive physical constraint)
- It doesn't affect how we recover coefficients from measured power
- We should only divide by the encoding scale factor s

**The Fix:**
Remove the line that multiplies by σ_max. Quantization happens directly from power.

**Expected Result:**
Model B will then match Model A exactly (100% recovery with no noise).

## Next Steps (This Week)

1. Fix Model B rescaling (1 line of code change)
2. Verify A ≡ B (should now match perfectly)
3. Run Model C sweep (16,000 trials per noise level)
4. Generate results table (phase jitter vs. recovery rate)

## Why This Matters

This isn't just "can we build a photonic computer?" It's "can we systematically compile a discrete algebraic ISA into optical primitives with measurable error bounds?"

That's a more interesting research question—and more likely to result in an actual research contribution.

## How to Read the Documents

**If you have 5 minutes:** Read PHOTONICS_QUICKSTART.md

**If you have 15 minutes:** Read PHOTONICS_QUICKSTART.md + photonics_precision_findings.md

**If you have 30 minutes:** Read SESSION_SUMMARY.md + photonics_research_plan.md

**If you want to understand everything:** Read all documents in order:
1. PHOTONICS_QUICKSTART.md
2. photonics_research_plan.md
3. photonics_precision_findings.md
4. photonics_debugging_report.md
5. SESSION_SUMMARY.md

## Files & Locations

```
/home/john/Projects/hardware/SPU/
├── PHOTONICS_QUICKSTART.md              ← Start here
├── RESEARCH_TRACK_INDEX.md              ← This file
├── photonics/
│   └── photonics.md                     (amended per feedback)
├── spu_strategy/
│   ├── photonics_research_plan.md       (what we're investigating)
│   ├── photonics_precision_findings.md  (why Model B fails)
│   ├── photonics_debugging_report.md    (analysis)
│   └── SESSION_SUMMARY.md               (session overview)
└── software/tests/
    ├── test_photonic_models_smul.py     (three-model framework)
    ├── debug_photonic_models.py         (precision tools)
    ├── test_photonic_surd_oracle.py     (existing)
    ├── test_photonic_noise_model.py     (existing)
    └── test_smul_photonic_experiment.py (existing)
```

## Status Dashboard

| Phase | Component | Status | Next Action |
| --- | --- | --- | --- |
| **1** | Model A Oracle | ✓ Complete | Use as baseline |
| **1** | Model B Ideal | 🔧 Bug found | Apply documented fix |
| **1** | Model C Noisy | 🔲 Blocked | Unblock once B fixed |
| **1** | Debugging | ✓ Complete | Done |
| **2** | Scattering | ☐ Future | Phase 2 work |
| **2** | Tolerance | ☐ Future | Phase 2 work |
| **3** | Hardware | ☐ Conditional | Only if 1-2 succeed |

## Key Research Questions

1. **What is the recoverable noise envelope?**
   - How large can σ_φ be before BQE fails?
   - Is there a hard threshold or gradual degradation?

2. **Is WDM encoding viable for silicon photonics?**
   - Can we isolate wavelength channels reliably?
   - How does chromatic dispersion affect recovery?

3. **What physical design constraints emerge?**
   - Temperature stability needed?
   - Phase delay sensitivity (SROT.60)?
   - Fabrication tolerances?

## Expected Outcome

By end of Phase 1:
- Model C will show recovery probability vs. noise parameters
- We'll identify the "sweet spot" (e.g., σ_φ ≤ 3° → 100% recovery)
- We'll have a concrete falsifiable result

This leads to:
- **If successful:** "SPU-13 compiles to photonics with X° tolerance"
- **If limited:** "Encoding breaks at Y° due to [specific cause]"
- **Either way:** Publishable research

## Contact & Guidance

- See PHOTONICS_QUICKSTART.md for command reference
- See photonics_research_plan.md for detailed specifications
- See photonics_precision_findings.md for current bug status
- See SESSION_SUMMARY.md for session context

---

**Last Updated:** 2026-08-19  
**Research Track Status:** Initialization Complete  
**Ready For:** Model B fix and Model C sweep
