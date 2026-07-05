# SPU-13 Market, Research, and Grant Positioning

Date: 2026-07-05

This is the current source of truth for grant, research, and commercial
positioning. It should be read with:

- `docs/CURRENT_STATUS.md` for what is actually proven now
- `docs/hardware_evidence.md` for silicon/RTL evidence
- `docs/SPU13_IDENTITY_AND_BOUNDARIES.md` for claim discipline
- `docs/fpga_board_scaling_strategy.md` for board acquisition order
- `hardware/docs/ecp5_oshwa_deliverable_audit.md` for OSHWA board readiness

## Strategic Position

The immediate strategy is:

1. Publish the SPU-13 foundation paper and companion RPLU v2, Lucas MAC, and
   SU3 papers as arXiv preprints.
2. Freeze a reproducible evidence tag with the current Tang 25K and Wukong
   Artix-7 proofs.
3. Use the papers and evidence package for grants, academic collaboration, and
   targeted commercial outreach.
4. Keep synthesis/bring-up moving on current hardware while larger boards and
   custom ECP5 hardware remain funding-dependent.

The project is now credible enough for research outreach because the core math
has passed across software oracles, RTL tests, and targeted FPGA silicon
proofs. The public pitch must still be evidence-bounded: this is a deterministic
exact-arithmetic FPGA coprocessor project, not a certified controller or a
finished commercial chip.

## One-Line Pitch

SPU-13 is an open deterministic exact-arithmetic coprocessor for rational
geometry, bounded robotics/control traces, reproducible lattice simulation, and
inspectable topological classification.

## Best First Funding Story

Lead with reproducibility:

> The same exact computation is replayed in Python, C++, Verilog RTL, and FPGA
> silicon, with no floating-point drift and explicit invariant checks.

That story fits several audiences:

| Audience | Best Frame | Evidence To Lead With |
|---|---|---|
| Open-source infrastructure funders | Open FPGA/silicon IP, reproducible hardware, open tooling | arXiv papers, OSHWA audit, Yosys/nextpnr flows, source release |
| NZ science / university partners | Deterministic computing platform for robotics, simulation, and open microelectronics | foundation paper, Wukong/Tang silicon proofs, student-sized work packages |
| Robotics/agritech companies | Exact trace replay, bounded correction, deterministic telemetry | ROTC/six-step robotics proof, RPLU2 Padé proof, SOM/BMU classification |
| Quantum/photonic research groups | Exact algebraic sidecar for phase/template checks and classical-control preprocessing | Lucas MAC paper, PHSLK, bounded sidecar language |
| Commercial FPGA users | Fixed-scope deterministic kernels and trace-verifiable hardware | build scripts, board ladder, smoke tests, reusable IP boundaries |

## Current Funding Lane Audit

Program names change. Verify every call before submitting.

| Lane | Current Status | Recommended Action |
|---|---|---|
| NLnet / NGI | As of 2026-07-05, NLnet's general NGI Zero Commons Fund page says its final call closed on 2026-06-01. The apply page says proposals are temporarily limited to NGI Taler and NGI Fediversity with a 2026-08-01 deadline, and regular open calls are expected to reopen after summer. | Prepare a reusable NLnet-style proposal now, but do not force SPU-13 into Taler/Fediversity unless there is a genuine scope fit. Recheck the open-call page before submission. |
| MBIE Endeavour | As of 2026-07-05, MBIE says the 2026 Endeavour round is contract-extension only and will not invite new applications. | Do not plan on a solo 2026 Endeavour application. Use the papers to find a university/CRI partner and monitor MBIE's open/upcoming funding page for better-fit calls. |
| MBIE / NZ science system | MBIE has other open/upcoming science and innovation opportunities, including capability and international collaboration calls that may require partners. | Treat MBIE as a partner-led track: university student project, lab collaboration, or industry-linked proposal. |
| NZ robotics/agritech | No formal grant dependency; outreach can begin after papers. | Prepare a one-page deterministic robotics brief and ask for evaluation conversations, not investment first. |
| Academic collaboration | Strong fit after arXiv. | Target ECE/FPGA, robotics/control, exact computation, open hardware, and quantum classical-control groups. |
| Commercial consulting | Can start small before grants. | Offer fixed-scope work only: deterministic FPGA kernels, RPLU table generation, trace-verification reports, board bring-up review. |

Official references checked on 2026-07-05:

