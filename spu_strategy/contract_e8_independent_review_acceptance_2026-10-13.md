# E8 independent review — acceptance boundaries

```bash
python3 -m json.tool build/e8_root_images_20261013/workload_preparation_02/left_kernel.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_e8_independent_review_acceptance_2026-10-13.md
```

Date: 2026-10-13. Authority: owner explicitly adopts admission, ownership and
observation as independent-review acceptance criteria. Status: CRITERIA RECORDED;
review PENDING; complete accounting and qualification HOLD. No campaign,
new execution allocation, implementation repair or FPGA work is authorized.
Same preparer records the criteria/evidence; independent reviewer UNASSIGNED.

## Immutable evidence and review subject

Add this separate addendum and a review template/evidence record under
`build/e8_root_images_20261013/independent_review_acceptance_01/`.
Do not modify frozen E8 source, proof dossier,384-configuration plan, short
kernel, original D4/E8120-case comparison, diagnostic evidence, ceilings or
hardware sources. Preserve the12-source E8 milestone and8-source corrected
workload packet, plus their previously protected inventories.

Review the [proof/accounting packet](../docs/E8_ROOT_IMAGE_MATHEMATICAL_REVIEW_PACKET_2026-10-13.md)
and [workload preparation contract](contract_e8_review_accounting_preparation_2026-10-13.md).
Separate mathematical sufficiency, implementation agreement, instrumentation
completeness and reviewer independence; none substitutes for another.

## A. Admission acceptance

The reviewer must establish all of the following:

1. External descriptors receive strict schema, length, actual-integer/range,
   reserved-ID, root/basis identity, duplicate-image and complete36-entry Gram
   validation under the verified context. Check the unimodular basis/index
   argument and identification with W(E8); determinant sign is unrestricted.
2. Define validated internal state and its context binding, construction,
   ownership and lifetime. External bytes/raw tuples cannot assert validity
   merely through a caller-supplied Boolean flag. Context identity and setup
   verification must precede reuse of a validation result.
3. For each internal operation identify the required token/index/domain/bounds
   checks and a proof of invariant preservation. LEFT action uses the verified
   exact reflection table; table involution alone does not prove Gram preservation.
   RIGHT/general composition and inverse require their own exact proofs and
   context agreement. Charge every check and lookup actually performed.
4. Avoid unnecessary repeated full external admission only where the reviewed
   internal-state contract and invariant proof justify it. Do not remove checks
   from the frozen reference or retroactively revise recorded costs. An optimized
   internal entry point needs its own source identity, schedule and controls.
5. Require atomic returned state and no caller mutation on refusal. Software
   observations do not qualify future CPU register ownership, reset or backpressure.

Existing evidence: exact external Gram/wire references and finite operator
witnesses are PREPARATION PASS. Public reference operations currently repeat
Gram admission; the metered prototype also performs two admissions. A reviewed
validated-state API and complete optimized schedule are NOT IMPLEMENTED.
Therefore admission-boundary closure remains PENDING.

## B. Ownership acceptance

The reviewer must establish all of the following:

1. Inventory shared immutable tables, private descriptors and all temporary
   objects separately, including setup/decoding/reduction/conversion/serialization
   storage. Describe every acquisition, alias, last use and release. Validate
   fixed register capacities against actual helper requirements.
2. Bind aliases to one owned object. Basis rows that reference root rows are
   not extra coordinate copies; independently instantiated contexts are copies.
   Include headers/context bindings and modeled control state. Explain all
   exclusions, including host objects/pointers and observer trace storage.
3. Reconstruct global simultaneous live peaks from lifetimes. Never sum
   unrelated maxima or omit retained input/output and intermediate buffers.
   One static object shared by K clients is counted once; K private objects
   are counted K times. Each baseline owns its required tables, not automatically
   the root-image context, and may not borrow free candidate computation.
