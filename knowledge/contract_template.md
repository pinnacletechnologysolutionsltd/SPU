# Engineering Contract Template

Use this template when drafting multi-agent contracts for SPU engineering tasks.

**Roles:**
- **Spec Author:** [Agent / Human name] (Formulates architecture, invariants, and falsification rules)
- **Halt-and-Flag Implementer:** [Agent / Human name] (Pre-review for edge cases, literal code execution)
- **Integration Auditor:** [Agent / Script / Human] (Hygiene sweeps, regression runner, evidence gatekeeping)

---

# Engineering Contract: [Task Name]
**Date:** YYYY-MM-DD  
**Contract ID:** `contract_<feature>_<date>.md`  
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

## 3. Step-by-Step Implementation Instructions (for Implementer)
1. ...
2. ...
3. ...

## 4. Mandatory Verification Commands (for Auditor / Runner)
Execute the following commands in exact order:

```bash
# 1. Scoped testbench check
iverilog -g2012 -I hardware/rtl/arch -o build/<target_module>_tb.vvp hardware/rtl/core/spu13/<target_module>.v hardware/tests/spu13/<target_module>_tb.v && vvp build/<target_module>_tb.vvp

# 2. Automated repository hygiene and regression gate
bash tools/verify_repo.sh
```

## 5. Stop Conditions (Emergency Brake)
- If pre-execution review reveals an unhandled edge case or contradiction, **HALT and flag the flaw**.
- If any testbench asserts `FAIL` or timing cannot be closed within constraints, **HALT immediately**.
- Do NOT add pipeline stages or FIFOs to paper over timing failures without drafting a revised contract.
