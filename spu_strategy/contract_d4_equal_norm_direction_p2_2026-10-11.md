# D4 equal-norm directional decision P2

```bash
python3 build/d4_equal_norm_direction/preparation_01/preflight.py
python3 build/d4_equal_norm_direction/preparation_01/cost_preflight.py
python3 tools/doc_audit.py --actual-pass 243
git diff --check -- spu_strategy/contract_d4_equal_norm_direction_p2_2026-10-11.md
```

Date: 2026-10-11. Status: DRAFT / HOLD before training; owner-set primary error ceiling 5%; abstract inference-cost bound reviewed.
Roles: Spec Author, Halt-and-Flag Implementer and Integration Auditor are
performed sequentially; do not launch additional agents.

## Scope and prerequisites

Preserve the completed P1b result: simple norm rules won the tested task.
Preserve all P1b sources, reports, qualification and campaign accounting.
Review the CPU timing attempt's single durable terminal result before launching
P2 training or qualification. Prepare this contract and bounded oracle checks
while that attempt runs. Keep D4 RTL gated on demonstrated benefit.

Use only a new software experiment and isolated evidence under
`build/d4_equal_norm_direction/`. Do not alter ISA, Surd, REGEN, Sparse Jet MAC,
transport, CPU routing or P1b mathematics. Do not infer timing, area, power,
board performance or a learned advantage from software feasibility.

## Fixed mathematical task

Enumerate nonzero integer D4 states with coordinates in [-8,8] and even
coordinate sum. Enumerate chamber representatives a >= b >= c >= |d|.
Use the 192 even-signed permutations as the symmetry group.

Assign binary decision 1 exactly when
`2 * max_root(dot(root,x)^2) >= 3 * sum(x_i^2)`;
use the 24 roots +/-e_i +/-e_j, i < j. Assign boundary equality to class 1.
Verify the independent explicit-root oracle against the efficient geometric
rule using the two largest absolute coordinates. Use integer arithmetic only;
do not normalize with floating point, square roots or approximate divisions.

Retain every norm shell containing both classes and every chamber orbit in
those shells. Treat the selected contrast shells as a constructed challenge for
norm-only rules, not a representative application workload. Do not infer application
prevalence, deployment accuracy or usefulness outside this declared distribution.
Do not select shells based on learned results. Use the witness
(3,2,2,1) and (3,3,0,0): squared norm 18, opposite decisions.

Treat this decision as D4 invariant but dependent on geometric direction
across distinct orbits. Do not attach different scalar labels to members of
the same orbit and then discard their orientation through canonicalization.
Do not claim an equivariant vector-action task; this contract has scalar output.

## Holdouts and weighting

Sort retained shells by exact squared norm; assign shell rank modulo five as
fold. Hold out entire shells and their complete symmetry orbits, including all
stabilizer-equivalent images. Verify no state/orbit occurs in both training and
test. Train on four folds and test on the fifth, for all five folds.

Use primary weights: equal shell, equal class within shell, equal base orbit
within class, uniform distinct states within orbit. Report exact fractions.
This makes the best norm-only decision's error exactly 1/2. Report uniform-state
and equal-orbit errors separately; do not transfer the 1/2 claim to them.
Reject changed labels, overlapping orbits, missing contrast classes and silent
changes to weights. Retain zero as an explicit excluded-domain fixture.

## Baselines, learner controls and cost contract

Compare constant/majority and norm-only controls, the explicit-root oracle,
the efficient exact geometric rule, and raw/canonical integer codebooks.
Include raw symmetry-augmented codebooks. Reuse the existing deterministic
integer learner only after freezing its source hash; do not change its training
schedule to favor P2. Use capacities 1,2,4,8,16,32 and bounds [-8,8].
Keep SOM as a separately proposed extension; do not silently expand these arms.

Budget coordinate storage at five signed bits per coordinate and one class bit:
21K prototype bits, plus actual representation/label/transform/table metadata.
Record equal storage-budget comparisons and report training workspace separately.
Charge canonicalization on every prediction. Do not use an uncharged test-set
lookup or omit transform/selection storage. Measure the implemented canonicalizer;
identify its exact algorithm before authorizing the experiment. Charge geometric
baselines their selection and arithmetic work as well.

