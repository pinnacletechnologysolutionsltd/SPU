# D4/E8 work-limit amendment — independent review draft

```bash
python3 -m json.tool build/d4_e8_math_20261013/ledger_diagnostic_01/result.json
python3 -m json.tool build/d4_e8_math_20261013/ledger_diagnostic_01/counts/summary.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_d4_e8_work_limit_amendment_2026-10-13.md
```

Date: 2026-10-13. Status: DRAFT / NOT RATIFIED. Qualification HOLD / NOT RUN.
Authority: owner requests a narrow amendment documenting observed maxima,
proposed revised limits and outstanding independent accounting review. Author,
evidence reconciler and draft reviewer are the same preparer; independent
reviewer identity and sign-off remain PENDING.

## 1. Immutable scope and diagnostic disposition

Add only this amendment and its review record under
`build/d4_e8_math_20261013/limit_amendment_review_01/`.
Preserve the [comparison contract](contract_d4_e8_comparison_readiness_2026-10-13.md),
[ledger diagnostic contract](contract_d4_e8_ledger_drycount_2026-10-13.md),
Profile implementation, original120 fixtures, five applicable approaches and
all frozen evidence/source manifests. The E8 root-image proposal stays separate.
No source repair, changed cost schedule, new diagnostic or qualification run
is authorized. No CPU/RTL/ISA or hardware workflow change is authorized.
Surd CPU/Himbächel backend repair retains physical engineering priority.

Accept the diagnostic as COMPLETE / diagnostic checks PASS for its recorded
scope. The sole terminal marker is COMPLETE, exit0, duration569seconds under
the1800-second operational timeout. That timeout is not a qualification budget.
All540 applicable arm evaluations cover120 frozen cases, not540 independent
workloads. Seven focused preparation tests passed before the diagnostic.
Do not promote these observations to formal comparison qualification.

## 2. Verified work and storage evidence

Source directory: `build/d4_e8_math_20261013/ledger_diagnostic_01/`.
Work columns count the recorded primitive schedule, not CPU instructions/cycles.
Case excludes table setup; cold total includes setup and all recorded stages.
Each column is its own maximum; storage maxima are simultaneous live peaks
within an evaluation, not a sum of separate object maxima.

| System / approach | Max case work | Max setup work | Max cold total | Max live bits |
|---|---:|---:|---:|---:|
| D4 coordinates | 145,974 | 110 | 146,084 | 13,440 |
| D4 generator word | 202,323 | 110 | 202,433 | 14,528 |
| D4 dense matrix | 6,323,268 | 26,672 | 6,349,940 | 32,864 |
| D4 Surd bridge | 1,359,643 | 3,232 | 1,362,875 | 23,136 |
| D4 signed permutation | 92,910 | 142 | 93,052 | 12,428 |
| E8 coordinates | 221,208 | 338 | 221,546 | 17,792 |
| E8 generator word | 280,981 | 338 | 281,319 | 19,392 |
| E8 dense matrix | 51,282,138 | 205,420 | 51,487,558 | 110,432 |
| E8 Surd bridge | 2,689,301 | 12,812 | 2,702,113 | 37,984 |

Largest cold total witness: `E8/inverse_pair/128/3`, matrix arm,256 tokens.
Largest storage witness: `E8/inverse_pair/128/0`, matrix arm,256 tokens.
The original2,000,000 case ceiling was exceeded40 times: D4 matrices10,
E8 matrices25, E8 Surd5. All540 storage observations are below1,048,576bits.
Including setup under the same2,000,000 ceiling still gives40 exceedances.
These findings apply only to the frozen fixtures and recorded model.

Original source manifest SHA256:
`0fb5d5d2442007180f5cdc6e387a3362d7c6a753e18fbc4c172d55d6b773d231`.
Fixture SHA256:
`e277bb68563ec9c5f318675ef5bbcf8fb419d3391ab70ae93090f7b96d0dd789`.
Diagnostic summary SHA256:
`9c998777ea3ef18ae0ca2162472ee0d74943460d124eb908d811fbdaefac26a1`.
Full540-row evidence SHA256:
`0022fcb5466c0ef6ebc964ddfaff841267142bfd79c09bf5833ea9b57a02337f`.
Retain the runner result and complete evidence inventory in the review record.

## 3. Proposed common ceiling; implementation unchanged

Propose64,000,000 charged primitives per arm per fixture, applied to the complete
cold total. Include admission, input wire, table setup, setup conversion,
descriptor construction, conversion, evaluation, final lattice validation,
output/descriptor serialization and ownership cleanup. Do not reset the total
at stage boundaries or exempt setup. Continue reporting setup and materialization
separately for interpretation, without deducting them from this common ceiling.
The current diagnostic's case/setup separation remains original evidence;
the proposed inclusive refusal policy is a prospective contract amendment.

Observed inclusive maximum51,487,558 leaves12,512,442 units below this candidate
ceiling. This is empirical headroom over the existing schedule, not a proof that
an amended instrumenter, larger inputs or new fixtures would fit. Do not adopt
64million solely because the diagnostic maximum fits. Review schedule omissions
and lifetime completeness first. Any source/schedule correction requires new
identities and separately authorized validation; this amendment starts no run.

