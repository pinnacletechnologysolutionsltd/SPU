# QCG-0 P0 draft execution-contract independent review

Date: 2026-10-23. Reviewer: `/root/qcg0_fixture_reviewer`, independent of the author and HEX-SOM acceptance context. Author scratch seen: no. **Overall disposition: REVISE.** W31 first-refusal stages are **unavailable under this draft**, not certified and not guessed. No implementation, freeze, pilot, benchmark or hardware work is authorized.

Read `P0_CONTRACT_REVIEW_AUTHORIZATION.md` first and verified its three pins before review: contract `21fb45af84d609c3c127010a10b0c2824aaac4772ab8d95a4abd9f5d8d2b8bfc`, pre-registration `eade4b5f0957c3679c94b67d8f4b1f6b6d005d65316a5337e6c8dfb9370b98dd`, Revision 3.1 diff `244e73004c51b3339465ac65eb0f97da5d5ae01d4d48b281f416de922f8a4bff`. All prior certificates, references, manifests, authorizations and degree addendum referenced by §0 also match their existing pins. Read the whole contract, pre-registration, editorial diff and relevant existing reference structures. Only read-only hashes/text/JSON projections and new review artifacts were used. No prior input was edited or regenerated, and no author scratch path in a diff header was accessed.

**Calculation budget used: zero of two invocations.** Local counts below are independently derived analytically from the printed loops. Stage semantics are insufficient; running a repaired oracle would invent a contract and is expressly disallowed. `P0_CONTRACT_REVIEW_EXPECTATIONS.json` records the derivable counts and a null W31 stage table with the reason. It is not a candidate or P0 result. The external manifest records all identities.

## Section 10 checklist

| # | Verdict | Evidence |
|---|---|---|
| 1 | REVISE | Literal/data classification and guard-versus-trigger intent are explicit, but W(D) is wrong for actual division products, raw shift/comparison rules are missing, and phase totals cannot add peaks/storage. Comparator needs a tie-break and refusal eligibility. See A and B below. |
| 2 | REVISE | Profile bounds agree numerically with the prior limits. Unique stages cannot be derived; statuses and atomic diagnostic accounting are incomplete. See B. |
| 3 | REVISE | True Cell A pair, no query curvature division, S3 final null and monotone Cell B formulas are correct. But the two reference files need different index-7 mappings, S4 literal coverage is missing, and whole-query versus observable-level refusals conflict without task granularity. See C. |
| 4 | REVISE | The four hand counts are correct for the displayed query routes. HORNER/DECAS/TSHIFT/FDSTEP local loops are executable, but preparation/call identity, retained-state copying, some expanded-arm flag state and sequential scheduling are not fully frozen. See D. FD exclusion and the C1 equivalence choices remain pending D-1/D-2. |
| 5 | PASS | Specified exact jet degrees and PH3h order 4 agree with the degree addendum; truncated order-2 cubic and harmonic states remain E2/APPROX rather than exact trajectories. The wire status for refusing APPROX still needs inclusion under checklist 2. |
| 6 | REVISE | There are **14** §7 rows, not 13. Local operation formulas and all four hand counts pass independent derivation, but LU-P is false for nonadditive quantities and preparation/equivalence expectations are not fully determined. See E and the expectation JSON. |
| 7 | REVISE | All 20 mutant rows inspected individually below. X-3's omitted h-composition has no effect on the h=1 Cell B; X-10's invariant does not detect globally omitted preparation; X-16's immediate repeated refusal cannot establish cache preservation. W31 stages are unavailable for the stated reasons. |
| 8 | REVISE | Resource envelope is bounded and still proposed, but launch prerequisites are not fail-closed in the shell; existing logs can be overwritten after mkdir failure; EXIT alone creates no terminal marker; 137 is not proof of timeout. Complete pin manifest and attempt-budget semantics remain prerequisites. See F. |
| 9 | PASS | Certified files remain unchanged, source pins match, and no mathematical fixture is reopened. Revision 3.1's route relabel, indexed metric, explicit guard and stale-sentence cleanup preserve the certified numerical meaning. Pending policy changes do not count as accepted mathematics or owner decisions. |
| 10 | REVISE | C1/B-PH operation equivalence is properly proposed as a design consequence, not measured superiority. However §1 item 4 asserts a total-view shift inequality before the preparation ledger uniquely exists, and §2 calls a proposed owner policy an “owner decision” while D-1…D-5 are pending. Scope that inequality to a conditional prediction and keep policies proposed until accepted. |

## A. Arithmetic and measurement defects

