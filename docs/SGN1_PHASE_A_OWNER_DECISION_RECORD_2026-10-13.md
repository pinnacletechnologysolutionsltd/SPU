# SGN-1 Phase A owner decision record and Phase B dependency

```bash
python3 -m json.tool build/sgn1/phase_a_closeout_20261013/archive_01/evidence_manifest.json > /dev/null
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/SGN1_PHASE_A_OWNER_DECISION_RECORD_2026-10-13.md docs/SGN1_PHASE_A_CLOSEOUT_REVIEW_2026-10-13.md docs/README.md
```

Date: 2026-10-13. Status: CLOSEOUT RECOMMENDED; explicit owner closeout pending.
Owner supports closeout subject to original-condition review and directs that
SGN-1 Phase B be deferred until Surd CPU FPGA backend qualification.
No further SGN campaign or hardware work is launched by this record.

## Original acceptance evidence, without substitution

The [closeout review](SGN1_PHASE_A_CLOSEOUT_REVIEW_2026-10-13.md) maps the seven
positive gates to original geometry, symmetry, routing, FCC scheduler and
mesh/cost evidence. The [bounded review result](../build/sgn1/phase_a_closeout_20261013/review_01/review_result.json)
checks source identities, durable COMPLETE results and all six mesh/cost streams.

The original [FCC qualification contract](../spu_strategy/contract_sgn1_scheduler_qualification_2026-10-13.md)
required sixteen specified named first counterexamples. The original scheduler
artifact retains these under each of its three seeds. The supplemental audit
does not supply or replace those mandatory original records.

The frozen [mesh preparation contract](../spu_strategy/contract_sgn1_mesh_measurement_preparation_2026-10-13.md)
requires the prepared preflight controls and exact comparison checks. The original
campaign ran seven preflight tests successfully under each seed, including the
eleven checker mutations and wire/storage controls, before its comparisons.
Its qualification records 23,838 mesh executions, 23,838 retained FCC rechecks,
matching application outcomes and six equal mesh/cost hashes, followed by the
required repository, trace and math gates. No original failing or absent
qualification run is replaced by a later diagnostic run.

The post-qualification audit records names and first counterexamples for eleven
mesh checker mutations of retained traces. This supplements diagnostic retention;
the mesh contract did not require a per-mutation diagnostic artifact as the FCC
contract did. Keep its later provenance visible. It establishes neither a new
positive execution count nor independent human acceptance of the checker.

## Conclusions to preserve in an owner closeout

1. Deterministic software behavior is qualified on the declared graphs,
   workloads, seeds and node orders. This does not establish arbitrary-domain
   scheduling independence or cross-device reproducibility.
2. The comparison establishes workload-specific tradeoffs. FCC uses fewer
   isolated-pair transmissions; mesh drains crossing and wavefront sooner.
   There is no universal topology winner or equal-total-link-budget result.
3. Hardware efficiency and finite-buffer behavior remain unqualified.
   No LUT, routing congestion, wire length, power, timing or board performance
   claim follows from these software results.

Keep the frozen inputs and qualification artifacts in place. A SHA256 inventory
under `build/sgn1/phase_a_closeout_20261013/archive_01/` identifies the retained
evidence, source snapshots, live software and decision documents. It is an
in-place archive inventory, not a separate/off-site backup. Do not rewrite
historical manifests or turn later review results into original campaign logs.

## Owner-directed Phase B deferral

Phase B remains DEFERRED / UNLAUNCHED. Resume consideration only after:

| Order | CPU implementation-path gate | Required evidence |
|---|---|---|
| 1 | FPGA backend repair | Validate legality of the original carry cluster, including its constraints and interactions; isolated LUT-pair legality is insufficient |
| 2 | Integrated CPU placement and routing | Legal placement and completed routing of the integrated design using the repaired backend |
| 3 | Routed 25 MHz qualification | Reproducible routed result, named source/tool/device/constraints, utilization and complete required timing coverage at a 40 ns period |
| 4 | CPU qualification closeout | Review durable results, limitations and remaining unqualified dimensions |
| 5 | SGN Phase B proposal | Freeze finite queues/backpressure and resource/cost models; consider small RTL only after justified software/model evidence |

Successful synthesis alone does not clear any outstanding placement/routing/
timing gate. Exit zero alone is not timing acceptance. This dependency requires
a reliable FPGA implementation path; it does not add a fully operational CPU,
GPU demonstration or board-functional requirement to this Phase B entry rule.
Keep those separate hardware claims under their own evidence contracts.

Existing [carry-repair](../spu_strategy/contract_surd_placer_carry_repair_2026-10-11.md)
and [placement-review](../spu_strategy/contract_surd_product_placement_review_2026-10-11.md)
documents provide prior scope and evidence boundaries. Their current campaign
state is not audited or changed by this SGN decision record. No CPU attempt,
repair method or new runtime budget is authorized here.

AOR and D4/E8 may retain their separately scoped mathematical/software activity;
this record allocates no FPGA resources to either. Surd CPU backend legality,
integrated routing and timing qualification remain the primary hardware work.
