# QCG-0 P0 Revision 3.2 independent read-only review

Date: 2026-10-23. Reviewer: `/root/qcg0_fixture_reviewer`, independent of the author and HEX-SOM acceptance context. **Disposition: REVISE, one remaining finalization defect.** B1/B2 program corrections pass; B3 cap attribution passes under the stated runner contract. No mathematical calculation, reference/stage generation, launcher execution, implementation or freeze occurred. The future stage allowance remains ungranted and unused.

Verified before review: contract `94e6631a48f4f362c310e72954af66b2853d477fbff8674cf555ff9064e44602`, Revision 3.2 diff `68146db053460c1ac0e106e5872e3bc5d91502c40fb31b5752285e3373097e7e`, request `adfcd3a3f9c49c158d0f31dd5f01faa7c560a57ba95cf5616be2ab18306818b9`, updated stage request `5f9e99c8163b60e326d8c42e5c81731149e9afea0a9ac1935b27cabd8bf5f481`. Also checked unchanged decision-record, previous review, pre-registration and supplemental-reference/stage identities. Read the entire current contract, its diff and both requests. Author scratch seen: no. All author inputs and prior artifacts remain unchanged.

## Section 10 and B1–B4

| Item | Verdict | Evidence |
|---|---|---|
| 0 / B1 C2 | PASS | S1 selects c3,c4,c6a and reads only constructed X,Y jets. S2 selects X,Y,S with c6b. S3 retains the full projection. Evolution explicitly shifts only selected jets; excluded jets are neither shifted nor read. |
| 0 / B2 FDINIT | PASS | t0=0, ordered point generation, ascending r/j difference updates and Delta copies are explicit; all operations share the FDINIT call counter. FDSTEP uses ascending j and old neighbor values. Outer route context is required, so stage strings are not compared across profiles/curves/tapes. This is textual confirmation, not a derived stage table. |
| 0 / B3 cap attribution | PASS | Centralized checked writing, reserved status90, status153/CAP_BREACH handling and RUNNER_DONE-last/no-after-breach rules make a known cap breach choose FAILED and OUTPUT_CAP. This remains an implementation conformance obligation, not a tested runner. |
| 0 / B4 finalization | REVISE | No set-e, bounded metadata, reserved space and an always-attempted post-run pin check correct the earlier control-flow issues. But a required metadata-write failure can still leave exactly one COMPLETE marker; see the concrete path below. |
| 1 administrative K/liveness | PASS | Accepted semantic-versus-administrative accounting and stated lifetime rules are preserved. |
| 2 event programs | PASS for text consistency | Named/generic/nested event counters and the corrected sequential projections/FDINIT resolve the previously identified textual ambiguities. Remaining stage results still require separate owner-authorized derivation. |
| 3 unequal lengths/zero | PASS | Explicit shared-index arithmetic, unmatched copies and [0] zero conventions remain unchanged. |
| 4 P-1 mapping | PASS | Adopted literal supplemental fields/statuses and the nonconstant-h vacuous-point qualification are unchanged. |
| 5 mutants/existing Cell A events | PASS | Value/grid assertions and concrete perturbations remain; printed Cell A stages agree with previously certified evidence, without recomputation. |
| 6 launch/evidence | REVISE | Reserved124 deadline model and checksum/tool separation remain accepted. B4's false-completion path prevents overall launch PASS. |
| 7 inherited checklist | PASS for preserved definitions; REVISE only for finalization | Existing W/aggregation/comparator/status/reference/count/class definitions remain consistent; fourteen rows and the prior numerical evidence are not reopened. |
| 8 preservation/D-1…D-6 | PASS | Owner ACCEPT scopes are carried over faithfully; no new geometry, policy authority or implementation/execution GO is implied. |

## Single blocking path: COMPLETE survives failed required evidence

The printed launcher first chooses MARK=COMPLETE when RC=0 and RUNNER_DONE exists. It then sets W=1 if writing exit.code or pins_after.txt fails, but **still executes `: > "$LEAF/$MARK"`**. If the marker write succeeds, the evidence leaf now contains exactly one COMPLETE marker. Only afterwards does the launcher print FINALIZE_FAILED and exit 3.

This is a direct branch in the written program, not an executed failure test or a hypothetical new threat model. A shell exit 3/message does not invalidate a durable COMPLETE marker for later marker-based interpretation. It contradicts “completion is never inferred” after a required evidence failure and the repository rule that COMPLETE means exit 0.

Minimal correction: finish required metadata writes before allowing a success marker; if W is nonzero, select FAILED rather than COMPLETE (and record FINALIZE_FAILED durably where possible), then attempt the single terminal marker. Keep launcher exit3 for finalization failure and never leave COMPLETE in that branch. If even a failure marker cannot be persisted, the result is unavailable; do not demand impossible guarantees from an unwritable filesystem. No replacement launcher was implemented here.

## Reserve, syntax and nonblocking notes

The finalization files now have explicit bounded contents and the cap check reserves4 KiB before selecting a marker. That resolves the previously unbounded post-check text issue in the declared output-byte model; it is not a claim about allocated filesystem blocks. No additional cap-sizing experiment or numerical calculation was performed. The remaining objection concerns truthful terminal state, not a demand to redesign the reserve.

The displayed launcher was piped as text to `bash -n`; syntax check exited0. The launcher itself was **not executed**. Static syntax success does not establish correct failure semantics.

The stale mixed PINS-layout sentence and X-18 prerequisite wording are removed. The stage request's Purpose still mentions Revision3.1 while its schema/preconditions refer to Revision3.2; update that historical label and freeze the exact amended contract hash in any future authorization. It is an editorial mismatch, not authority to calculate under the older text.

The proposed maximum three 30-second invocations, 1 GiB each, 90-second cumulative external ceiling, 4 MiB per file and 10 MiB cumulative output bounds remain a reasonable bounded request for the now-specified sequential/Cell B stage derivation. This recommendation grants no allowance and consumes no slot. After the narrow finalization correction, seek the required current review/owner authorization before any calculations; do not reuse the exhausted R2 budget. D-1…D-6 remain accepted only in their recorded conformance/scope/abstract-ledger/ranking/retained-storage/deferral senses. Freeze, implementation and P0 remain HOLD.
