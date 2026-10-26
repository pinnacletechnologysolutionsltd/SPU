# SPU-13 Photonic Architecture

**Status: HYPOTHETICAL-BUT-COMPLETE.** This document describes what an
SPU-13 photonic backend implementation would have to look like to
satisfy the already-frozen REGEN ISA contract and the already-validated
compile-time reliability model — **not a chip that exists, not a claim
that one is being built.** Every parameter below carries one of four
status labels (§0). Do not cite anything here as `silicon-verified`
without a matching entry in
[`docs/hardware_evidence.md`](hardware_evidence.md) — none exists for
this track and none is implied.

**Scoped 2026-08-24 (`docs/PHOTONIC_SPU13_ARCHITECTURE_SPEC.md`'s prior
revision), drafted 2026-08-24 after Halt-and-Flag review.** Directive:
"broader system architecture, hypothetical-but-complete" — include the
physical component picture, not just the logical/interface layer, with
every physical claim explicitly labeled. This document is the third
posture change on this branch in one day: E18–E21 (mechanism discovery)
→ the corrected-reliability-model contract (engineering validation) →
`docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` (interface consolidation)
→ this document (what a hypothetical implementation of that interface
would look like as a system).

## 0. Status hierarchy (applies to every claim below)

Four tiers, stated once here, then used as inline tags throughout:

- **[ESTABLISHED]** — backed by real RTL, a frozen ISA contract, or a
  frozen/reproducible simulation result with its own evidence artifact.
  Includes testbench-verified RTL; **does not include silicon** unless a
  `hardware_evidence.md` citation is given inline.
- **[SIM]** — the literal value `PhotonicQuadrayBackend` /
  `photonic_experiment_config.py` uses (e.g. `n_eff=2.45`, `1550nm`,
  `dn_eff_dT=1.86e-4/K`). Physically plausible (real telecom band,
  textbook-order silicon-photonics constant), traceable, reproducible —
  **never validated against a real device.** [SIM] means "the
  simulator's own number," not "measured."
- **[UNRESOLVED]** — an architectural question this document surfaces
  because current evidence doesn't distinguish between multiple real
  possibilities. Not a placeholder value — an explicit open question.
- **[NOT CLAIMED]** — silicon feasibility, yield, power, area, fab
  compatibility, timing/performance. This document makes zero claims in
  this tier; sections that would otherwise need one say so and stop.

A number with no tag anywhere near it is a defect in this document.

## 1. System overview

```
SPU-13 digital core (existing RTL)
      |
      v
opcode 0x09 (REGEN), .block K          <- [ESTABLISHED], §2
      |
      v
backend measurement interface           <- [ESTABLISHED] as an RTL
(bk_qr*_meas, bk_sigma_exp, bk_angle_k)    signal bus, §3
      |
      +-- digital reference backend      <- [ESTABLISHED], implemented,
      |   (fpga_chain.v, current)           this is what actually runs today
      |
      +-- photonic backend                <- [SIM]/[UNRESOLVED], §4 —
          (hypothetical, this document)       does not exist in RTL/silicon
```

The digital SPU-13 core already has a real, RTL-implemented backend
abstraction boundary for REGEN — not a design proposal, an existing fact
(§2, §3). A photonic implementation is one hypothetical occupant of the
"backend" slot in that diagram, alongside the digital reference backend
that already exists and runs today. This document describes what would
need to be true of that hypothetical occupant; it does not modify or
threaten the existing digital path.

## 2. ISA extension point — resolved, no new opcode

**[ESTABLISHED].** The question this section set out to answer —
whether photonic dispatch needs a new opcode — is already answered by
existing, frozen work, not something this document decides:

- `knowledge/isa_reference.md` was missing a `0x09` entry until this
  session (fixed as part of drafting this document — a documentation
  gap, not a missing feature). **REGEN (opcode `0x09`, `.block K`) is a
  real, RTL-implemented, architecturally frozen SPU-13 instruction**
  (`hardware/rtl/core/spu13/spu13_regen.v`, wired into
  `spu13_core.v:1025`, `core_regen_opcode = (eff_inst_word[63:56] ==
  8'h09)`; ISA semantics frozen in
  `spu_strategy/contract_regen_isa_0x09_2026-08-20.md`, "REGEN v1").
- Its **governing rule is exactly the one this section was scoped to
  investigate**: *"the ISA is not modified to accommodate any
  substrate — photonic, FPGA, ASIC, or digital. A substrate that cannot
  satisfy this contract is an implementation failure, not a reason to
  change the ISA."* A photonic implementation does not get a new
  opcode; it has to satisfy REGEN's existing architectural semantics
  (`S̃_K ↦ S_K`, idempotence, fault-preserves-state) or it isn't a
  conforming REGEN implementation.
- The reference model already enumerates backend substitutability as a
  real, working abstraction, not a proposal: `software/tests/regen_emulator.py`
  implements three interchangeable layer-2 backends —
  `PhotonicBackend`, `FpgaReferenceBackend`, `DigitalSurdBackend` — all
  satisfying the same layer-3 REGEN projection. **This document's
  hypothetical photonic architecture is filling in a slot the ISA
  contract already named and the reference model already exercises**,
  not inventing a new mechanism.
