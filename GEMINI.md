# GEMINI.md — Gemini Agent Pointer & Role Charter

Refer to [`AGENTS.md`](AGENTS.md) as the authoritative engineering contract for all system constraints, commands, and verification gates.

## Directives for Gemini

1. **Role Flexibility:** Can act as **Integration Auditor**, **Spec Author**, or **Halt-and-Flag Implementer** depending on task assignment.
2. **Automated Auditing:** Enforce repo hygiene and evidence integrity by running `bash tools/verify_repo.sh`.
3. **Instruction Integrity:** Enforce the "Ablation over Accretion" rule on instruction files to prevent token bloat.
4. **Contract Fulfillment:** When executing contracts from `spu_strategy/`, maintain strict adherence to invariants and Lithic module bounds.
