# Engineering Contract Template

Use this template when drafting multi-agent contracts for SPU engineering tasks.

**Roles:**
- **Spec Author:** [Agent / Human name] (Formulates architecture, invariants, and falsification rules)
- **Halt-and-Flag Implementer:** [Agent / Human name] (Pre-review for edge cases, literal code execution)
- **Integration Auditor:** [Agent / Script / Human] (Hygiene sweeps, regression runner, evidence gatekeeping)

---

# Engineering Contract: [Task Name]
**Date:** YYYY-MM-DD  
**Contract ID:** `gtp_contract_<feature>_<date>.md`  
**Status:** DRAFT | ACTIVE | BLOCKED | COMPLETE  

## 1. Objective & Scoped Files
* **Target Files to Modify:**
  - `hardware/rtl/core/spu13/<target_module>.v` (Keep ≤ 150 lines, Lithic)
* **New or Updated Testbenches:**
  - `hardware/tests/spu13/<target_module>_tb.v`
* **Software / Oracle Alignment (if applicable):**
  - `software/tests/test_<oracle>.py`

## 2. Invariants & Hard Constraints (The "Never" List)
- [ ] **Exact Arithmetic Only:** No floating-point or transcendental approximations.
- [ ] **No Speculative Abstraction:** Write direct, explicit logic without unrequested generic wrapper layers.
- [ ] **No Scratch Clutter:** All temporary testbenches or simulation dumps must be removed after verification.
- [ ] **Port Interface Invariant:** Do not alter existing top-level or core port lists without explicit authorization.

## 3. Evidence Claims and Reproducibility

Record evidence as separate claims. Structural validity, functional
simulation, synthesis/place-and-route, interface validation, and silicon
observation are not nested gates: a pass at one stage does not establish a pass
at another. For each claim, name the artifact, source revision, configuration,
command, result, and evidence location. Mark unrun dimensions `NOT RUN` rather
than inferring their result.

| Evidence claim | Required statement |
|---|---|
| Structural validation | Whether the intended topology and hierarchy are present, and how that was checked |
| Functional simulation | Whether tested behavior matches the named oracle and the exact tested scope |
| Synthesis / place-and-route | Whether the design is realizable under named device, clock, and resource constraints |
| Interface validation | Whether clocks, reset, serial protocol, and pin mappings were checked, and by what method |
| Silicon observation | Which exact programmed artifact produced the observed behavior, and what the observation establishes |

Comparative or determinism benchmarks must report these dimensions
independently:

1. Repeatability across runs on one device.
2. Reproducibility across builds from declared source/configuration.
3. Reproducibility across devices.
4. Exact agreement with an independent mathematical oracle.
5. Measured performance/resource cost for each guarantee claimed.

Do not infer correctness from repeatability, cross-device agreement from
cross-build agreement, or whole-system guarantees from a tested kernel.

## 4. Step-by-Step Implementation Instructions (for Implementer)
1. ...
2. ...
3. ...

## 5. Mandatory Verification Commands (for Auditor / Runner)
Execute the following commands in exact order:

```bash
# 1. Scoped testbench check
iverilog -g2012 -I hardware/rtl/arch -o build/<target_module>_tb.vvp hardware/rtl/core/spu13/<target_module>.v hardware/tests/spu13/<target_module>_tb.v && vvp build/<target_module>_tb.vvp

# 2. Automated repository hygiene and regression gate
bash tools/verify_repo.sh
```

## 6. Stop Conditions (Emergency Brake)
- If pre-execution review reveals an unhandled edge case or contradiction, **HALT and flag the flaw**.
- If any testbench asserts `FAIL` or timing cannot be closed within constraints, **HALT immediately**.
- Do NOT add pipeline stages or FIFOs to paper over timing failures without drafting a revised contract.