Retain the proposed1,048,576-bit simultaneous live-storage ceiling, signed64
normalized slots, signed256 temporaries and maximum256tokens. These research
limits remain proposed, not CPU architectural limits. Storage headroom does not
validate the completeness of the inventory or correctness of refusal behavior.
The Profile implementation remains at2,000,000 work units and is not edited.
Ratification must name the exact future enforcement implementation and identity;
neither this document nor owner review of it grants execution authorization.

## 4. Charged stages and exact independent-review obligations

Reconciliation confirms that each row's categories and stages sum to its work,
and that setup plus case work equals the cold total. Recorded stages are
admission, input_wire, setup, setup_conversion, construction, conversion,
evaluation and commit. Commit contains output lattice checks, byte processing
and cleanup; inclusion in its total does not prove every required operation
was instrumented. Independent review must resolve the following specific items.

| Area and source boundary | Required review finding |
|---|---|
| [meter](../software/research/lattice_drycount/meter.py): scalar/op/test | Define compound predicates versus individual comparisons; validate repeated operand/result type/range charges and indexed reads/writes; check consistency for constants, aliases and already validated inputs |
| meter: loop/constant/allocate/release | Verify initialization, all conditions including termination, increments, constant moves, allocation validity and cleanup; separate observer bookkeeping from target work |
| [admission](../software/research/lattice_drycount/admission.py): admit/lattice | Check shape/type, token limits, lattice parity and sum checks; reconcile ownership before input copies and treatment of incoming fixture data |
| [exact](../software/research/lattice_drycount/exact.py): gcd/quotient/normalize | Check every Euclid iteration/termination and state move, absolute/sign operations, remainder validation, checked quotients, denominator rules, raw cancellation growth and committed bounds; resolve direct tuple access versus charged reads |
| exact: add/multiply | Verify schoolbook rational and full Surd schedules, factor3, both negations for Surd subtraction, normalization frequency and any redundant counted work; no selective optimizations between approaches |
| [matrices](../software/research/lattice_drycount/matrices.py) and [spatial](../software/research/lattice_drycount/spatial.py) | Confirm trusted-table load/build charges, dense zero-start dots, left composition, identity initialization, deferred evaluation and conversion/materialization costs; retain independently derived count formulas |
| [signed](../software/research/lattice_drycount/signed.py) | Check conventional descriptor setup/composition, lookup reads, XORs, conditional negation and old/new lifetimes; do not infer a native SPU advantage |
| [wirecost](../software/research/lattice_drycount/wirecost.py) versus [wire](../software/research/lattice_drycount/wire.py) | Review header/count/shape calculations, byte and token addressing, pack/unpack, padding/sign/normalization checks, temporary byte lists/views and observer encode/decode exclusions; resolve uncharged dispatch/metadata arithmetic explicitly |
| [arrays](../software/research/lattice_drycount/arrays.py), meter frames and [adapter](../software/research/lattice_drycount/adapter.py) | Prove each declared register capacity covers helper arguments, intermediate results, accumulators and GCD/conversion work; check fixed headers, table aliases, frame/control slots, matrix views and global simultaneous lifetimes |
| [ledger](../software/research/lattice_drycount/ledger.py) and [checks](../software/research/lattice_drycount/checks.py) | Distinguish replay of emitted observations from proving schedule completeness; review every-arm independent witness coverage, formula scope, scalar/denominator widths, retained-output checks and corruption controls |

The full540-row diagnostic used independent rational output checks and selected
closed-form arithmetic counts; full primitive-event replay was performed only
on short literals. All five D4 literal approaches had replay coverage. No
independent human/agent sign-off exists yet. A consistently omitted operation
or allocation could escape emitted-event replay and the selected formulas.
The recorded raw-width maximum66 includes serialization masks/constants; it is
not by itself a measure of mathematical coefficient growth.

## 5. Ratification and later authorization gates

1. Assign an independent reviewer. Record identity, date, independence, exact
   reviewed source/fixture/evidence hashes and item-by-item dispositions above.
2. Accept the ledger schedule and ownership model explicitly, or enumerate
   concrete defects and proposed corrections without modifying frozen evidence.
3. Confirm64,000,000 covers all reviewed cold totals; require renewed limit
   review if corrections change the model. Independently accept or revise the
   storage inventory and each finite-width/refusal obligation.
4. Ratify a prospective amendment naming the single common ceiling, enforcement
   boundary and corrected source identities. Do not substitute this diagnostic
   for missing qualification or complete refusal checks.
5. Only then prepare a separate exact qualification command with maximum
   attempts, per-attempt wall-clock timeout, cumulative allocation and retry
   policy. Obtain explicit owner execution authorization before launch.

Current disposition: diagnostic COMPLETE / checks PASS; this amendment DRAFT;
independent accounting review PENDING; qualification HOLD / NOT RUN. No additional
execution is launched. No FPGA performance, memory realization or SPU advantage
is claimed. Repository documentation audit findings remain separately recorded.