- Substrate opacity has already been adversarially tested at the RTL
  level, testbench-only: *"No substrate-specific detail leaked through
  the tested REGEN architectural boundary under the Stage-C
  populations"* (232 boundaries × 3 phase conditions, zero leaks —
  `spu_strategy/contract_regen_stageC_2026-08-20.md`, "testbench-verified,
  no silicon claim"). This is evidence about the boundary's opacity in
  the tests run, not a universal proof, and not silicon.

**What this means for §1's diagram:** the digital-core-to-backend split
already exists and is real; this document's job is only §4 (what a
photonic occupant of that slot would need to look like), not inventing
the slot itself.

## 3. Backend abstraction contract

**[ESTABLISHED]** for the interface signature; **[NOT CLAIMED]** that a
photonic implementation exists to satisfy it. Two layers, kept separate
deliberately:

**RTL-level interface** (real, from `spu13_regen.v`/`fpga_chain.v`): any
backend feeding `spu13_regen` must supply, per REGEN boundary:
`bk_qr0_meas_{a,b,c,d}`, `bk_qr1_meas_{a,b,c,d}` (42-bit measurement
words), `bk_sigma_exp0`/`bk_sigma_exp1` (per-lane scale exponent),
`bk_angle_k` (accumulated common-mode rotation), and `bk_valid`. The
existing digital reference backend (`fpga_chain.v`) is one concrete,
already-working implementation of this interface — a fixed-point
Q2.40 chain, **not** a photonic one. A photonic backend would need to
drive the same signal bus with values derived from a real optical
measurement instead of a digital fixed-point chain — what those optical
measurements would need to look like is §4/§5.

**Reliability-level interface** (from
`docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` §1, restated here so this
document is self-contained, not re-derived): the adopted whole-chain
estimator is `P_chain = Π P_event(m0, sigma_det)`, conservative by
construction; the fitted per-event law is
`P_event(m0, sigma_det) = sigmoid(beta·(a − log2(sigma_det) − m0))`,
`a=-4.79, beta=3.19` — **[SIM]**, fit for
`PhotonicQuadrayBackend.SCALE=0.1, deltaT=2.0` only, not a physical
constant. A photonic backend's actual detector noise floor
(`sigma_det`) is what would need to be measured against this law once a
real device exists; nothing here supplies that number.

## 4. Physical component picture