**Division width proxy:** for a=n_a/d_a and b=n_b/d_b, raw division forms n_a·d_b and d_a·n_b, so its schoolbook product proxy is bn(a)bd(b)+bd(a)bn(b). The draft instead uses the multiplication proxy bn(a)bn(b)+bd(a)bd(b) for both M and D. If W_bits is deliberately a different abstract proxy, rename it and remove the claim that it accounts for the actual raw integer products; otherwise correct D. Do not silently repair it in implementation.

For LU-W the printed inputs have bit lengths (31,2) and (3,11). Multiplication W_bits is 115; raw product is 5368709120/3072 (33/12 bits), reduced product 5242880/3 (23/2 bits). With inputs included, reduced peak is at least 31, not just the result's 23. For division of those same inputs the correct cross-product proxy would be 347, while the draft assigns 115. This is a small analytic counterexample, not an executed width campaign.

Raw checks must cover all actual intermediate products and sums, not just a final numerator/denominator pair. In an addition, cross-products can exceed a bound even when their sum cancels. Signed denominator correction, zero/divisor testing, import validation, shifts' parity normalization and comparisons' cross-products need exact rules: which are K, which raw values are checked, what ordering is used, and whether they update W peaks/G diagnostics. In particular S cannot mean “normalization and width checks disappear”; parity reduction may avoid a gcd call but must preserve canonical form and bounds. Whether bn(0) uses the declared minimum also needs to be consistent for G_bits and storage.

**Aggregation:** M,A,S,D,K,G_calls,G_bits,W_bits are additive counters. W_peak_red/raw aggregate by maximum, not addition. T_total is retained state at a defined observation point or a declared maximum, not P-storage plus Q-storage. Specify alias/dedup rules, scratch versus retained state, and how state changed by sequential stepping is summarized over the tape. Otherwise total-view comparisons and LU-P are not executable as written. Peak live scalar reporting required by the pre-registration should also have a defined reported field; it need not be added to a guard by this review.

Guard/trigger membership is otherwise clearly separated: S is guarded, not a trigger. The lexicographic tuple is a proposed deterministic *ranking*, not an intrinsic definition of a componentwise best arm. Add a fixed arm-id tie-break and require a comparator to have complete successful matched outputs; refused/nonapplicable arms cannot win by accumulating less work. Report the per-category virtual best separately as already proposed. D-3/D-4/D-5 are owner choices, not accepted here.

## B. Refusal stages and atomicity are not yet determined

`arm.phase.procedure.opindex` does not identify repeated invocations of the same helper for different polynomials, queries or nested composition calls. HORNER operation 1 occurs for x, y and other outputs. The first failing point also depends on a preparation DAG/order that §5 does not supply. Schoolbook product summation order and zero initialization, derivative construction, integral order, composition buffers, coefficient conversion ratio generation, accumulation initialization and cache derivation order are not frozen at elementary Q-operation resolution. W31 preparation can refuse before query-time, so a query-only route is insufficient.

Freeze a unique call/output/query identity or a global event index, an exact operation enumeration including width subchecks, and a complete preparation order before requesting literal stages. Specify whether imports are checked and whether a failed raw check precedes gcd/reduced checking. Do not infer stages from final values. **No W31 first-refusal stage is certified in this review**, and no bounded calculation slot was spent inventing one.

§3's status grammar lacks `OUT_OF_DOMAIN` used in X-5, `NOT_PRIMITIVE_RETIMING` from the registered controls, and a consistent wire encoding for APPROX/E2 rejection. NOT_APPLICABLE is variously a direct arm status and a refusal code. Define the exhaustive schema and whether PREPARATION_REFUSED wraps ARITH_LIMIT. NONMONOTONE in Cell B versus OUT_OF_DOMAIN for traversal length is reasonable only when the requested operations and their refusal scope are explicit.

Query rollback must distinguish committed result/cache/ledger state from durable diagnostic evidence about the attempted failure, including its stage and consumed attempt work. Keeping preparation-failure ledgers but rolling back every query-visible counter is not by itself a complete attempt accounting rule. Independent global resource-budget counters must not reset on refusal, warm-up or timed repeats. State atomicity needs a before/after comparison and subsequent accepted query, not only the same failing query again.

## C. Output/reference coverage

The original `QUINTIC_FIXTURE_VALUES.json.cell_A` stores raw N, so double index 7 exactly once. The R2 `CellA_adapted_true_curvature_pair` already stores true 2N, so **do not double it again**. §4's combined “references (index 7 doubled)” must spell out the separate mappings. Sequential reference rows contain true curvature quotients plus source polynomials, not literal N_kappa/D_kappa rows; either define a certified adaptation or supply the missing rows under separate review. Do not confuse a check-only quotient with a charged output division. X-11's D=0 applies to **Q phase**, since preparation legitimately integrates using D.

