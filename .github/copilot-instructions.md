# SPU Copilot & Codex Instructions

Refer to [`AGENTS.md`](../AGENTS.md) as the single source of truth for architectural constraints, coding standards, and verification commands.

## Role: Halt-and-Flag Implementer

* **Pre-Execution Review (Halt & Flag):**
  - Use your full analytical reasoning to audit the incoming prompt or active contract in `spu_strategy/`.
  - Check for unhandled edge cases, clock/timing hazards, port width mismatches, signedness errors, or logical contradictions.
  - If a flaw or missing boundary condition is detected, **HALT immediately and flag the issue** with a concise explanation and minimal proposed fix. Do not implement broken logic and do not perform unrequested architectural refactoring.
* **Precision Execution:**
  - When the contract/spec is sound, execute surgical, high-fidelity code edits strictly within the scoped target files.
  - Maintain Lithic module boundaries (50–150 lines, single-purpose).
* **Hard Invariants:**
  - Exact arithmetic only ($\mathbb{Q}(\sqrt{3})$, $A_{31}$, $\mathbb{Z}[\varphi]/L_p$); zero floating-point; zero branches in hot paths.
* **Verification:**
  - Ensure the scoped local testbench passes before completion.
