# Engineering Contract: REGEN (0x09) — First-Class Regeneration-Boundary Instruction

**Date:** 2026-08-20
**Contract ID:** `contract_regen_isa_0x09_2026-08-20.md`
**Status:** FROZEN — **REGEN v1, architectural semantics frozen**
(machine-actionable; supersedes the DRAFT ISA proposal's open items; all §7
decisions resolved; re-affirmed and tagged v1 on 2026-08-20 after Stage C).

**Authority:** This contract is the **authoritative document** for REGEN
semantics. The photonic experiments and the Stage A–C artifacts are the
**evidence base** (appendix A), not normative sources: where any experiment
or implementation artifact conflicts with this contract, this contract
governs.

**Roles:**
- **Spec Author:** John + Deep Code. Grounded in the seven frozen photonic
  experiments (`results/sweeps/*_frozen_v1_2026-08-20.json`), the decision-
  complete ISA proposal (`spu_strategy/ISA_REGEN_ARCHITECTURE_PROPOSAL_2026-08-20.md`),
  and the executable reference model (`software/tests/regen_emulator.py`).
- **Halt-and-Flag Implementer:** pre-execution review of this contract before
  any Verilog/SurdLang implementation.
- **Integration Auditor:** executes §4 verification gates; evidence gatekeeper
  (no unbacked "silicon-verified" claims).

---

## 0. Architectural Freeze Declaration (REGEN v1)

REGEN is an **architectural component of SPU-13**, not an experimental idea.
The ISA semantics are frozen; implementations are interchangeable below the
boundary.

**This contract defines (architectural, frozen):**

- opcode `0x09`;
- `.block K` block assembly and legal-operation counting (§3);
- valid/invalid REGEN (the `S̃_K ↦ S_K` projection, §2.2);
- `K = 0` (empty block) as a true pass-through — `REGEN(REGEN(S)) = S`;
- fault behavior (REGEN_PREC: a fault commits nothing and preserves state);
- state-commit semantics (whole-state; a fault cannot commit stale state);
- idempotence (`REGEN(REGEN(S)) = S` — permanent architectural invariant);
- the architectural state after REGEN (exact, canonical);
- implementation obligations (the declared regeneration envelope, §2.5).

**This contract does NOT define (implementation-specific, below the boundary):**

- photonic interferometer geometry or optical path lengths;
- σ normalization / Σ_total bookkeeping (§2.4);
- detector architecture or receiver gain trim hardware;
- temperature-sensor implementation or the thermal reference;
- the compensation law's Taylor approximation or its precision;
- any fixed-point representation (e.g. Q2.30/Q2.40) or FPGA-specific
  datapath width;
- the regeneration-frequency policy (K scheduling) beyond the block semantics
  (that is a compiler/architecture-policy matter, not ISA semantics).

**Governance rule (frozen):** the ISA is **not modified to accommodate any
substrate** — photonic, FPGA, ASIC, or digital. A substrate that cannot
satisfy this contract is an implementation failure, not a reason to change
the ISA. Precision requirements belong to the implementation, not to the ISA
semantics.

**Scope of the verified claim (frozen wording):** *"No substrate-specific
detail leaked through the tested REGEN architectural boundary under the
Stage-C populations"* (232 boundaries × 3 phase conditions, zero leaks).
This is a falsifiable, adversarially tested claim about the tested
populations — not a universal proof of abstraction. It is precisely as strong
as the Stage-C evidence and no stronger.

---

## 1. Objective & Scoped Files

The ISA gains exactly one architectural primitive:

```
REGEN   opcode 0x09
```

with architectural meaning `REGEN: S̃_K ↦ S_K`, where `S_K` is the exact
algebraic state corresponding to the completed `.block K`. **The "how"
(Σ_total, gain trim, detector, calibration) is implementation-specific and is
NOT part of the ISA contract.**

- **Reference model (executable semantics of this contract):**
  `software/tests/regen_emulator.py` — layer 1 exact oracle, layer 2
  continuous backends (Photonic / FPGA-reference / Digital), layer 3 REGEN.