The registered PH3/PH5 sequential tables, Cell B square-retiming rows, CH1, b1–b9, loops and harmonic operator exist. The pinned JSON has **no literal phi_ns/phi_rev S4 tangent/speed/curvature sample tapes**. Existing certificates prove their formulas and describe the stationary behavior, but §8 X-2 cannot cite nonexistent tangent/speed rows. Negative generator sign alone (b5) changes neither h's sign nor hodograph and cannot exercise a negative-h mutant. Freeze the actual h-form reversal operation and its literal expectations before implementation; do not regenerate the existing fixtures.

For stationary controls, a direction query can return d while tangent/curvature queries refuse. If S4 is a single whole-query transaction, §3's “no values” rule would suppress d as well. Explicitly separate operation-level queries/statuses or define an atomic bundled result schema before using the reference as a correctness gate. Likewise phi_bad can have exact oriented/piecewise oracle diagnostics while the single-polynomial accumulated-length query refuses; define which API produces which output. The positive square-retiming Cell B row itself is consistent.

## D. Procedure completeness and route counts

Independently counting the printed loops gives the displayed Cell A B-Horner 28M/27A/1K, B-PH=C1 26M/23A/2S/1K; Cell B B-COMP 21M/18A/1K and C1 33M/31A/1S/1K. Under one-gcd-per-M/A/D these have 55,49,39,64 gcd calls respectively. This does not establish raw widths, preparation counts or complete phase equality.

In TSHIFT the descending i order correctly preserves polynomial shifting; DECAS's ascending j order correctly reads the previous level's neighbor before mutation. FDSTEP's ascending j order is also correct. But sequential code must emit t=0 before the first step, stop at 16/16, and specify how the next S sample/increment is obtained and stored. Query C2 must shift a fresh copy for each random-access query; otherwise repeated/nonmonotone tape queries modify the retained jets. E-BEZ/E-TS must retain or deterministically derive phi′ for their flag; it is absent from their retained-state entries. TSHIFT-based arm state copies and phase boundaries must be explicit for stages and T_total.

Preparation primitive descriptions do not yet fix counts or stages. The common-source h=1 declaration also needs scope: it covers the screen fixtures, while PH3h and negative-h capability tasks need their separately specified source/algorithms. Accepting C1 equivalence is D-1; identical source-level query operations are a legitimate design choice, but equality of every phase/category follows only after the full preparation and storage policies are identical and fixed. FD's Cell A NOT_APPLICABLE is a proposed scope choice D-2, not a reviewer-accepted owner decision. The phrase “any fallback is Horner” is too universal: it is the chosen P0 policy, not a mathematical impossibility of arbitrary polynomial evaluation methods.

The registered standalone-versus-joint sharing metric also needs executable standalone routes and a preparation/cache charging schedule. A list of joint arm algorithms alone cannot establish J_c/Sigma_c. The contract should explicitly implement or defer that registered metric, rather than imply it is covered by screen-ledger totals.

## E. Every ledger row and mutant path

§7 has 14 rows: LU-H, H0, DC, TS, FD, S, VAL, D, W, G, P and EQ-1,2,3. Analytic formulas and a degree-2 example are filed in the expectation JSON. FDINIT's written policy gives d(d+1) M and 3d(d+1)/2+d A, hence 5d(d+1)/2+d gcd calls. This can become an independent expected-count gate, unlike a self-reconciled total. LU-P needs type-specific aggregation. EQ-1/EQ-2 are proposed equivalence invariants, not fully derived preparation expectations; EQ-3 also needs the complete reference mapping described above.

