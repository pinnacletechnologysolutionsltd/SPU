# CLAUDE.md — Claude Code Engineering Guidance

@AGENTS.md

## Directives for Claude

1. **Role Portability:** You may serve as **Spec Author** (drafting architectures and bounded contracts in `spu_strategy/` using [`spu_strategy/contract_template.md`](spu_strategy/contract_template.md)), or as **Halt-and-Flag Implementer** on assigned tasks.
2. **Commands, Not Prose:** When specifying implementations or findings, provide exact shell commands and file diffs rather than conversational narrative.
3. **No Speculative Abstractions:** Do not create wrapper layers, extra helper classes, or unrequested generic infrastructure. Keep modules Lithic (50–150 lines).
4. **Repository Hygiene:** Clean up any temporary test scripts (`tmp_*.v`, `scratch_*.py`) or waveform dumps before declaring a task complete.
5. **Silicon Claims Discipline:** Never state that a feature or fix is "verified in silicon" unless citing the exact section in [`docs/hardware_evidence.md`](docs/hardware_evidence.md).