Freeze executable counters for comparisons, integer additions/subtractions,
multiplications, sign/absolute operations, loads and stored bits. Count model
search and canonicalization together. Report operation vectors and integer widths;
do not invent FPGA cycles, energy or combine unlike operations into an unexplained
scalar cost. Report training cost separately from inference cost.

Report accuracy versus storage and full inference cost against the efficient
geometric rule, which already has perfect accuracy on this task. Do not set
higher accuracy than that rule as the learner's objective. Require strictly lower
storage or inference cost at or below an explicitly owner-accepted primary
held-out error rate before calling a learned result beneficial. Freeze the owner-set ceiling at exactly 1/20 (5%) for the primary held-out
error aggregated across all five folds using the declared shell/class/orbit/state
weights. Include every held-out shell exactly once. Report per-fold errors
separately; the ceiling applies to the aggregate, not a selected best fold or
uniform-state metric. Record the owner response "Roughly ~5%" as the basis for
this operational ceiling. Do not round an error above 1/20 down to a passing value.
Include baseline constants/tables and learned representation metadata in like-for-like
storage accounting; do not claim lower storage by omitting the geometric baseline's
actual cost or by comparing only prototype bits. Freeze the inference comparison
rule before training: use the owner-selected sum of primitive counts with unit
weight for every listed operation, retaining the full operation vectors and widths.
Charge four input-coordinate loads once per prediction, four prototype-coordinate
loads per distance evaluation and one winning-label load. Exclude local register
reads from memory-load counts consistently for both arms. Count distance and
index selections separately. Treat these as abstract software-accounting units;
do not interpret the sum as hardware cycles, latency, area or energy.
Do not invent post-result weights for unlike operations.

Keep exact error/cost frontiers even when no point meets acceptance. Accept a
negative result if no learned point meets the frozen acceptable-error and cost
hurdles. Stop this bounded tranche without extra capacities, seeds or task changes
in that case. Require demonstrated benefit and a separate reviewed implementation
contract before proposing D4 hardware.

## Implementation and verification gates

1. Review task/oracle feasibility and all five holdouts.
2. Freeze the owner-accepted error threshold, cost comparison rule, canonicalizer,
   cost counters, learner hashes and falsifiable controls.
3. Review CPU timing's terminal result; do not wait in the agent session.
4. Prepare an isolated snapshot, a refusing-overwrite launcher and evidence manifest.
5. Obtain a new owner budget specifying experiment attempts, per-attempt timeout
   and cumulative cap; do not reuse P1b's closed slots. Request qualification
   budget separately. Do not launch either campaign without those frozen budgets.
6. Execute the frozen experiment via `tools/run_detached_job.sh` with a new output
   directory and local terminal notification; end the turn after LAUNCHED.
7. Audit every prediction by measuring disagreement against the independent
   root oracle. Recompute learner errors, confusion counts and exact weighted
   rates from the recorded predictions. Treat learner errors as experimental
   results, including errors exceeding acceptance; do not fail qualification
   merely because the learner disagrees with the oracle. Fail verification for
   mislabeled truth, incorrect error accounting, changed source hashes, leakage
   or violated execution contracts. Separate unsupported/unrun dimensions from
   implementation mismatches. Record qualification integrity and experimental
   benefit as separate verdicts.
8. Run the mandatory repository, scoped, ROTC/IROTC, robotics/SOM/Lucas/Padé
   gates and separate `A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t
   rplu2pade all` in the independently budgeted frozen qualification.

Use `bash tools/verify_repo.sh`, `TB_FILTER=d4 python3 run_all_tests.py`,
`python3 software/tests/test_rotc_vm_rtl_trace.py`,
`python3 software/tests/test_irotc_vm_trace.py`,
`python3 software/tests/test_rational_robotics.py`,
`python3 software/tests/test_rational_som.py`,
`python3 software/tests/test_lucas_mac_oracle.py`, and
`python3 software/tests/test_pade_batch_inversion.py` as the unchanged full gates.
Treat the Padé result as a repository qualification gate, not D4 physical timing.

Halt and flag disagreement between truth/reference implementations, leakage,
ambiguous task invariance, incomplete
cost accounting or altered protected P1b evidence. Do not amend a frozen experiment
in response to its outcomes. Record any revision as a separate reviewed contract.