4. Keep setup count, simultaneous context count and client concurrency distinct.
   Private/shared lockstep are matched concurrency controls; cold serial is a
   separate scheduling control. Specify any access/arbitration/bandwidth model
   before interpreting simulated time. Current primitive counts contain no
   evidence of hardware table bandwidth or contention performance.

Existing evidence: the proposed static context inventory is307,680bits; the
single-kernel recorded peak is312,480bits and retained storage307,776bits
(context plus96-bit output descriptor). All384 ownership records are prepared
metadata; private/shared concurrency and complete workspace lifetimes have
not been executed or independently closed. Ownership review remains PENDING.

## C. Observation acceptance

The reviewer must establish all of the following:

1. Freeze identical initial vectors, chronological LEFT-action tokens and
   materialization checkpoints for all representations. The observable at t
   is w_t(initial_vector). Include final t exactly once and preserve descriptor
   state at checkpoints. Do not reinterpret the cumulative prefix as an
   incremental update applied to a previously materialized vector.
2. Check exact (tick,client,value) equivalence against an independent reference.
   Charge ordinary/reduced-word evaluation, coordinate/basis conversion, matrix
   decoding and every deferred update before comparing materialized endpoints.
   Descriptor-only endpoints must be reported separately.
3. Freeze reduced-word retention/reduction policy, equality/context handling
   and serialization policy. Charge construction, reductions, admission,
   conversion, observation and cleanup at their actual frequencies. Do not
   hide borrowed root-image/matrix state or move case work into observer work.
4. Distinguish short observer previews from full workload/performance evidence.
   Freeze a common reviewed work/storage profile and explicit refusal behavior
   before any later campaign. No existing ceiling is ratified for this new domain.

Existing evidence: four L8 previews produce25 checked observations and matching
private/serial inverse-pair traces. That verifies the exercised semantics only.
The full384 configurations have NOT RUN; complete multi-representation accounting,
reduced-word retention policy and crossover measurements remain PENDING.

## Recorded kernel stage decomposition — unchanged schedule

Source: `build/e8_root_images_20261013/workload_preparation_02/left_kernel.json`.

| Recorded stage | Charged primitives | Included work |
|---|---:|---|
| admission | 10,554 | Initial object/frame allocation, first Gram admission and token checks |
| left_update | 82 | Output/loop allocation,24 indexed reads,8 writes, result checks and loop controls |
| post_admission | 10,545 | Second Gram admission, input release and frame cleanup |
| Total | 21,181 | The original complete short-kernel schedule |

No materialization, table construction, wire decoding, inverse or reduced-word
cost was recorded by this kernel; report those dimensions NOT MEASURED, not zero.
The82-unit stage is not an end-to-end validated internal instruction or hardware
cycle count. Removing the surrounding admissions is a separate proposal, not a
demonstrated optimization. Preserve all original stage labels and charge events.
Independent emitted-event replay PASS verifies the recorded scalar/count/storage
observations; it does not establish absence of consistently omitted work/lifetimes.

## Independent verdict and stop conditions

The reviewer must record identity, affiliation/tool role, date, independence
from the preparer, exact source/context/fixture/evidence hashes, findings,
corrections and one verdict per A/B/C boundary. Permitted verdicts: PASS,
FAIL, PENDING. A boundary is PASS only when every required item is supported
or an explicitly reviewed scope amendment defines the narrower accepted claim.
Partial mathematical approval cannot close complete accounting or qualification.

Global review closes only with independent PASS for all three boundaries and
the proof/operator obligations. A defect halts work at the affected gate; preserve
evidence and propose a concrete correction without editing frozen artifacts.
Assignment/signature and all independent boundary verdicts are currently PENDING.
Record no preparer signature in the independent-reviewer field.

Current disposition: preparation PASS; independent review PENDING; complete
accounting HOLD; qualification HOLD. No384-configuration campaign, new allocation,
native ISA experiment or FPGA work is authorized. Surd CPU physical/backend
qualification remains the hardware priority.
