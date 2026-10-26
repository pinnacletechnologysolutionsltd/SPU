# QCG-0 P0 owner decision record (dispositions recorded 2026-10-23)

Date: 2026-10-23. Subject: the exact decision text of `QCG0_P0_EXECUTION_CONTRACT.md` Revision 3, SHA-256
`d6f27aae3328814b67b8c10da2e916b2f3943dbffa9416f97aa4e629243e7989` (433 lines) as it stood when this record was generated (each quotation below is copied programmatically from that file; section numbers are the contract's).
The quoted text below is from Revision 3. **Revision 3.1** (SHA-256 `2829a167eabb3bcc16a5beed35249ce91f5097de0f7934647e0f7676b474ee44`) records the
dispositions in its §11 and changes only status wording (diff `QCG0_P0_EXECUTION_CONTRACT_REVISION_3_1.diff`). The owner approved D-1…D-6 on
2026-10-23 "with the independent reviewer's stated qualifications"; the scopes recorded here adopt those qualifications and broaden none.
Acceptance is not authorization: freeze, implementation and execution remain HOLD.

| ID | Decision (contract wording) | Reviewer recommendation (not an approval) | Owner disposition (ACCEPT / REVISE / REJECT) and scope |
|---|---|---|---|
| D-1 | C1 declared equivalent to B-PH (Cell A) and PHFD (sequential) | accept as a scoped conformance design, no candidate-specific advantage claim | ACCEPT. C1/B-PH (Cell A) and C1/PHFD (sequential) equivalence is a conformance control, not a C1-specific performance advantage. |
| D-2 | FD `NOT_APPLICABLE` in random-access Cell A; sequential FD retained | accept for P0 scope | ACCEPT. FD is not applicable to random-access Cell A; retained as a mandatory sequential comparator. |
| D-3 | literal-constant shift policy (S), semantic-versus-administrative K, M2 informational | accept as an abstract accounting convention (not CPU timing or hardware cost) | ACCEPT. The arithmetic ledger is an abstract operation-accounting convention, with the explicit K/administrative distinction; not a proxy for hardware performance. |
| D-4 | lexicographic comparator with eligibility and ASCII arm-id tie-break | accept; call it the lexicographically selected comparator | ACCEPT. Deterministic lexicographic ranking, ASCII tie-break, complete secondary comparisons retained. |
| D-5 | guard on `T_ret_peak` (retained-state storage), split reported only | accept for retained-state storage only | ACCEPT. `T_ret_peak` is retained-state storage only; scratch lifetime and other memory measures reported separately; no peak-total-memory claim. |
| D-6 | defer the J_c/Σ_c sharing metric | accept; P0 makes no sharing claim | ACCEPT. Defer the joint-versus-standalone sharing metric; P0 makes no sharing-efficiency claim. |

## Verbatim contract text behind each decision

### D-1

> 2. Under the frozen algorithms C1 performs B-PH's operations in Cell A and PHFD's in the sequential control (**proposed
>    design consequence, pending D-1**). P0 can then report equivalence there but not a candidate-specific arithmetic advantage;
>    Cell B is where C1 differs.

> | EQ-1 | Cell A: ledger(C1) = ledger(B-PH) in every category and phase | exact equality (**proposed**, pending D-1; depends on the preparation and storage rules of §2/§5) |
> | EQ-2 | sequential: ledger(C1) = ledger(PHFD) | same |

> (see §5 Cell A: C1 follows the b-steps b1–b19 identically to B-PH; Cell B C1 is the stand-alone retimed generator h1–h13.)

### D-2

> 3. FD is `NOT_APPLICABLE` in Cell A (**proposed P0 scope, pending D-2**; this is a chosen policy, not a claim that no
>    random-access finite-difference method exists).

> §5: B-FD in Cell A is `NOT_APPLICABLE`; the sequential tape keeps FD (FDINIT in P, FDSTEP per sample).

### D-3

> **Classification rule (do values equal to 2 or ½ qualify?)** No. S depends only on the literal constant in the algorithm text.
> A multiplier that merely **evaluates** to 2 or ½ (the parameter t = ½, a coefficient equal to 2, the step 1/16) is M or D.
> A constant that comes from an index, a binomial or the degree is M or D whatever its value (`÷(i+1)` is D, `i·a_i` is M).
> Applied identically to every arm.

> | **S** | shifts | exactly the **literal constants 2 and ½ written in this contract's algorithm text**, cost 1, no gcd |

> | **K** | semantic comparisons | each comparison or sign/zero test **named in the algorithm text** (the `ok` flags, `φ′ ≥ 0`, join predicates, regularity tests) counts 1, whether or not it forms products. **Administrative checks are not K and are not counted anywhere:** the zero-divisor guard inside D, the parity test inside S, import and width/bound checks, declared-degree assertions and oracle-side assertions. They may raise a status (`INVALID`, `REFUSED`) but add no ledger entry. Hence preparation has K = 0 even though it performs divisions. |

> | **M2** | informational | M operations whose multiplier *value* is a power of two (2, ½, 4, 1/16, …). Reported only. |

### D-4

> **Comparator (proposed deterministic ranking; not a claim that a componentwise best exists).** Eligible comparators are
> conventional arms with status OK on every matched request (never `REFUSED`, `NOT_APPLICABLE` or `PREPARATION_REFUSED`). The
> comparator is the eligible arm lexicographically smallest on (M, A, D, K, T_ret_peak, W_peak_red) in the total view; ties are
> broken by arm id in ascending ASCII order. The per-category virtual best over eligible arms is the secondary view.
> Categories are never summed.

### D-5

> | **T** | storage | `T_ret_peak` = maximum, over the observation points "end of P" and "after each completed Q request", of the retained-state bits: Σ over distinct retained rational objects of (bn + bd + 1 sign bit). Scratch (per-query temporaries, TSHIFT copies, copies of coefficient lists) is **excluded**; an object counts once only where §5 declares an alias (for example D_κ is the σ² object), otherwise every stored rational counts separately. |

> **Guard set G\*** (all must be ≤ the comparator in the total view): M, A, S, D, K, G_calls, G_bits, W_bits, W_peak_red,
> W_peak_raw, T_ret_peak. **Trigger set Tr** (a ≥ 20% reduction in one, with G\* satisfied, raises the exploratory signal): M, A,
> D, K, T_ret_peak, W_peak_red. **S is guarded and not a trigger.** A lower T_ret_peak bought with higher M or A is a TRADE-OFF.

### D-6

> **Sharing metric (registered in pre-registration §11).** `J_c/Σ_c` needs executable standalone routes and per-group
> preparation dependencies that this contract does not define. **Proposed: DEFER to a follow-on contract (D-6).** P0 then
> reports the per-arm total-view ledgers only and makes no sharing claim. If D-6 is refused, a dependency table per arm must be
> reviewed before implementation.