- NLnet apply page: `https://nlnet.nl/propose/`
- NLnet NGI Zero Commons Fund: `https://nlnet.nl/commonsfund/`
- MBIE Endeavour Fund: `https://www.mbie.govt.nz/science-and-technology/science-and-innovation/funding-information-and-opportunities/investment-funds/endeavour-fund`
- MBIE open/upcoming funding: `https://www.mbie.govt.nz/science-and-technology/science-and-innovation/open-and-upcoming-science-and-innovation-funding-opportunities`

## Outreach Order

Do not scatter outreach before the papers exist. The sequence should be:

1. Finish the foundation SPU-13 paper.
2. Finish or at least preprint the RPLU v2, Lucas MAC, and SU3 papers.
3. Tag the repository with the paper evidence baseline.
4. Build a compact evidence pack:
   - paper PDFs
   - `docs/CURRENT_STATUS.md`
   - `docs/hardware_evidence.md`
   - latest test-regression result
   - resource/timing tables for Tang 25K and Wukong Artix-7
   - one-page board/funding plan
5. Send targeted outreach:
   - NZ university ECE/robotics supervisors
   - NZ robotics/agritech companies
   - open hardware / open silicon funders
   - deterministic computing and FPGA researchers
   - quantum/photonic groups only with the narrow Lucas/PHSLK sidecar angle

## Academic / Commercial Targets

Treat this as a contact map, not an endorsement list.

| Group Type | Examples | Best Ask |
|---|---|---|
| NZ robotics/agritech | Robotics Plus, Halter, DairyNZ-adjacent robotics teams, university robotics labs | "Would you evaluate a deterministic trace-replay coprocessor for bounded kinematics/correction?" |
| NZ universities | Auckland, Canterbury, Victoria, Otago, AUT engineering/computing groups | "Could this become a student project or funded open hardware research collaboration?" |
| Open hardware / FPGA groups | OSHWA community, open silicon/open FPGA researchers, Yosys/nextpnr ecosystem | "Can we validate this as reproducible open FPGA IP?" |
| Quantum / photonic groups | Xanadu, QuTech, other classical-control/QEC hardware groups | "Is an exact algebraic phase/template sidecar useful as a preprocessing kernel?" |
| Industrial deterministic computing | PLC, telemetry, embedded control, verification-heavy users | "Would exact trace replay and invariant-guarded commits solve a real audit problem?" |

## Safe Claim Language

Use:

- "deterministic exact-arithmetic FPGA coprocessor"
- "bit-exact replay across oracle, RTL, and FPGA proofs"
- "research and development platform"
- "current evidence covers split probes and constrained Artix integration"
- "larger boards are full-integration targets"
- "custom ECP5 hardware is evaluation-ready as a concept, not fab-ready"

Avoid:

- "certified safety controller"
- "GPU replacement"
- "quantum computer"
- "general AI chip"
- "full custom silicon is solved"
- "OSHWA certified" before certification is actually granted
- "MBIE/Endeavour funding path" without current call verification
- any performance or energy claim without measured data

## Evidence Pack Checklist

Before sending serious grant or partner outreach:

- [ ] arXiv links for central SPU-13, RPLU v2, Lucas MAC, and SU3
- [ ] Git tag for the paper baseline
- [ ] `python3 run_all_tests.py` log stored under `build/evidence/`
- [ ] Wukong Artix resource/timing table
- [ ] Tang 25K probe resource/timing table
- [ ] RP2350/Wukong J11 smoke-test captures
- [ ] one-page project brief
- [ ] one-page budget with small, medium, and large ask levels
- [ ] OSHWA status clearly marked as concept/pre-certification if not certified

## Budget Ladders

| Ask Size | Use |
|---:|---|
| NZ$1k-3k | Instruments, Pico 2, Colorlight i9, logic analyzer, power meter, spare boards |
| NZ$5k-15k | Contract review by EE, test coupons, better development PC/host, evaluation boards |
| NZ$25k-75k | Student project, robust Artix/Kintex/ECP5 evaluation stack, documentation sprint |
| NZ$100k+ | Contract EE for custom board, multi-board prototype run, measurement equipment, part-time research assistant |

## Next Concrete Actions

1. Finish paper drafts first.
2. Keep current Wukong/Tang evidence stable; do not disturb known-good wiring
   for a speculative transport upgrade.
3. Prepare the one-page project brief and evidence bundle.
4. Draft a partner-led MBIE/university note.
5. Draft an NLnet/open-hardware note, then recheck the exact open call before
   submission.
6. Start small NZ robotics outreach only after the papers are visible.
