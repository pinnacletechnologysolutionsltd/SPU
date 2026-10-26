# QCG-0 R3.2.2 — independent contract consistency review request

Date: 2026-10-23. Read-only review. Do not modify the candidate (`p0/` code), derive W31 stage tables, execute P0, or start any campaign.

| Artifact | SHA-256 |
|---|---|
| Amended contract (Revision 3.2.2) | `872def93c853e5520817785a75b472a126e864b437dca20eff8899b4ac091cb2` |
| Revision 3.2.1 baseline (independent PASS) | `1f8aca9f088ffbaafb002ba5cffde7bdee7b33fdfcf18dcf20dec16202b8cf2f` |
| `QCG0_P0_EXECUTION_CONTRACT_REVISION_3_2_2.diff` | `d86faa4470b878c91ec78cf45591665f2ef19fda965590d8b545059837a99342` |
| `P0_CONTRACT_S3_CLARIFICATION_PROPOSAL.md` | `8363caf1c2019278130cb044bb1ef11452e28bb4effdb6af2c5222df1ab43bf3` |
| Draft `p0/PINS.sha256` (42 entries; only the contract line changed) | `70321a042e8a5c6abb75ac33bb14dba07d2333d97cf24d0c3606b251bc386647` |

Check: (1) `NOT_ISSUED(STATE_DEPENDENT_AFTER_REFUSAL)` is consistently a scheduling outcome, not a status or refusal code; (2) the dependent/independent
classification, especially Horner/Bezier/PH on S3; (3) ending a dependent tape after a refusal at **q00** is an explicit, acceptable policy (the author kept the simple
rule; a finer rule would need a code change); (4) §2 and §3 comparator eligibility agree, in particular for `INVALID`: §2 requires status OK on every matched request,
so `INVALID` appears already ineligible and was deliberately **not** added to the §2 parenthetical (author's reading; please confirm or rule otherwise);
(5) zero eligible comparators on a tape (W31, PH5 S3) is representable without inventing a comparator; (6) event ids, `qNN`, issued+unissued=17, the operation
budget and W31 stage-table requirements are mutually consistent; (7) nothing in registered mathematics, workloads, comparison rules, costs, guards or thresholds changed.
Also verify the diff against the baseline and the 42-entry pin manifest.

Return PASS or REVISE with precise findings. On REVISE, only the required semantic correction is made and resubmitted.
