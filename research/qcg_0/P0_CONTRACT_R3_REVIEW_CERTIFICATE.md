# QCG-0 P0 contract Revision 3.1 independent read-only review

Date: 2026-10-23. Reviewer: `/root/qcg0_fixture_reviewer`, independent of the author and HEX-SOM acceptance context. **Current disposition: REVISE.** This verdict follows inspection of Revision 3.1 itself; it does not reuse Revision 2's verdict as the current assessment. No mathematical calculation, fixture generation, stage generation, implementation, freeze or execution was authorized or performed. The proposed future stage allowance remains a request and has not been granted or consumed.

## Identity and scope

Verified the five supplied SHA-256 identities before review:

- Contract: `2829a167eabb3bcc16a5beed35249ce91f5097de0f7934647e0f7676b474ee44`.
- Revision 3.1 diff: `48bccfadb9f980cbc48e6d9b3eb71ce20a951ec77c6fab517c3b01e6017bc75a`.
- Decision record: `67bd7fe09ad806b79c214e231b89bac314b81eddc3d2d1e0ca4aef461ea83995`.
- Review request: `65feb1de3bdcbda24a488903dfdc53bf4cc91844dcb01dff0b5670f0b01e4f1e`.
- Stage-allowance request: `4774432fd745fcc6142a92f496daa122e8f80c63c79316de5053e29ef3980723`.

Read the whole current contract, §10 checklist, request, decision record, proposed allowance and Revision 3.1 diff. Recomputed the referenced prior review/reference identities and unchanged pre-registration; all match. The R2 numerical results are treated as pinned existing evidence, not recalculated. Author scratch seen: no. Only hash/text metadata checks and these new exclusive review artifacts were used. All input documents and prior artifacts remain unchanged.

## Current section 10 checklist

| Item | Verdict | Evidence |
|---|---|---|
| 1. Administrative K and liveness | PASS | §2 explicitly excludes administrative zero-divisor/parity/bound/import/degree checks from K and counts named semantic tests. Preparation K=0 is consistent with the existing accepted count convention. L_peak now uses creation-to-last-read and assignment lifetime rules; it remains informational and cannot imply total memory superiority. |
| 2. Event grammar and sequential programs | REVISE | Whole-call counters including nested primitives, generic procedure/polynomial names, P16–P31 and expanded-arm k1–k8 close the earlier named-composite gaps. Position-only S1 selection and independent tape snapshots are now explicit. However C2's selected c6 still reads absent jS/jU/jV in S1/S2, and FDINIT's difference-table traversal is not frozen. These are actionable program conflicts before stage derivation; see B1/B2. |
| 3. Unequal lengths and zero polynomial | PASS | PADD/PSUB now count one A only where both operands exist, copy unmatched coefficients with the appropriate free negation, and explicitly represent zero as [0], degree 0. PDER of degree 0 and HORNER of a constant have explicit no-operation behavior. No new arithmetic evaluation was needed. |
| 4. P-1 adoption | PASS | §4 adopts the actual four-representation/dyadic and nonconstant-h random references, separate direction/tangent/status semantics, reversal's nonzero initial position, representation-signed versus base-oriented fields and accumulated length. The t=0 h-composition mutant's vacuity is explicitly stated. No reference is regenerated or changed. |
| 5. Mutant particulars/Cell A stages | PASS | X-12 now checks exact grid and output values, X-21 names the coefficient perturbation, and X-23 specifies the rational and primitive-retiming controls. The six printed Cell A W31 first-event strings and their stated evidence limits match the unchanged R2 certificates/JSON. This pass generates no new stage results. |
| 6. Launcher/evidence | REVISE | Reserved exit124 and forbidden runner SIGTERM handling remove the old elapsed-time heuristic within the trusted-runner model. Checksum-only pins and separate tool-version comparisons, explicit marker counting and caps are substantial corrections. Per-file cap attribution and final-output/post-check handling still do not implement all promises; see B3/B4. |
| 7. Inherited checklist obligations | PASS for preserved numerical/accounting definitions; REVISE for remaining programs/protocol | Corrected W proxy, typed aggregation, accepted comparator eligibility/ASCII tie-break, status grammar, reference mappings, existing hand/preparation counts, jet/class distinctions and fourteen conformance rows remain consistent with prior evidence. No calculation was repeated. Complete executable procedures and fail-closed evidence remain blocked only as detailed here, rather than assumed true from historical review results. |
| 8. Preservation and decisions | PASS | Decision record and current §11 faithfully record owner ACCEPT for D-1…D-6 with the prior qualifications. No scope broadening, certified-value change or implicit implementation/launch authority is introduced. Acceptance is expressly separate from authorization. |

