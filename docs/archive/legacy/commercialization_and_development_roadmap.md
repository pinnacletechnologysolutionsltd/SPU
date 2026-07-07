# Commercialization and Development Roadmap

Date: 2026-07-05

This roadmap keeps SPU-13 fully open while giving the project a practical path
to money, users, certification evidence, and industrial credibility.

For the FPGA board ladder behind the dev-kit strategy, see
`docs/fpga_board_scaling_strategy.md`.

For grant and high-margin market positioning, see
`docs/SPU13_MARKET_AND_GRANT_POSITIONING.md`.

## Core Positioning

SPU-13 is an open deterministic exact-arithmetic geometric field processor for:

- exact geometric computation
- deterministic graphics and visual telemetry
- bounded control and robotics kinematics
- deterministic lattice simulation
- inspectable rational SOM/BMU classification
- RPLU lookup/correction surfaces
- industrial telemetry and control
- guarded interfaces to future non-von-Neumann coprocessors

The public claim should avoid competing with GPUs, NPUs, or tensor accelerators
on throughput. The defensible claim is determinism:

> Same inputs, same rational state, same trace, same output, across simulation,
> RTL, FPGA, and future board revisions.

Do not position SPU-13 as a general CPU/GPU replacement, LLM accelerator,
stochastic neuromorphic processor, quantum computer, or certified safety
controller. The canonical boundary is `docs/SPU13_IDENTITY_AND_BOUNDARIES.md`.

## Open Project Policy

The project should be completely open, but the brand should remain controlled.
Open hardware allows others to make, modify, distribute, and use the design; it
does not require clones to be treated as official SPU-13 products.

Licensing:

- SPU-13 is committed to maximum open-source impact. All RTL, PCB designs, schematics, software, firmware, tools, and documentation are released under the `CC0 1.0 Universal` (Public Domain) license.
- Trademarks, board names, certification marks, logos: reserved.

Open licenses should not try to restrict fields of use. The control surfaces are
documentation, warranty, certification claims, trademarks, and which reference
designs the project validates.

## Business Ladder

### 1. Public Dev Kits

Selling development kits is the best first commercial step, but only after a
small paid beta run. Do not jump directly into a large campaign until the board
has repeatable bring-up evidence.

Initial kit contents:

- SPU-13 FPGA board or carrier around a known FPGA module
- visual SOM/debug display or display header
- pre-flashed RPLU periodic pack
- UART/SPI/USB debug bridge
- example traces for SOM, RPLU, rotor, and Davis Gate
- open BOM, schematics, RTL, flash image tooling, and test scripts
- clear statement of what is proven, experimental, and not safety-certified

Recommended sequence:

1. Private bench prototype.
2. 5-10 trusted evaluator kits.
3. 25-50 paid alpha kits.
4. Public Crowd Supply-style campaign once manufacturing costs, support burden,
   lead time, and failure modes are known.

Crowdfunding works best as demand validation and community formation, not as a
substitute for manufacturing readiness.

### 2. Consulting

Consulting should start in parallel with dev-kit preparation. It can fund the
work without waiting for a campaign.

Offer fixed-scope services:

- FPGA bring-up and deterministic telemetry integration
- rational geometry / kinematics consulting
- RPLU table generation for robotics, materials, or calibration
- custom SOM/RPLU classifier demonstrations
- open hardware architecture review
- trace-verification and reproducibility reports

Avoid unlimited custom work. Keep every contract tied to reusable upstream
improvements when possible.

### 3. Custom FPGA Builds

The phrase should mean custom FPGA bitstreams, FPGA carrier boards, and
integration cores first, not custom FPGA silicon.

Near-term sellable work:

- custom SPU-13 subset builds for specific boards
- customer-specific RPLU packs
- deterministic telemetry bridges
- robotics correction cores
- industrial sensor classification cores

ASIC or chiplet work is a later-stage funding target after the dev-kit ecosystem
and FPGA evidence exist.

### 4. Vertical Packages

Verticals should be entered in this order:

| Vertical | Timing | Rationale |
|---|---|---|
| Industrial robotics | First | Strong fit, lower certification burden, clear RPLU correction value |
| Industrial telemetry / PLC adjunct | First | Deterministic state classification and visual audit trail |
| Education / research FPGA kit | First | Open project, visible demos, community growth |
| Drones / autonomous robots | Later | Useful, but guidance claims require careful framing |
| Space / aerospace | Later | High-value deterministic niche, high evidence burden |
| Automotive / self-driving | Later | Functional-safety process required before serious claims |
| Quant trading | Separate | Potentially lucrative but not a good public wedge |

## Quant Trading Position

Quant trading should not be the first public story. It can create conflicts with
the open community and tends to reward secrecy over shared validation.

Possible narrow angle:

- deterministic exact arithmetic kernels
- reproducible backtesting primitives
- low-latency FPGA experiments
- auditable simulation traces

Treat this as private consulting only if it funds the open work without pulling
the roadmap away from robotics and industrial control.

## Grant / Research Positioning

The project should pitch against research themes rather than stale program
names until an active solicitation is verified. Strong themes are deterministic
hardware, open microelectronics IP, low-SWaP control, quantum classical-control
interfaces, rational edge classification, and reproducible lattice simulation.

The grant story should lead with evidence:

> the same exact computation replayed in Python, C++, RTL, and FPGA silicon.