## Preparation record (not experiment qualification)

Use verified suite count 243 for the audit command above. Its provenance is
[the frozen decoder repository regression](../build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/regression_02/repository.stdout.log),
Total PASS 243 / Total FAIL 0, with its COMPLETE/exit-0 campaign result. Replace
243 with the actual verified full-suite count for a future P2 qualification
snapshot; never use a scoped count or an expected count as verification evidence.
Do not interpret that snapshot's count as fresh verification of a changed checkout.

Review [task feasibility](../build/d4_equal_norm_direction/preparation_01/preflight.json),
[executable costs](../build/d4_equal_norm_direction/preparation_01/cost_preflight.json)
and [manifest](../build/d4_equal_norm_direction/preparation_01/manifest.json).
The bounded preparation checks passed: 37 contrast shells, 243 orbits and
24,504 distinct states; five held-out folds contain 52/49/56/50/36 orbits.
The independent explicit-root oracle agrees with the efficient geometric rule.
Corrupted labels and orbit leakage reject. Canonicalizer agreement and operation
counter checks pass across all retained distinct states. Protected P1b evidence
hashes match before and after preparation.

Use the five-comparator sorting network (01,23,02,13,12), absolute coordinates
and even-sign parity to form the D4 chamber representative. Charge four absolute
operations, five comparisons, ten selections, four sign tests, three XORs,
one sign selection and an executed negation where applicable. Record primitive
operations as software accounting units; do not claim hardware instruction costs.
The efficient geometric baseline charges four absolutes, six comparisons,
ten selections, five multiplications, five additions and two constant shifts.
Retain the implemented operation-vector histograms. Do not claim learned search
costs are validated before implementing and testing those counters.

Keep training and full qualification NOT RUN. Preserve the no-overwrite preflight
outputs; use a new evidence directory for any revision. Oracle feasibility does
not demonstrate a learned advantage. Do not start an experiment until CPU timing
review and the fresh budget gate above are satisfied.

## CPU prerequisite and pre-training cost review

Review [CPU timing terminal evidence](../build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/timing_01_review.json):
TIMEOUT/124 at 7,200 seconds during routing. Both mappings passed; the selected
exact-digital CPU has 80 DSPs with Surd enabled, zero without. Legal routing,
complete required timing coverage and 25 MHz acceptance remain unresolved. The
authorized timing slot is consumed. This review satisfies P2's prior-review gate;
it does not authorize another CPU timing attempt.

Execute and review the bounded cost check independently of training:

```bash
python3 build/d4_equal_norm_direction/cost_review_01/review_cost_bounds.py
```

Preserve [the cost-bound record](../build/d4_equal_norm_direction/cost_review_01/cost_bound_review.json)
and its no-overwrite behavior. The check exercises the declared predictor,
verifies winner selection against the retained learner's winner routine in
5,892 predictions, checks deterministic tie selection, and retains actual vectors.
It includes synthetic prototypes and inputs; it does not fit any model or report
learned accuracy. The algebraic cost bound is parameter independent for the
specified full-distance-scan implementation only.

The efficient geometric rule costs 36 abstract units, including input loads.
A raw K-prototype scan costs 18K+2 units. K=1 costs 20 units but predicts one
constant label, giving exactly 1/2 primary error under the declared balanced
weighting, regardless of training. Eliminating its unnecessary distance scan
reduces cost but leaves the same unacceptable error. Every K>=2 costs at least
38 units, more than the perfect rule; canonicalization adds cost.

Halt the training-launch preparation for the current inference-benefit hypothesis:
no declared full-scan capacity can both meet the 1/20 error ceiling and reduce
inference cost in the approved model. Do not spend a training budget to search
for a result excluded by this bound. Total storage benefit remains UNVERIFIED:
21K prototype/label bits are known, but a complete comparable program/metadata
storage ledger is not implemented. Do not assert a universal storage lower bound
or claim that all alternative algorithms are excluded.

Retain this as a bounded pre-training cost review, not a trained experiment,
full qualification, hardware-benefit result or reopening of completed P1b.
Require a separately reviewed, plausible storage-benefit hypothesis or changed
implementation contract before continuing toward training. Do not alter the
agreed error ceiling, cost weights or task in response to this finding.
