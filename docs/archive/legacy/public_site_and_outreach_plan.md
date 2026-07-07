# SPU-13 Public Site and Outreach Plan

Date: 2026-07-05

This is the lightweight plan for building a public-facing SPU-13 presence while
the papers and hardware evidence mature. The repository remains the engineering
source of truth; the website and social channels should point back to the repo,
papers, and evidence logs.

## Goal

Create several credible contact surfaces:

- a public website or GitHub Pages documentation site
- LinkedIn profile/project updates
- optional X posts for FPGA/open-hardware visibility
- GitHub Discussions or issues for technical follow-up
- a clear contact page for research, grants, consulting, and collaboration

The public voice should be evidence-bound: explain the architecture, math, and
hardware proofs without claiming a finished commercial chip or certified control
system.

## Recommended Site Structure

Start with a small static site. GitHub Pages is enough.

```text
/
  Start Here
  Architecture
  Mathematics
    Quadray Coordinates
    Rational Trigonometry
    Synergetics / IVM Background
    M31 / A31 Arithmetic
    Lucas Phinary Arithmetic
  Hardware Evidence
    Tang Primer 25K
    Wukong Artix-7
    ECP5 / Colorlight i9 Plan
  Papers
    SPU-13 Foundation Paper
    RPLU v2 Paper
    Lucas MAC Paper
    SU3 Coprocessor Paper
  Bring-Up Logs
  Funding / Collaboration
  Contact
```

## First Five Posts

1. **What is SPU-13?**
   - One-page overview of deterministic exact-arithmetic computing.
   - Link to `docs/SPU13_IDENTITY_AND_BOUNDARIES.md`.

2. **Why Quadray Coordinates?**
   - Explain tetrahedral/IVM geometry as the native coordinate model.
   - Keep this educational, not overclaimed.

3. **No Floating-Point Drift**
   - Explain exact rational/finite-field closure.
   - Use Lucas and ROTC zero-drift examples.

4. **From Python Oracle to FPGA Silicon**
   - Explain the evidence ladder: Python, C++, RTL, synthesis, routed image,
     hardware telemetry.
   - Link to `docs/hardware_evidence.md`.

5. **Artix-7 Bring-Up Notes**
   - Wukong JTAG, J11 SPI, LUCAS/SU3/ROBOTICS/RPLU2PADE proofs.
   - Show what passed and what remains experimental.

## Channel Strategy

| Channel | Purpose | Cadence |
|---|---|---|
| Website / GitHub Pages | Canonical public explanation | Update whenever docs/papers change |
| GitHub README | Short entry point and build links | Keep concise and current |
| LinkedIn | Grants, robotics, universities, EEs, companies | 1 useful post every 1-2 weeks |
| X | FPGA/open-hardware/math visibility | Optional; short links to real posts |
| GitHub Discussions | Technical questions and collaboration | Enable after arXiv or first public push |

## Writing Rules

Use:

- deterministic exact-arithmetic FPGA coprocessor
- bit-exact replay across oracle, RTL, and FPGA proofs
- research and development platform
- current evidence covers split probes and constrained Artix integration

Avoid:

- certified safety controller
- GPU replacement
- quantum computer
- general AI chip
- production silicon
- measured speed/energy claims without data

## Implementation Sequence

1. Create a minimal `website/` or `docs/site/` directory.
2. Pick MkDocs Material, Jekyll, or plain GitHub Pages.
3. Add `Start Here`, `Architecture`, `Hardware Evidence`, `Papers`, and
   `Contact` pages first.
4. Publish the first post: "What is SPU-13?"
5. Add links from `README.md`.
6. Post the article link on LinkedIn with a short, evidence-bound summary.
7. Add one technical explainer per week or fortnight.

## Contact Page Content

Include:

- project summary
- GitHub repository link
- arXiv links once available
- collaboration interests:
  - deterministic FPGA arithmetic
  - rational robotics/control
  - open hardware / open silicon
  - exact lattice simulation
  - quantum classical-control sidecars
- contact method
- clear note that SPU-13 is currently a research and development platform, not
  a certified safety product

## Near-Term Checklist

- [ ] Choose site generator.
- [ ] Draft the `Start Here` page.
- [ ] Draft the `What is SPU-13?` post.
- [ ] Add a public contact page.
- [ ] Add website link to `README.md`.
- [ ] Prepare LinkedIn announcement after the first page is live.
- [ ] Keep all claims aligned with `docs/CURRENT_STATUS.md` and
      `docs/SPU13_MARKET_AND_GRANT_POSITIONING.md`.