The inherited ten-item checklist is therefore not being silently skipped: its ledger/category, aggregation, comparator, reference-preservation, degree/class and claim-boundary portions retain PASS; its complete procedure/refusal and launcher portions remain REVISE. The existing row counts and numerical expectations are accepted only through their unchanged pinned review evidence.

## Blocking findings and minimal corrections

### B1. C2's selected read step references values forbidden by its tape

The required-step table says all unselected steps are not executed. C2 S1 selects c3,c4,c6, so only jX and jY are constructed; c6's written read list nevertheless reads jS, jU and jV. C2 S2 selects c3–c6,c12–c14, so jU/jV are still absent but read by c6. Calling c6 free does not make these variables exist. The evolution sentence also says the retained jets are shifted each step without explicitly limiting that to selected jets.

Minimal correction: define tape-specific c6 projections and selected evolution. S1 reads only x=jX0,y=jY0 and shifts only X,Y. S2 reads x,x′,y,y′ from jX/jY and sigma=jS1, and shifts only X,Y,SS. S3 uses the full c6 read list and all needed jets. Alternatively split c6 into individually selected read steps. State explicitly that excluded jets are not shifted or read. This is a source-level correction to be reviewed, not an implementation choice or permission to execute extra hidden work.

### B2. FDINIT still does not freeze its triangular-table event order

FDINIT names sample/Horner generation but ends with “then the triangular table”; it gives a count, not the update traversal. The general “indices ascending” rule does not identify the table's loop nesting or assign t0. Different valid difference-table constructions can produce the same table/count with different intermediate order and first W31 event k. Unique stage derivation cannot choose one silently.

A minimal proposed specification is: set t0=0; generate p0…pd in the existing k order; copy v=p; set Delta0=v0; for r=1…d, for j=0…d−r in ascending order set v_j=v_{j+1}−v_j (one A), then copy Delta_r=v0. All these A events continue the same `FDINIT.<poly>` operation counter after point-generation and HORNER events. Copies carry no arithmetic count. This is a proposed textual correction, not a newly adopted procedure or computed table. The author can select a different exact traversal, but it must be explicit and reviewed before the allowance is requested again.

For the future stage JSON, retain outer identifiers for profile, curve, tape (S1/S2/S3), arm and request/sample. Reused event strings are unambiguous only inside that declared route context; the request's per-arm/per-curve/per-tape deliverable is an appropriate basis. No global uniqueness across unrelated routes should be inferred from qNN alone.

### B3. Per-file cap enforcement does not imply the promised OUTPUT_CAP evidence

RLIMIT_FSIZE can prevent a write and produce a file-size signal or EFBIG exception even while the directory total is below 10 MiB. The printed launcher writes OUTPUT_CAP only when its total `du` check exceeds 10 MiB. A per-file-limit failure can therefore produce FAILED without the promised cap-cause file. If the runner handles a failed write and later reports success, RC0 plus RUNNER_DONE can even choose COMPLETE unless the runner's cap-breach state is mandatory and independently recorded.

Minimal correction: specify how per-file-limit exceptions/signals are recorded as cap failures and how they reach the marker owner; any attempted cap violation must preclude COMPLETE. Define the required runner cap-state/diagnostic contract or an external attribution mechanism. Do not pretend that total directory size alone detects a per-file breach. No signal experiment or runner implementation was performed in this review.

### B4. Final evidence writes sit outside the cap check and the guaranteed post-check path

