# AOR × FPRA P0 Revision 3 — independent static specification review

**PASS.** Reviewer: `/root/aor_fpra_r3_spec_review`.
Recorded by `/root` from the independent read-only review response, 2026-10-23.

Reviewed [Revision 3](PREPARATION.md), SHA-256:
`8af8572184b9921f6ed6a689ce7e44ed9635810d45d4b18d684919ffa56eaadb`.
Verified [preserved Revision 2](PREPARATION_REVIEWED_R2.md), SHA-256:
`19082a62fc22fa10763975b25d47544b420fda5940d792c46544cfd531f6cc5a`.
Compared the [Revision 2 findings](REVISION2_SPEC_REVIEW.md) and verified that
the [recorded diff](PREPARATION_REVISION_3.diff) exactly matches Revision 2 to 3.

All four findings are resolved:

1. **READ/COPY and scratch accounting — lines 201–258.** Retained loads,
   private copies, arithmetic results and ownership transfers are distinguished.
   Helper entry order, last-use releases, size-check failure cleanup, metadata,
   journal and receipt transfers are fixed. The same schedule applies whenever
   arms perform the same operation. General return/refusal cleanup and
   transaction lifetimes at lines 192–197 remain consistent. No contradictory
   release or unequal charging requirement was identified.
2. **SET atomicity and COMMIT — lines 136–145, 239–258.** Both SET operations
   preserve committed state on denial, including denial of final COMMIT.
   Successful no-ops charge one COMMIT without changing semantic state,
   snapshots or caches; staging and receipt rules are specified.
3. **Freshness visited sets — lines 101–105, 233–237.** Every STEP, SET_EQUAL
   and OBSERVE validation starts with a fresh empty set, released before
   subsequent work. Metadata rules preserve this lifetime.
4. **Controls 12–13 — lines 318–319.** Mathematical outputs and public receipts
   are shared requirements. Powering assertions apply to C/D; expanded STEP and
   current-pair cache expectations apply to A/B.

Additional READ/COPY events remain subject to reserve-before-event work denial
(lines 274–296), including staging/publication failures. Atomic rollback and
bounded administrative reporting are consistent with that precedence. Literal
first-refusal stages and operation totals remain deferred (lines 328–333).
This review does not certify those numerical fixtures or empirical feasibility.

No remaining specification contradiction was identified within the authorized
scope. Mathematics, four arms, event tape, cadences, controls and resource
ceilings are preserved.

**Recommendation:** Freeze the reviewed specification identity and proceed to
the independent literal/reference derivation gate only under separate bounded
authorization. Fixture derivation, candidate implementation and execution remain
HOLD. No numerical fixtures, candidate code, tests, experiments, campaigns, ISA
changes or hardware operations were performed. The reviewer modified no files.
QCG-0, X2, CPU/GPU hardware and closed research remain separate.
