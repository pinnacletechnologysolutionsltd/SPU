# QCG-0 P0 contract §3 clarification proposal (for independent read-only consistency check)

Date: 2026-10-23. Subject: Revision 3.2.1 (`1f8aca9f…cf2f`), unchanged. This file proposes text; it edits nothing. Owner intent accepted for review; not authoritative until the reviewer accepts it and a contract revision incorporates it.

## Proposed text, appended to §3 "Atomicity and evidence"

> **Dependent requests after a refusal.** A tape is *state-dependent* when a request reads state that an earlier request of the same tape advances: stepped forward-difference tables, retained Taylor-shifted lists, retained jets, or S3's previous-sample value used by `inc_k`. If a request of a state-dependent tape is refused, committed state is unchanged (above), so the state the next request requires was not advanced. Every later request of that tape whose required state was not advanced is **not issued** and is recorded as `NOT_ISSUED(STATE_DEPENDENT_AFTER_REFUSAL)`. This is a scheduling outcome, not a status of the grammar above and not a refusal code; it carries no values, no event id and no ledger entry. "Every (arm, request) yields exactly one status" applies to every *issued* request. Requests that read no advanced state (Horner, Bezier, PH evaluation on S1/S2) are issued independently. No unissued request may be reported as OK, and no reference value may stand in for it.

## Consistency checks made by the author (not independent)

| Contract text | Consistent? | Note |
|---|---|---|
| §3 atomicity: refusal leaves committed state bit-identical | Yes | The proposal relies on it: the unadvanced state is exactly why the next request would be off-grid. |
| §3 status grammar, `NOT_APPLICABLE` "never a refusal code" | Yes | `NOT_ISSUED` is outside the grammar and is not added to it. |
| §5 grid assertion: sample k at exactly k/16 | Yes | Issuing an off-grid sample would violate it; not issuing it cannot. |
| §5 sequential scheduling "for k = 1..16 step then sample; inc_k as soon as sample k+1 exists" | Yes | A refused step means sample k+1 never exists, so `inc_k` is also unissued. |
| §3 event id `qNN` = 0-based position in the frozen tape | Yes | Positions are not renumbered; unissued positions simply have no event. |
| §5 S3 `inc_k` | Needs reviewer attention | S3 reads the previous sample even for Horner, Bezier and PH, so those arms are state-dependent on S3 only. The text above covers this through "previous-sample value". |
| §2 comparator eligibility: OK "on every matched request" | Needs reviewer attention | An arm with `NOT_ISSUED` requests is not OK on every matched request, so it is ineligible as comparator on that tape. Here that is every arm on PH5 S3 under W31; P4096 is unaffected. |
| §8 X-15/X-16 | Yes | X-16 concerns Cell A; the sequential W31 table is not yet derived. |

## Implementation state

`arms_seq.Seq.run_tape` already follows this rule (`STALE` when `evolving ∩ retained` is non-empty after a non-OK request). Tests: `sequential_refusal_rule` (PH5 S3 under W31: sample 1 refuses, 15 `NOT_ISSUED`, for Horner, FD, C2, PH; a tight profile showing Horner continuing and FD stopping). No code change is needed if the text is accepted as written; a different rule would change `run_tape` only.

## Next step

Independent read-only consistency check of this text against §2, §3, §5, §8 and the registered tapes. Only after acceptance: one direct `stages.build()` development check under the stated conditions.