**Rule, stated explicitly before anything else in this section
(Halt-and-Flag amendment):** a simulator lane or field component is a
**logical representation of computational state**, not a physical
resource. `fld = [[0j]*4 for _ in range(13)]` (13 lanes × 4 complex
components, `test_regen_equivalence.py:58`) describes what the *state*
looks like inside the exact-arithmetic/behavioral model — it must never
be read as "the chip needs 13×4 physical channels" without an explicit,
separately-justified mapping from logical state to physical resource.
No such mapping exists yet (§4's channel-count entry below).

| Stage | What it does | Grounding | Label |
|---|---|---|---|
| Encode | Digital SurdFixed64/Quadray value → optical field, WDM dual-rail: `E = s·(v⁺ − v⁻)`, `SCALE=0.1` | `PHOTONICS_MODEL_STATUS.md` Model B §1 | [SIM] |
| Propagate | Passive transfer matrix `M(c,d)`, normalized by `sigma_max` for passivity | `PHOTONICS_MODEL_STATUS.md` Model B §2–3 | [SIM] |
| Phase / LO tracking | `dphi = K_RAD · deltaT`, `K_RAD = (2π/1550nm)·deltaL·dn_eff_dT`; real telecom wavelength, textbook-order silicon thermo-optic coefficient (`n_eff=2.45`, `dn_eff_dT=1.86e-4/K`, `deltaL≈6.43µm`) | `test_regen_equivalence.py:206`, `photonic_experiment_config.py` `PhysicalParams` | [SIM] |
| Detect / readout | Dual-rail photodetection, noise injected at readout (`sigma_det`), BQE quantization back to integer state | `PHOTONICS_MODEL_STATUS.md` Model B §4–5; design-rule doc §1 | [SIM] |
| REGEN commit | Whole-state commit into `spu13_regen`'s `bk_*` interface (§3) | `spu13_regen.v` | [ESTABLISHED] (RTL exists; photonic driver of this interface does not) |

**Channel count — [UNRESOLVED], not a placeholder.** The logical state
is 13 lanes × 4 components; dual-rail encoding roughly doubles whatever
physical channel count follows from a chosen mapping. Whether real
hardware would run on the order of 100+ simultaneous WDM channels, or
achieve the same logical state via temporal multiplexing, lane
multiplexing, multiple photonic subarrays, a hybrid spatial/WDM scheme,
or some other architecture entirely, **is not distinguished by any
evidence produced by this branch.** This is a real architectural
decision a future contract would need to make, not a number this
document should invent to fill a table cell.

**Timing — [NOT CLAIMED], stated as unspecified rather than filled with
a placeholder.** `PhotonicQuadrayBackend` contains no propagation,
modulation, detector, ADC, REGEN, or control timing model of any kind.
No latency or throughput number appears anywhere in this document,
because none would mean anything — a placeholder here would be actively
misleading rather than merely provisional, so this section omits one
rather than including one for completeness.

## 5. Noise/reliability budget interface

Restatement of `docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` §1's
formulas as **the interface a real component selection would need to
satisfy** — not a claim that any component satisfies it:

```
m0,safe(sigma_det, P_target) = a - log2(sigma_det) - ln(P_target/(1-P_target))/beta
sigma_det,max(m0_worst, P_target) = 2^(a - m0_worst - ln(P_target/(1-P_target))/beta)
```

`a=-4.79, beta=3.19` — **[SIM]**, per §3. If a photonic device with a
measured `sigma_det` ever exists, these formulas (unchanged) are how its
noise floor would translate into a required REGEN period `M` or a
maximum tolerable detector noise budget, given a target per-event
reliability `P_target`. No number in this section is a device
specification; all of it is a conversion formula waiting for a device
number nobody has measured yet.

## 6. Non-goals

- **[NOT CLAIMED], explicitly:** real device part numbers or vendor
  selection; real timing/clock architecture; thermal or packaging
  design; cost/manufacturability; silicon feasibility, yield, power,
  area, or fab compatibility; any RTL or silicon claim for a photonic
  implementation (the digital REGEN RTL's own silicon status is
  unrelated — see §2's citations, none of which claim silicon).
- **§4's channel-count question is surfaced, not resolved** — this
  document does not pick an answer to have one.
- **No modification to the ISA, `spu13_regen.v`, or `fpga_chain.v`** —
  §2's governing rule (the ISA doesn't change to accommodate a
  substrate) applies to this document too; it describes a hypothetical
  occupant of an existing slot, it does not propose changing the slot.
- **No reopening of E18–E21 or the corrected-reliability-model
  contract** — their conclusions are restated (§3, §5), not
  re-examined.
- **No corrected (non-conservative) reliability estimator** — §5 uses
  only the adopted conservative law; the rejected corrected estimator
  (`docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` §1) is out of scope
  here as everywhere else on this branch.

## 7. Evidence ledger — mandatory pre-publication audit gate

Every numerical parameter used anywhere above must appear here. The
converse is not required — this table may contain simulator parameters
this document doesn't happen to use.

| Parameter | Value | Label | Source |
|---|---:|---|---|
| REGEN opcode | `0x09` | [ESTABLISHED] | `spu13_core.v:1025`, `contract_regen_isa_0x09_2026-08-20.md` |
| Substrate-opacity test | 232 boundaries × 3 phase conditions, 0 leaks | [ESTABLISHED] (testbench, no silicon) | `contract_regen_stageC_2026-08-20.md` |
| `lambda0` | 1550 nm | [SIM] | `PhysicalParams`, `photonic_experiment_config.py` |
| `n_eff` | 2.45 | [SIM] | `PhysicalParams` |
| `dn_eff_dT` | 1.86e-4 /K | [SIM] | `PhysicalParams` |
| `deltaL_a`, `deltaL_b` | 6.4322e-6 m | [SIM] | `PhysicalParams` |
| WDM encode scale | `SCALE=0.1` | [SIM] | `PhotonicQuadrayBackend` |
| Fitted recovery law | `a=-4.79, beta=3.19` | [SIM] | design-rule doc §1 |
| Lane/component count | 13 × 4 | [ESTABLISHED] (logical state, not physical) | `test_regen_equivalence.py:58` |
| Physical channel count | — | [UNRESOLVED] | §4 |
| Latency/throughput | — | [NOT CLAIMED] | §4 |

## References

- `docs/PHOTONIC_REGEN_COMPILATION_CONTRACT.md` — §1/§3, restated here
  in §3/§5.
- `spu_strategy/contract_regen_isa_0x09_2026-08-20.md` — REGEN v1,
  frozen ISA semantics, §2's authority.
- `spu_strategy/contract_regen_stageA_2026-08-20.md`,
  `contract_regen_stageC_2026-08-20.md` — RTL implementation and the
  substrate-opacity adversarial test, §2/§7.
- `hardware/rtl/core/spu13/spu13_regen.v`, `fpga_chain.v` — the real RTL
  §2/§3 cite.
- `software/tests/regen_emulator.py` — the three-backend reference
  model, §2.
- `knowledge/isa_reference.md` — canonical ISA table, `0x09` entry added
  2026-08-24 as part of drafting this document.
- `spu_strategy/PHOTONICS_MODEL_STATUS.md`,
  `software/tests/test_regen_equivalence.py`,
  `software/tests/photonic_experiment_config.py` — [SIM] sources, §4/§5.
- `docs/SPU4_ABI.md` — the RTL-grounded ABI-spec pattern this document
  cannot yet match (§0) — the model for what "real" looks like if this
  track ever gets a photonic RTL/silicon implementation.