| Mutant | Review of path/expectation |
|---|---|
| X-1 | Exercised: nonzero N exists on the Cell A tape; double original raw index 7 only once. |
| X-2 | REVISE: b5 is a generator gauge change, not negative h. H-form reversal could exercise both defects, but its procedure and literal tangent/speed rows are not supplied. |
| X-3 | Partially exercised: omitting phi′ changes Cell B, but omitting h composed with phi does **nothing** when original h=1. Add a separately certified nonconstant-h retiming control or narrow the mutant; do not claim the current row kills it. |
| X-4 | Oriented total 0 versus accumulated total 8/3 is a valid exact diagnostic. Specify how that diagnostic coexists with the class refusal. |
| X-5 | Mathematically valid class refusal; register OUT_OF_DOMAIN in the status grammar and the exact request scope. |
| X-6 | Exercised by the existing b7/b9 raw and gated reference layers. |
| X-7 | Literal-double/data-half cases exercise classification; freeze exact scalar/event rules so their ledger expectation is executable. |
| X-8 | Exercised by the zero constant term in LU-H0; no zero skipping. |
| X-9 | Rule is valid; choose a concrete integer-result operation/input and verify its expected gcd event, not just an “any result” template. |
| X-10 | REVISE: omitting all preparation can still satisfy P+Q=total; two zero preparation ledgers can even agree. Supply independently fixed nonzero preparation counts/states, not the invariant alone. |
| X-11 | Valid only as Q.D=0 for Cell A; P.D is nonzero from integration. Fix the stated scope. |
| X-12 | FDINIT path exists; assert its independent count including grid-point generation and difference table, not FDSTEP alone. |
| X-13 | Printed LU-TS/LU-DC formulas exercise count defects; retain output equivalence checks as well, since correct counts alone do not establish correct values. |
| X-14 | Degree-2 truncation of PH3's nonzero cubic position term exercises the class error; fix the APPROX rejection schema. |
| X-15 | BLOCKED derivation under draft: no unique W31 stage table; freeze operation/width/stage semantics first. |
| X-16 | REVISE: the same refused query may still refuse before reaching a poisoned cache entry. Compare full committed state before/after and follow with a known admissible query as well as the immediate repeat. |
| X-17 | Existing nonzero harmonic operator is an adequate class-control reference; not a zero-state trajectory test. |
| X-18 | Stationary phi_ns at 0 exercises the defect, provided direction and tangent/curvature requests have explicit separate refusal scopes and literal reference schema. |
| X-19 | Query equality is a legitimate declared invariant; full-phase equality still depends on frozen preparation/storage rules. |
| X-20 | FD exclusion can exercise the P0 policy after D-2 acceptance; fix its status encoding. |

The pre-registration's controls also include cache perturbation, reversal twice, non-polynomial/primitive retiming refusals, C4 and 3-4-5 rotation expectations. If those remain required by the registered P0, explicitly map them into the suite or list their proposed deferral as a scope change for owner acceptance. Twenty mutant rows do not automatically cover every registered semantic control.

## F. Launch and resource evidence

The command is proposed, not run. Its individual cd, pin check and mkdir commands lack fail-fast guards. If the leaf already exists, mkdir fails but the next timeout line still runs and truncates old stdout/stderr with `>`; a failed cd or pin check can similarly fall through. The Python pin check does not undo already overwritten evidence. Freeze a fail-closed launcher that validates identities, requires a new evidence leaf, refuses overwrite and records external provenance before launch. Do not implement that launcher during this review.

`echo $? > EXIT` records a number, not exactly one durable COMPLETE/FAILED/TIMEOUT marker. The comment creates no markers. SIGKILL exit 137 can also arise from OOM/external kill or the program's own exit status; it is not proof that the wall-clock timeout expired. Root contract §4.2 requires a proven timeout outcome, with exit 124, distinct from test failure/unavailable result. A deadline owner outside the killed process must persist and attribute the terminal result, with exactly one terminal marker and readback. An ordinary post-run pin check must be recorded and must not mask the underlying exit. The future launch must meet the repository's applicable evidence requirements; this draft is not a substitute for them.

The one-invocation/60-second/1-GiB/no-child/no-network/no-device/no-install bounds are explicit. Define the million-operation event set and whether conformance, all mutants, warm-up and three timed passes consume it; “across all arms” alone is insufficient. Rolled-back failures still consume actual execution work. Clarify whether output cap includes logs/provenance and how a violated cap is durably reported. Oracles are uncounted for comparative costs but must stay under the same invocation's wall/memory/output limits. Numerical bounds do not grant a retry or authorize splitting.

PINS.sha256 does not yet exist and cannot be certified complete; freeze the full implementation/source/reference/procedure identities, scripts and tool versions under the later implementation authorization. The mutually related source/pins identities need a noncircular external manifest policy. Do not treat the existing prerequisite prose as proof of future readiness. The draft's 60-second ceiling itself does not mandate a detached job expected to exceed 60 seconds, but any later longer deterministic job remains subject to the repository detached-runner rule.

## Required next action and boundary

Author must revise the ledger/width model, aggregation, operation/stage order, status/refusal schema, reference coverage, mutant controls and fail-closed evidence protocol; then independent review can derive unique refusal expectations without architectural invention. D-1…D-5 remain pending owner choices. A revised contract, complete pins and independent PASS are prerequisites, not implementation GO. This review leaves freeze, implementation and P0 HOLD. No other campaign or hardware was touched.
