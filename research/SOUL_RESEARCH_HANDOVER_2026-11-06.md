# Soul research handover — 2026-11-06

Scope is bounded software research. The owner authorized pushing these Soul
research files to a public research branch as a specific exception; production
integration and any broader publication remain on hold. No physical or
subjective-identity claim follows.
This note records the final state of the work, not authorization for another
experiment. The exact source and reproducible artifacts are in each directory.

| Experiment | Disposition | Result and limit |
|---|---|---|
| [SOUL-CONTINUITY-0](soul_continuity_0/FINDINGS.md) | BOUNDED PASS | Two closely related deterministic engines shared serialized state and a supplied rule. Same schema; summary matched the five task answers. |
| [SOUL-MEM-1](soul_mem_1/FINDINGS.md) | PARTIAL | History helped against a restricted summary; equal storage and learned-rule/evidence support were not established. |
| [SOUL-MEM-2](soul_mem_2/FINDINGS.md) | PARTIAL | At equal byte budgets the stronger compact policy matched or exceeded tested history policies. Explicit persistent uncertainty was missing; logical access counts are not runtime. |
| [SOUL-LEARN-0](soul_learn_0/FINDINGS.md) | BOUNDED PASS | A finite-hypothesis learner revised a provisional rule after a counterexample. Correct candidate was predefined; reload used the same engine. |
| [SOUL-EVIDENCE-0](soul_evidence_0/FINDINGS.md) | PARTIAL | Attempt 2 passed 26 registered cases after preserving a malformed-record defect in attempt 1. Prediction output does not explicitly distinguish provisional from uniquely established. |

Evidence-0's separate checker binds a finite evidence set, candidate language
and interpretation rules to a trusted digest; it checks only declared fixture
semantics. Its digest does not authenticate the anchor or establish observation
truth. The producer and checker are separately coded, not formally verified.
The detailed [proposal and A1/A2 amendments](SOUL_EVIDENCE_0_PROPOSAL.md) record
the contract; owner authorized the bounded evaluation in the conversation.
Attempt-specific sources, hashes and outputs are under `soul_evidence_0/evidence/`.

Reproduction and resource bounds are in each experiment's README. Evidence-0
attempt 2 ran five focused tests and two identical registered runs, within 30 s
and 1 GiB per process. The repository also contains unrelated pre-existing
uncommitted work; do not include it in a Soul-only commit. Base revision at start of this task was
`e7d37aa6714b42aa79b07df1a9c625143dd112b4`. No successor is
authorized automatically. In particular, SOUL-CONTINUE-1 is a future candidate,
not evidence of learned-state migration to a different engine. SPU physical
qualification and QAF retain their separate governance and evidence boundaries.
