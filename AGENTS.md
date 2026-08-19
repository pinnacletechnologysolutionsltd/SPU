# SPU-13 Engineering & Governance Contract

This file defines the mandatory engineering constraints, functional agent roles, and verification gates for the SPU codebase. It is loaded as the root engineering contract.

---

## 1. System Context & Tech Stack

* **Architecture:** SPU-13 (13-axis cuboctahedral manifold cortex) & SPU-4 Sentinel (4-axis Quadray satellite/edge node).
* **Arithmetic Fields:** Bit-exact, deterministic arithmetic over $\mathbb{Q}(\sqrt{3})$, $A_{31}$ (Mersenne 31 field $[1, \sqrt{3}, \sqrt{5}, \sqrt{15}]$), and $\mathbb{Z}[\varphi]/L_p$ (Lucas Phinary).
* **Hardware Toolchain:** Verilog HDL with OSS CAD Suite (Yosys + nextpnr-himbaechel). Primary hardware targets: Tang Primer 25K (probe/bring-up) and Wukong Artix-7 100T (silicon evidence).
* **Software Toolchain:** Python 3.10+ (emulator, oracles, assemblers), C++17 (oracle bit-parity).
* **Design Rule:** Single-purpose "Lithic" modules (50–150 lines). Split concerns rather than growing oversized files.

---

## 2. Functional Roles & Governance Protocol

Engineering tasks follow a portable, 3-role governance protocol (any tool or human can fill any role):

1. **Spec Author (Strategist / Drafter):**
   * Formulates mathematical representations, architectures, and contract specifications.
   * Drafts machine-actionable contracts in `spu_strategy/` using [`spu_strategy/contract_template.md`](knowledge/contract_template.md).
   * **Rule:** Must write command-first instructions with exact shell invocations; zero speculative prose.

2. **Halt-and-Flag Implementer (Analytical Reviewer & Coder):**
   * **Pre-Execution Review (Halt & Flag):** Inspects incoming specs for unhandled edge cases, clock/timing hazards, or logical contradictions. If a defect is found, **HALT immediately and flag the flaw** with a minimal proposed correction rather than implementing broken logic or silently rewriting the architecture.
   * **Precision Execution:** Executes surgical, literal code edits (50–150 line Lithic modules) strictly within the defined scope.
   * **Rule:** Zero speculative abstractions or out-of-scope refactorings.

3. **Integration Auditor (Verification & Repo Gatekeeper):**
   * **Automated Gatekeeper:** Runs deterministic verification via `bash tools/verify_repo.sh`.
   * **Integrity Gate:** Validates that any "silicon-verified" claim cites [`docs/hardware_evidence.md`](docs/hardware_evidence.md).
   * **Hygiene Enforcement:** Sweeps untracked temporary files (`tmp_*`, `scratch_*`, root `.vcd` dumps).

---

## 3. Hard Constraints (The "Never" List)

1. **NO Floating Point or Division in RTL:** All arithmetic is exact in $\mathbb{Q}(\sqrt{3})$, $A_{31}$, or $\mathbb{Z}[\varphi]/L_p$.
2. **NO Branches in Hot Paths:** Control flow compiles to multiplexer Boolean polynomials.
3. **NO Unbacked Silicon Claims:** Never claim a feature is "silicon-verified" unless backed by a specific entry in [`docs/hardware_evidence.md`](docs/hardware_evidence.md). Otherwise, state `testbench-verified`, `simulation-only`, or `unmeasured`.
4. **NO Manual Edits to Generated Files:** Never hand-edit `software/lib/irotc_catalog.py`, `spu13_irotc_codes.mem`, `spu13_irotc_golden.mem`, or `rplu2_boot_tables.bin`. Always run their generator scripts.
5. **NO Vacuous Assertions:** Testbench assertions must be falsifiable (cannot assert against constants or untoggled signals).
6. **NO Root Directory Clutter:** Temporary scripts, waveform dumps (`*.vcd`), and test binaries must never be committed to the root directory.

---

## 4. Mandatory Verification Commands

Before declaring any task complete or committing changes, execute the required gates:

```bash
# 1. Automated Repo Hygiene & Regression Gate (Runs full suite + citation checks)
bash tools/verify_repo.sh

# 2. Scoped Triage Gate (during active development)
TB_FILTER=<subsystem_prefix> python3 run_all_tests.py

# 3. ROTC / IROTC Trace Equivalence Gate
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py

# 4. Math Oracle & Parity Gates
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py

# 5. FPGA Synthesis Check (Artix-7 100T Padé build)
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade synth/pnr/pack
```

---

## 5. Normative References & Catalogs

* **ROTC 0–35 Angle Catalog & Permutations:** [`knowledge/rotc_tables.md`](knowledge/rotc_tables.md)
* **ISA Reference & Opcodes:** [`knowledge/isa_reference.md`](knowledge/isa_reference.md)
* **Hardware Silicon Evidence Ledger:** [`docs/hardware_evidence.md`](docs/hardware_evidence.md)
* **SPU Lexicon & Terminology:** [`knowledge/SPU_LEXICON.md`](knowledge/SPU_LEXICON.md)
* **Contract Template:** [`spu_strategy/contract_template.md`](spu_strategy/contract_template.md)
