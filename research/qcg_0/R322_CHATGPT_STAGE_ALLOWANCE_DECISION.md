# QCG-0 R3.2.2 — ChatGPT stage-table allowance decision

Date: 2026-10-23
Reviewer: ChatGPT (GPT-6)
Disposition: **APPROVE REBINDING, bounded independent derivation only**

## Bound identity

- Contract Revision 3.2.2 SHA-256: `872def93c853e5520817785a75b472a126e864b437dca20eff8899b4ac091cb2` (uploaded bytes verified)
- Request SHA-256: `9448d32b7c5c8199f8646dadb6d7305322112fa5269887341bb12b0dc3037be6` (uploaded bytes verified)
- Original allowance request identified in the request as `fe81e620…3546`, but its full bytes were not supplied. This decision is a **new, self-contained bounded authorization**, not a certification of that old document's contents.

## Maximum permitted work

- Up to **3 independently bounded invocations**, with **30 seconds per invocation**, **1 GiB address space**, **4 MiB per output file**.
- **No retries** of any consumed invocation. No network access. No widening to Cell A or other work.
- Target: independent W31 stage tables for the specified **48 sequential arm/tape routes**, **5 Cell B routes**, and their **21 preparations**, to the extent actually in scope of the frozen derivation request.
- **896 is an upper bound**, not a mandatory count. q00–q16 positions after the first REFUSED/INVALID on a dependent tape are `NOT_ISSUED` without any further evaluation; stateless requests continue. Each table reports issued/unissued counts.
- Stage outcomes use exactly `OK`, `REFUSED` with first event ID, `INVALID`, or `NOT_ISSUED`. Distinguish `PREPARATION_REFUSED` when preparation prevents any requests; do not silently relabel preparation refusal as a sequential request result.
- Use the event-ID grammar and named §5 a/b/c steps; preserve outer context (profile, curve, tape/cell, arm, request).
- Derivation must be independently written from the contract and independently grounded mathematical references. **Do not import, call, or copy candidate `research/qcg_0/p0/` code or its reported refusal events.**
- Produce reviewer certificate plus JSON tables, recording their content hashes **before** comparing them to any candidate outputs.

## Preconditions and limitations

- This authorization permits a reviewer to attempt the stated bounded derivation; it is **not evidence that a derivation has occurred or passed**.
- Before running, establish and record the actual reference-file identities, source/command/environment identity, resource-enforcement method, and attempt accounting. If those prerequisites cannot be met within the fixed scope, report **HOLD** rather than improvising or consuming a campaign slot.
- The 21/48/5 counts are the request's stated intended coverage, not independently re-derived from the complete source/reference bundle during this review. A discrepancy must be reported and resolved without expanding the allowance.
- Full repo, pinned references, and reviewer environment were not supplied here. This decision does not independently certify those artifacts.
- **Formal contract freeze, candidate implementation changes, P0 launch, FPGA operations, and P0 acceptance remain HOLD.**

Decision: **GO for independently bounded W31 stage derivation only, after prerequisites are established.**
