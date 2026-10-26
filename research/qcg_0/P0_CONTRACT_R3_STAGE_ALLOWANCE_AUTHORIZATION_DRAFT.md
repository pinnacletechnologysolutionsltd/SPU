# QCG-0 R3.2.1 stage-table calculation allowance: authorization record (DRAFT transcription for the coordinator to file)

Date: 2026-10-23. Transcribes the owner's message "QCG-0 R3.2.1 — stage-table calculation allowance APPROVED". The author (Claude) is **not** the reviewer, ran **no**
calculation, and performs none under this allowance. Hash identities below were checked by `sha256sum` only; the coordinator should re-verify them when filing.

| Parameter | Approved limit |
|---|---|
| Contract | Revision 3.2.1, SHA-256 `1f8aca9f088ffbaafb002ba5cffde7bdee7b33fdfcf18dcf20dec16202b8cf2f` |
| Allowance request | SHA-256 `fe81e6209c69696656648ae8275dcbbb130320dce51381b1dfc625f2b8b23546` |
| Calculations | 21 preparations, 48 sequential routes, 5 Cell B routes; evaluation ceiling 896 |
| Invocations | maximum 3, zero retries |
| Per-invocation deadline | 30 seconds; cumulative external ceiling 90 seconds |
| Address space | 1 GiB per invocation |
| Output | 4 MiB per file, 10 MiB cumulative |
| Exclusions | no children, network, installs, implementation, benchmarking or P0 execution; Cell A untouched and not recalculated |

Evidence in hand: independent PASS certificate `384db31162658f709a002006c42086bbaf277011d0bde4a558692cb6fd4ec2b4`, manifest
`36f8b3773a75635015e3c1ab619132febe…` (full value in `P0_CONTRACT_R321_REVIEW_MANIFEST.json`'s file hash), decision record
`QCG0_P0_DECISION_RECORD.md` (D-1…D-6 ACCEPT with the recorded scopes).

**Mandatory conditions for the reviewer (owner):** (1) verify the full contract, request, PASS certificate, evidence manifest and inherited source/reference
hashes and D-1…D-6 scopes before any calculation; (2) read the review scripts first: bounds, no alteration of certified data, independently checkable output;
(3) establish how per-file and cumulative output caps are **enforced**, not merely checked afterwards; if any deadline, memory or output limit is
unenforceable, return HOLD without launching; (4) calculate only the frozen operations and stages, no alternative algorithm to avoid a width refusal;
(5) a Cell B preparation refusal is an acceptable mathematical outcome: record the exact first failing event, route context and status; (6) at most three
invocations, no retry, no extra computation after exhaustion, no widening to Cell A.

**Deliverables:** an independent certificate, a stage-table JSON (every route with a unique context and either its first-refusal event or an explicit null), and
an evidence-hash manifest. A terminal PASS means the derivation and evidence checks passed, not that all W31 operations were admitted.

Freeze, candidate implementation, benchmarking and P0 execution remain HOLD.