Current grant/pitch source of truth:
`docs/SPU13_MARKET_AND_GRANT_POSITIONING.md`.

Current audit note:

- NLnet remains relevant, but the exact open call must be checked before
  submission. On 2026-07-05 its general NGI Zero Commons Fund page says the
  final Commons call closed on 2026-06-01, while the apply page temporarily
  lists only NGI Taler and NGI Fediversity.
- MBIE remains relevant as a New Zealand research pathway, but the 2026
  Endeavour Fund round is contract-extension only and does not invite new
  applications. Treat MBIE as a partner-led track through universities, CRIs,
  or other current MBIE opportunities.
- Commercial and academic outreach should start after the arXiv papers are
  live, using the evidence pack rather than speculative performance claims.

## Aerospace, Drones, Guidance, and Space

SPU-13 may be useful for these domains because exact deterministic arithmetic is
valuable in navigation, guidance, attitude control, sensor fusion, and fault
monitoring. The public project should still avoid claiming flight readiness.

Near-term language:

> Research and development platform for deterministic guidance, navigation,
> telemetry, and verification experiments.

Avoid language like:

> Certified flight controller, autonomous weapons guidance, road-ready
> self-driving controller, or safety-critical replacement processor.

The first aerospace/space product should be a deterministic monitor or
co-processor, not the primary flight control path.

## Robotics First Product

The first serious product should be:

> SPU-13 Open Deterministic Robotics Kit

Core demos:

1. Rational rotor / six-step kinematics trace.
2. RPLU trajectory correction from injected drift.
3. SOM classifier assigning motion/contact/material state.
4. Visual display showing BMU, material ID, correction bin, Davis stability, and
   memory tier.
5. VM-to-RTL-to-FPGA trace replay.

This is fundable because it gives users something concrete:

- inspectable control state
- deterministic correction tables
- exact path replay
- no hidden floating-point model
- open design files

## Development Roadmap

### Phase 0: Stabilize and Demonstrate Before New Tang 25K

- Clean the test runner so generated SDK/build trees are not discovered.
- Implement the host visual renderer from existing SOM, ROTC, RPLU, and Davis
  traces.
- Produce deterministic trace artifacts under `build/`.
- Rebuild the rational robotics simulation harness.
  See `docs/rotc_robotics_bringup_plan.md`.
- Run SOM BMU trace replay and produce golden visual artifacts.
  See `docs/som_bringup_plan.md`.
- Add QSUB and DELTA RTL FSMs, then trace-verify against the VM.

### Phase 1: Replacement Tang 25K Bring-Up

- Re-run known flash/RPLU proof.
- Prove SDRAM hydration on the replacement board.
- Prove ROTC in silicon — see `docs/rotc_robotics_bringup_plan.md`.
- Prove SOM_CLASSIFY in silicon — see `docs/som_bringup_plan.md`.
- Capture UART telemetry and visual renderer replay.
- Validate RPLU periodic pack loading and runtime material update.

### Phase 2: Dev-Kit Alpha

- Freeze SPU-13 dev-kit v0.1 architecture.
- Build 5-10 internal/evaluator units.
- Write quickstart, bring-up, recovery, and known-limitations docs.
- Publish OSHWA source package draft.
- Record demos for robotics, visual SOM, RPLU material map, and Morse
  sonification.

### Phase 3: Paid Beta / Crowdfunding Readiness

Campaign should wait until:

- at least three physical units pass the same bring-up procedure
- BOM and assembly quotes are known
- failure/recovery instructions are written
- firmware/flash images are reproducible from source
- support channel is ready
- shipping regions, taxes, and compliance expectations are understood
- warranty language is clear

### Phase 4: Public Campaign

Best-fit campaign message:

> An open deterministic FPGA coprocessor kit for rational robotics, exact
> geometry, RPLU material lookup, and inspectable SOM classification.

Avoid overloading the campaign with every possible domain. Mention aerospace,
space, drones, and automotive as research directions, not as certified first
products.

## Immediate Next Steps

1. Finish the SPU-13 foundation paper and companion RPLU v2, Lucas MAC, and SU3
   papers.
2. Freeze a paper evidence tag with the current 107/107 regression result and
   Wukong/Tang silicon evidence.
3. Prepare a one-page project brief for academic, grant, and commercial
   outreach.
4. Prepare partner-led MBIE/university and NLnet/open-hardware proposal drafts.
5. Keep the Pico 2 and Colorlight i9 acquisition path small and non-blocking.
6. Keep the custom ECP5 board as an EE/funding-dependent evaluator, not a
   fabrication-ready design.
7. Resume synthesis bring-up after the docs/papers have a stable evidence
   baseline.

## References

- OSHWA open hardware basics and certification:
  https://certification.oshwa.org/basics.html
- CERN Open Hardware Licence v2 variants:
  https://cern-ohl.web.cern.ch/
- Crowd Supply guide and worldwide project platform:
  https://www.crowdsupply.com/guide
- EIC Accelerator deep-tech funding reference:
  https://eic.ec.europa.eu/eic-funding-opportunities/eic-accelerator_en
- SOM bring-up plan: `docs/som_bringup_plan.md`
- ROTC/Robotics bring-up plan: `docs/rotc_robotics_bringup_plan.md`
- FPGA board scaling: `docs/fpga_board_scaling_strategy.md`