The cap check precedes writing the marker and `pins_after.txt`; the shell is outside the runner's RLIMIT_FSIZE and running total. Thus the printed program does not enforce the declared aggregate cap over final provenance/pin-check evidence. Also, with set-e, an earlier evidence-write failure (for example writing exit.code or the chosen marker) can stop the script before the advertised “post-run pin check is always attempted”. The prose's failure reporting intention does not create that control flow.

Minimal correction: give final metadata a bounded reserved budget, or move its bounded generation before the final cap/marker decision; define a single finalization path that always attempts the post-run pin check and records inability to persist evidence. Exactly one terminal marker must be owned by that path. A launcher unable to persist completion evidence must not infer success. This is a narrow finalization-contract correction, not a request to implement a supervisor during review.

## Matters now resolved, not reopened

**Deadline attestation:** the new protocol no longer infers a deadline from elapsed time or treats 137 as TIMEOUT. Given the explicit trusted-runner requirements that it never returns reserved124 and leaves SIGTERM with its terminating default behavior, GNU timeout's returned124 is an adequate owner of the deadline outcome for this model; other nonzero statuses remain FAILED. The implementation gate must enforce those requirements, including no ignored/blocked SIGTERM disposition. This review does not demand arbitrary hostile-runner protection or reinstate the rejected elapsed-time heuristic. No new timeout experiment is authorized.

**Pin/version manifests:** the later explicit checksum-only PINS and separate TOOLS string format resolve the former mixed-format defect. The earlier layout paragraph still saying PINS contains “tool paths and versions” is stale exposition; remove it to match the precise format, but it is not a separate algorithmic blocker. Actual manifests do not yet exist and cannot be certified by prose; their complete identities and out-of-band hashes remain future freeze prerequisites.

**Historical status text:** X-18's “needs P-1” wording is stale because §4 adopts the existing supplemental rows. The specific adopted references and current §11 discharge the prerequisite. Revision 3.1's changes in the supplied diff are policy/status wording, not a new mathematical fixture. These editorial points do not justify fixture regeneration.

## Owner dispositions: faithfully recorded and bounded

D-1 accepts C1/B-PH and C1/PHFD equivalence only as conformance controls, not C1-specific advantage. D-2 excludes FD from random-access comparators while retaining mandatory sequential comparison. D-3 accepts an abstract syntactic ledger and explicit administrative/semantic distinction, not CPU or hardware cost. D-4 accepts deterministic lexicographic selection and secondary comparisons without claiming a universal componentwise best. D-5 concerns retained-state storage only, with scratch/liveness reported separately. D-6 defers joint-versus-standalone sharing and makes no P0 sharing-efficiency claim. The decision record and §11 agree with these qualifications. These choices are **accepted owner policies now**, unlike the previous draft; no additional policy acceptance is being requested by this certificate.

## Proposed future stage allowance: recommendation, not authorization

The scope is appropriate for an independent exact-rational first-refusal trace of the amended sequential and Cell B programs, stopping at each route's first refusal; no Cell A recomputation, candidates, benchmark, or P0 execution. The proposed upper ceilings—at most three invocations, 30 seconds each, 1 GiB address space, cumulative external ceiling90 seconds, per-file limit4 MiB, cumulative new outputs10 MiB, internal4096/16384-bit ceilings, no children/network/devices/installs, inspected scripts and full evidence—are reasonable **maximum ceilings to submit to the owner after B1/B2 are corrected and reviewed**. They are not an estimate proving completion and must not be extended automatically.

Before any future authorization, pin the amended contract/programs and exact request schema; reconcile the request's informal preparation-count estimate with its per-arm/per-curve scope; specify external termination/exit recording and bounded output finalization; and record the reviewer-confirmed command and frozen ceilings in the new authorization. Every launched calculation consumes a slot, including failure/timeout/unavailable outcomes; stop at exhaustion. The exhausted R2 allowance cannot be reused. This certificate neither grants that new allowance nor spends any slot.

Only a current independent PASS on the amended text, the separately authorized remaining stage derivation, complete pins/manifests and later owner freeze/implementation/execution gates can change readiness. This review ends with REVISE on B1–B4. All existing numerical certificates retain their original scope; no other campaign, simulator, RTL or hardware was touched.
