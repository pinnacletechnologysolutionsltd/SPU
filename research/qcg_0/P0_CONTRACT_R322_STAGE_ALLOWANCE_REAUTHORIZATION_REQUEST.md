# QCG-0 R3.2.2 — stage-table allowance: re-authorization request (preparation only; nothing executed)

Date: 2026-10-23. The draft allowance (`P0_CONTRACT_R3_STAGE_ALLOWANCE_AUTHORIZATION_DRAFT.md`) names Revision 3.2.1. Contract Revision 3.2.2 (commit `a087145`) changed the
sequential rules, so the allowance must be re-bound before any use. The author (Claude) is not the reviewer, has run no stage calculation, and will not consume the allowance.

| Identity | Old (draft allowance) | Needed |
|---|---|---|
| Contract SHA-256 | `1f8aca9f088ffbaafb002ba5cffde7bdee7b33fdfcf18dcf20dec16202b8cf2f` (3.2.1) | `872def93c853e5520817785a75b472a126e864b437dca20eff8899b4ac091cb2` (3.2.2) |
| Allowance request | `fe81e620…3546` | reviewer to confirm it still applies, or issue a replacement |
| R3.2.2 reviewer certificate | — | not yet in the repository; to be preserved by a separate provenance commit |

Limits proposed unchanged (reviewer's to confirm): up to 3 invocations, 30 s each, 1 GiB address space, 4 MiB per file, no network, no retry, no widening to Cell A.

Points for the reviewer to settle explicitly:
1. Whether the counts in the draft (21 preparations, 48 sequential routes, 5 Cell B routes; ceiling 896) still apply. Under §3 (3.2.2) the positions after the first refusal of a state-dependent (arm, tape) are NOT_ISSUED and need no derivation, so the work can only shrink; the stage tables must use the §3 row vocabulary (OK, REFUSED with event id, INVALID, NOT_ISSUED).
2. That event ids follow the §5 step labels (a/b/c steps; no generic `FDSTEP.*` names where a step label exists).
3. That the calculation remains independent of the candidate code (`p0/`), which must not be consulted or used as an oracle.
4. That the result is filed as a reviewer certificate plus JSON like the Cell A tables, with hashes recorded before any comparison with the candidate.

## Requested records (two, logically distinct; they may arrive together)

**A. R3.2.2 contract review certificate.** The reviewer's actual PASS disposition for contract SHA-256 `872def93c853e5520817785a75b472a126e864b437dca20eff8899b4ac091cb2`
(commit `a087145`): reviewed scope, findings and any qualifications. Not authored or reconstructed by the implementer. A contract PASS does not by itself authorize a derivation.

**B. Stage-derivation allowance decision.** Confirm or revise the bounded allowance for independent sequential and Cell B W31 derivation under R3.2.2. Maximums preserved:
3 invocations, 30 s each, 1 GiB address space, 4 MiB per file, no network, no retry, no additional Cell A derivation. The reviewer is asked to verify explicitly:
- the §3 issued / `NOT_ISSUED` semantics and the dependent-tape classification;
- that the 896-evaluation ceiling is a bound on permitted work, not an expectation: a dependent tape that refuses early yields `NOT_ISSUED` rows without further calculation;
- §5 event-id grammar and step labels, with state and event identities established independently, not copied from the candidate's reported first-refusal events;
- independence from the candidate implementation;
- certificate and JSON evidence hashes recorded before any comparison with the candidate.

Derivation execution stays on HOLD until decision B is explicit. The candidate (`p0/`), mathematical references, comparator policy and the existing allowance evidence are not to be modified.