- **Verification harness (this contract's gates):**
  `software/tests/test_regen_emulator.py`.
- **No RTL changes in this contract.** This contract freezes the ISA-level
  semantics; RTL/SurdLang expression is a follow-on contract.

## 2. Architectural Semantics (FROZEN)

### 2.1 REGEN instruction

- Opcode `0x09`; no register operands (whole-state projection, decision 1).
- Block length `K` is **compile-time metadata** (decision 3): the assembler
  knows `K` from `.block K` and validates exactly `K` eligible operations.
  The runtime hardware does NOT expose `K` as general-purpose architectural
  state.
- REGEN performs whole-state regeneration: the entire optical/continuous
  state of the completed block is projected to the exact algebraic state
  (scalar SurdFixed64 + Quadray). It does not regenerate scalar components
  opportunistically — it is a **state boundary**.

### 2.2 Exact-state restoration (the core guarantee)

If the backend satisfies its **declared regeneration envelope** (2.5):

```
REGEN(S̃) = S_oracle
```

where `S_oracle` is the independent exact big-integer result of the block
(clamped once at the end, per the frozen oracle discipline). The ISA promises
**the state**, not photons, interferometers, a particular Σ, or a particular
detector.

Falsifiable wording (adopted verbatim): *REGEN maps a physically represented
state back to the exact algebraic state when the implementation satisfies its
declared regeneration envelope.* This contract does NOT claim arbitrary
optical corruption is corrected.

### 2.3 REGEN_PREC — envelope, not physical constants

`REGEN_PREC` is defined in terms of the **permitted regeneration error
budget for the selected block**:

```
REGEN_PREC  = the regeneration error budget (recovery requirement) that the
              selected .block K implementation must satisfy.
```

The backend may satisfy the budget via gain precision, detector resolution,
calibration accuracy, compensation law, etc. **Physical characterization
values (e.g., "±0.00013 dB", "±1.14 K", "Σ_total 2.2e10") are evidence about
one implementation; they are NOT architectural constants and must not appear
in the ISA.**

`REGEN_PREC` faults (out-of-budget: cos(K·δφ) ≤ 0 or budget exceeded) set the
typestate guard and leave the destination untouched, per the existing
ROTC/IROTC fault convention.

### 2.4 Σ_total and bookkeeping remain private

Σ_total, temperature, calibration state, detector headroom, and
saturation/rejection counters are **internal to REGEN** (decision 5). They
are exposed only through the **non-architectural telemetry interface** (debug
observability; not program-visible ISA state). Rationale, now empirically
established: two backends with different internal Σ_total produce identical
architectural results (emulator Gate 2).

### 2.5 Backend obligations (the regeneration envelope)

Each backend implementing `.block K` + `REGEN` must declare an operating
envelope: the conditions (thermal operating range, noise budget, calibration
accuracy, dynamic-range limit) under which it guarantees 2.2. Within the
envelope, the architectural result is exact; outside it, `REGEN_PREC` faults.
The frozen experiments provide the reference envelope for the photonic
backend: common-mode thermal with the compensation law (no boundary through
K=16, experiment #5); per-op regeneration for any stochastic noise beyond
budget (experiment #6); single-factor budgeting is conservative (experiment
#7).

## 3. Block Assembly Rules (FROZEN)

- `.block K` precedes exactly `K` eligible operations; `.regen` terminates
  the block.
- Eligible operations: exact algebraic ops (e.g., `smul`, `srot60`).
- **Legality:** a block declaring `K` with fewer or more than `K` ops is an
  assembly error (`BlockValidationError` in the reference model).
- **Idempotence (permanent architectural invariant):**
  `REGEN(REGEN(S)) = S`. Once the state is exact, regenerating again must not
  change it.

## 4. Mandatory Verification Gates (for Auditor)

Execute in exact order:

```bash
# 1. Executable reference-model gates (this contract's semantics)
cd software/tests && .venv/bin/python test_regen_emulator.py
#    Expect: Gate 1 PASS (conditioned 100% at K in {1,2,4,8,16}, dT in {2,5};
#    uncompensated degradation within 2.5pt of frozen Step-5 Arm-A),
#    Gate 2 PASS (photonic == fpga == digital == oracle, 100%),
#    Gate 3 PASS (block legality + REGEN idempotence).

# 2. Frozen evidence intact (additive-only changes)
cd /home/user/Projects/hardware/SPU
.venv/bin/python run_photonic_deltaT_sweep.py > /dev/null && \
.venv/bin/python - <<'EOF'
import json
def strip(d):
    d = json.loads(d)
    for c in d['cells']: c.pop('timestamp', None)
    d.pop('generated', None)
    return json.dumps(d, sort_keys=True)
a = strip(open('results/sweeps/deltaT_sweep.json').read())
b = strip(open('results/sweeps/deltaT_sweep_frozen_v1_2026-08-20.json').read())
assert a == b, 'frozen #1 changed'
print('frozen #1 bit-identical: OK')
EOF

# 3. Repo hygiene + full regression
bash tools/verify_repo.sh
```

### 4.1 Verification vectors (must include the failures)

| Vector | Expectation |
|---|---|
| K = 1, 2, 4, 8, 16, thermal compensated | 100% recovery (Gate 1) |
| K = 1, 2, 4, 8, 16, thermal uncompensated | matches frozen Step-5 Arm-A within 2.5pt (Gate 1) |
| valid `.block K=4` | assembles, exact result (Gate 3) |
| `.block K=4` with 3 ops | assembly error (Gate 3) |
| `.block K=4` with 5 ops | assembly error (Gate 3) |
| `REGEN` on exact state | idempotent: `REGEN(REGEN(S)) = S` (Gate 3, permanent invariant) |
| same block, three backends with different Σ_total | identical exact state (Gate 2) |

## 5. Stop Conditions (Emergency Brake)

- **HALT** if a backend violates 2.2 within its declared envelope (the
  exact-state restoration guarantee is falsifiable).
- **HALT** if `REGEN(REGEN(S)) = S` fails on any backend.
- **HALT** if block legality (3) is bypassed by any assembler/emulator.
- **HALT** if physical characterization values (2.3) leak into the ISA
  contract wording or any architectural encoding.
- Do NOT add opportunistic per-component regeneration to REGEN; it is a
  whole-state boundary by contract.

## 6. Non-Goals

- NO RTL/Verilog implementation in this contract (follow-on contract).
- NO changes to the existing opcode table or the Wheeler–Feynman adapter
  profile.
- NO new Monte Carlo experiments required by this contract (the seven frozen
  artifacts + emulator gates are the evidence).

---

## Appendix A. Evidence Base (tagged 2026-08-20)

The artifacts below are the **evidence base** for REGEN v1. They are not
normative: where any of them conflicts with this contract, this contract
governs. Their role is to justify the frozen semantics and to bound the
implementation obligations.

| Tag | Artifact | Role in the evidence |
|---|---|---|
| E1 | `results/sweeps/deltaT_sweep_frozen_v1_2026-08-20.json` (sha b3d5cecc…) | Thermal envelope ±1.14K @ ≥99.9%; justifies the common-mode rotation mechanism and the conditioned-compensation law. |
| E2 | `results/sweeps/calib_sweep_frozen_v1_2026-08-20.json` (sha 551208a8…) | Calibration requirement ≈1.5e-5 relative for ≥99.9%; justifies REGEN_PREC as an implementation envelope, not ISA constants. |
| E3 | `results/sweeps/deltaT_calib_sweep_frozen_v1_2026-08-20.json` (sha 66862942…) | Joint ΔT×calibration; cancellation ridge ε* = cos(δφ)−1; the compensation law is exactly implementable. |
| E4 | `results/sweeps/amp_phase_det_sweep_frozen_v1_2026-08-20.json` (sha 5a6aefcf…) | Non-common-mode noise axes; multiplicative+additive failure mechanism; implementation-side precision budgeting. |
| E5 | `results/sweeps/ksweep_frozen_v1_2026-08-20.json` (sha 20a45cc1…) | K-chain: conditioned regeneration holds 100% through K=16 under common-mode thermal; unconditioned collapses; REGEN as a state boundary. |
| E6 | `results/sweeps/knoise_sweep_frozen_v1_2026-08-20.json` (sha 47800546…) | Per-op stochastic noise: arm A (per-op REGEN) vs arm B (chain); REGEN as dynamic-range management (Σ_total wall). |
| E7 | `results/sweeps/knoise_combined_sweep_frozen_v1_2026-08-20.json` (sha f3e49dbf…) | Combined multi-factor pass: single-factor budgeting is conservative. |
| SA | `spu_strategy/contract_regen_stageA_2026-08-20.md` (IMPLEMENTED) | ISA plumbing: decode 0x09, `.block K`, E_REGEN set, REGEN_PREC typestate, pass-through on exact arithmetic. |
| SB | `spu_strategy/contract_regen_stageB_2026-08-20.md` (IMPLEMENTED, **frozen as the deterministic reference implementation**) | Fixed-point backend: bit-exact equivalence Digital ≡ Stage-A RTL ≡ Stage-B RTL ≡ VM; the compensation law in hardware. |
| SC | `spu_strategy/contract_regen_stageC_2026-08-20.md` (IMPLEMENTED) | Hostile equivalence testing: 232 boundaries × 3 phase conditions, zero leaks; the claim in §0's scope wording. |
| EM | `software/tests/regen_emulator.py` | Executable reference model (exact oracle, continuous backends, REGEN). |

**Freeze obligations:** E1–E7 frozen artifacts must remain bit-identical to
their live copies (re-run gate in §4). SA/SB/SC contracts remain green on
`bash tools/verify_repo.sh`. The evidence base is re-tagged only when the
architectural semantics change (a v2 freeze would supersede this one).
