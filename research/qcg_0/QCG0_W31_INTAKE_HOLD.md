# QCG-0 independent W31 derivation — intake verification and HOLD

Date: 2026-10-23
Reviewer: ChatGPT (GPT-6)
Disposition: **HOLD — NO DERIVATION ATTEMPT LAUNCHED**

## Packet integrity

Archive SHA-256: `f5d478aae3e72ee3083cf5ed5cfa323f713ef98bc60f284d875b9cac69572587`.
Extracted `/mnt/data/w31_review/`; `sha256sum -c SHA256SUMS` passed all 12 listed paths (11 inputs plus README).
The package excludes the candidate `research/qcg_0/p0/` and its reported results.

## Input identities

```json
{
  "inputs/P0_CONTRACT_R2_LEDGER_STAGE_EXPECTATIONS.json": "093b006b4b11e289066265a9021fba92c28ec252b8df44eac06a48f8eeca75bb",
  "inputs/P0_CONTRACT_R2_REMAINING_CELL_A_STAGE_EXPECTATIONS.json": "d231a81305f975727b82431bb04a51dff41fbc55a85708a8521c63c36edf6a0a",
  "inputs/P0_CONTRACT_R2_SUPPLEMENTAL_REFERENCES.json": "9422d7617c65a9a3fc2fa1ab19af7ce7ea634721cfeb251096cd3821534237a0",
  "inputs/P0_CONTRACT_R322_STAGE_ALLOWANCE_REAUTHORIZATION_REQUEST.md": "9448d32b7c5c8199f8646dadb6d7305322112fa5269887341bb12b0dc3037be6",
  "inputs/QCG0_P0_EXECUTION_CONTRACT.md": "872def93c853e5520817785a75b472a126e864b437dca20eff8899b4ac091cb2",
  "inputs/QCG0_P0_EXECUTION_CONTRACT_REVISION_3_2_2.diff": "d86faa4470b878c91ec78cf45591665f2ef19fda965590d8b545059837a99342",
  "inputs/QCG0_PREREGISTRATION.md": "eade4b5f0957c3679c94b67d8f4b1f6b6d005d65316a5337e6c8dfb9370b98dd",
  "inputs/QUINTIC_FIXTURE_VALUES.json": "8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34",
  "inputs/R322_CHATGPT_CONSISTENCY_REVIEW.md": "6c3ea533198d419c71135bafade86c413cf8fe89d6e4ee5ec32ac1d9ecb70be2",
  "inputs/R322_CHATGPT_STAGE_ALLOWANCE_DECISION.md": "30cacc8c57b7936b49913bd692a57788ed5187ce30a2bb3a2e5409d608c811fc",
  "inputs/REVISION2_FIXTURE_VALUES.json": "a66af3d68da5a7dba439818778af9e8fe70244e3dc2d8250ea891354124a0b46"
}
```

## Intake interpretation

Structural coverage is 2 curves × 8 sequential arms × 3 tapes = 48 routes, and 5 Cell B routes; 16 + 5 = 21 per-arm preparations; 48 × 17 + 5 × 16 = 896 position ceiling. These are structural counts, not derived W31 statuses. After a dependent first REFUSED or INVALID, remaining positions are NOT_ISSUED by §3. Cell A arithmetic outcomes are out of scope.

## Execution prerequisites and attempt accounting

Environment inspected: Python `3.13.5` on `Linux-6.18.55-x86_64-with-glibc2.41`. Archive verification command: `sha256sum -c SHA256SUMS`.
The independent derivation implementation has **not** been authored and qualified; hence no exact derivation source identity, launch command, run-specific memory and wall-clock enforcement, or independent stage-table outputs are available. Launching before these are established would violate the allowance preconditions.

**Invocation 1:** NOT LAUNCHED.
**Invocation 2:** NOT LAUNCHED.
**Invocation 3:** NOT LAUNCHED.
**Consumed slots:** 0/3.

No stage arithmetic, candidate comparison, QCG P0 execution, source modification or contract change occurred. No W31 reference tables or acceptance certificate are claimed.

## Release condition

Independently author and inspect a contract-derived stage interpreter (without candidate code), record its exact SHA-256, frozen entry command, resource enforcement (30 s, 1 GiB, 4 MiB/file, network disabled), and append-only attempt log. Only then consume a slot. Preserve table/certificate hashes before any candidate comparison.
