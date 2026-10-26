# Parallel preparation alongside Surd CPU repairs

Date: 2026-10-14. Offline verification and isolated AOR-S1 software qualification COMPLETE.

```bash
cat docs/PARALLEL_TRANCHES_2026-10-14.md
cat spu_strategy/AOR_S1_REVIEW_PACKET_2026-10-14.md
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/PARALLEL_TRANCHES_2026-10-14.md spu_strategy/AOR_S1_REVIEW_PACKET_2026-10-14.md
```

The owner requested that parallel work begin. This increment covers provenance,
the existing offline T1d user path and AOR-S1 specification review. It does not
allocate another CPU placement attempt or change frozen research limits.

## Evidence and status reconciliation

| Item | Retained evidence / current boundary | Next deliverable |
|---|---|---|
| CPU backend compatibility | `build/spu_surd_register/backend_compatibility_20261012/cpu_placement_campaign_01` through `_04`: TIMEOUT, TIMEOUT, FAILED, TIMEOUT, respectively; each has one terminal marker. | Keep consumed attempts visible; integrated routing and timing remain separate acceptance gates. |
| Local LUT legality | `build/spu_surd_register/backend_compatibility_20261012/local_lut_legality_campaign_02`: COMPLETE, exit 0. | Review original carry-cluster constraints and interactions; this result alone does not qualify the integrated CPU. |
| Product placement repair | `build/spu_surd_register/product_placement_repair_20261011/routing_01` through `_04`: TIMEOUT, FAILED, FAILED, FAILED. | Preserve these results and their original limits. |
| Placer crash repair | `build/spu_surd_register/placer_crash_repair_20261012/routing_01`: FAILED. | Preserve failure; this increment does not reopen its campaign. |
| T1d offline evaluator | S1/S2/S3 sources and focused tests already exist; [walkthrough](gpu_scene_preview.md) provides preview, edit and inspect commands. | Retain a fresh source-bound walkthrough bundle and scoped test logs. |
| T1G recovery image | Retained image and physical scope are identified in [artifact plan](REPOSITORY_SETUP_AND_ARTIFACT_PLAN_2026-10-08.md) and [ledger §3.37](hardware_evidence.md). | Recheck bytes and record missing source/tool provenance explicitly before a release package. |
| T1H diagnostic image | Retained diagnostic image; H1 remains HOLD. [Ledger §3.38](hardware_evidence.md). | Keep diagnostic replay separate from a qualified release default. |
| AOR | S1 amendment ratified and isolated implementation authorized with three contracted attempts. | Software qualification COMPLETE; Padé build COMPLETE, timing qualification pending; three slots consumed. |
| E8 | [Validated-state prototype](E8_VALIDATED_STATE_PREPARATION_2026-10-13.md) exists; setup remains unmetered and independent sign-off pending. | Retain as alternate research lane; do not duplicate completed preparation. |
| SGN Phase B | [Owner decision](SGN1_PHASE_A_OWNER_DECISION_RECORD_2026-10-13.md) explicitly defers entry until CPU backend/routing/25 MHz qualification and closeout. | Preserve dependency. |

This is a selected evidence inventory, not a complete audit of CPU campaigns or
remaining authorization. Attempt directories count as consumed whether they
passed, failed or timed out. A successful fixture/local result is not a routed
CPU result. Historical manifests and contract status headers remain unchanged.

## Offline T1d verification bundle

Preparation lives under `build/parallel_tranches_20261014/preparation_01/`.
It retains selected source snapshots, SHA256 identities, Git status, repair-result
identities and the two retained programming-image hashes. Missing files and
unavailable image provenance are explicit inventory fields.

The exact verification entry point is:

```bash
tools/run_detached_job.sh --output build/parallel_tranches_20261014/verification_01 --timeout 1800 --notify-desktop -- python3 build/parallel_tranches_20261014/preparation_01/verify.py
```

One verification launch, no automatic retry. The 1800-second guard is an
operational limit for existing offline tests and commands, not an arithmetic
resource ceiling or FPGA campaign budget. After LAUNCHED, end the agent turn;
interpret only exactly one COMPLETE, FAILED or TIMEOUT marker on a later invocation.

The entry point runs the focused S1, S2 and S3 tests; renders baseline and edited
ideal/device previews; inspects the documented tie and vertex-edit witnesses;
checks 64-byte packets, expected winners and software evidence markers; and
runs the documentation audit and scoped whitespace gate. It saves every command,
exit code and stdout/stderr, with an aggregate `checks.json`. Failed checks remain
visible even when later independent checks run. Source hashes are compared before
and after execution to detect checkout changes during validation.

The retained [runner result](../build/parallel_tranches_20261014/verification_01/result.json)
has exactly one COMPLETE marker, exit 0, and a 42-second duration. The
[check records](../build/parallel_tranches_20261014/preparation_01/checks.json)
record successful S1/S2/S3 tests, four previews and six pixel inspections,
documentation audit execution, scoped whitespace execution and unchanged
source hashes during the run. The copied preparation sources remain the original
tested versions; this subsequent status update is not part of those snapshots.

Baseline full-frame RGB agrees between ideal and device models at all 307,200
pixels. The edited full frame has three RGB differences (307,197 matching
pixels), localized at `(321,35)`, `(322,71)` and `(323,109)`. Exact rational
depth selects triangle 1; equal truncated model depths select triangle 0 under
the declared tie rule. The separate [diagnosis](../build/parallel_tranches_20261014/pixel_diagnosis_01/explanation.json)
records exact gaps of 905/1932, 1205/1932 and 295/1932, respectively, tied model
depths 1982, 1964 and 1945, and unchanged preview source hashes. Successful
walkthrough execution does not establish edited full-frame equality.
At the documented edited witnesses, `(100,200)` changes from red to
background and `(300,200)` changes from red to green in both models. This is
software-model evidence; S2's scoped RTL checks do not establish full-top or
physical equivalence.

The audit exited 0 while reporting 14 broken internal links, 30 uncited silicon
claim findings, one stale suite-total finding, 115 orphaned documents and one
superseded-status finding. These are regex findings requiring judgement, not
individually confirmed defects. Its tracked-file scan does not cover the two
new untracked preparation documents. No clean repository-wide documentation
result or new regression-suite total follows from exit 0; 238 is the prescribed
audit argument.

## Next preparation increment

1. Pixel diagnosis is complete for the three retained differences. Preserve
   the original images/manifests and use the added walkthrough commands to
   explain this profile's finite-depth tie behavior.
2. AOR-S1 specification review, ratification and the separately authorized
   isolated implementation campaign are complete. The
   [independent review disposition](../spu_strategy/AOR_S1_INDEPENDENT_REVIEW_DISPOSITION_2026-10-14.md)
   retains the review of the original 83 operations, five kernels, 11 comparators
   and 13 alias maps. The
   [implementation contract](../spu_strategy/contract_aor_s1_isolated_implementation_2026-10-14.md)
   added eight operation witnesses and 26 executable mutation controls, preserving
   the original reviewed case identities. Software qualification passed all
   91 operation, five kernel, 11 comparator and 13 alias witnesses and all
   26 controls. The repository stage passed 244 tests with zero failures and
   the separate trace/math gates. The existing Artix-7 Padé regression build
   completed in 509 seconds, with post-route clk_fast 34.80 MHz as a tool-reported estimate; 25 MHz timing qualification remains pending timing-model review.
   All 27 frozen software/configuration and 306 hardware/build source identities
   agree at closeout. The
   [closeout review](../build/aor_s1/implementation_qualification_20261014/closeout_reconciliation_01/REVIEW.md)
   records incomplete timing coverage: missing DSP entries, stub delay concerns
   and delay/corner provenance require review of the exact backend/database.
   This is isolated finite software qualification and a completed Padé build;
   it grants no AOR RTL, silicon, performance or resource claim. Checked 1*a
   remains a logical accounting convention. All three allocated slots are
   consumed; actual recorded runtime totals 1,455 seconds within the allocated
   12,600-second ceiling. The
   [live campaign ledger](../build/aor_s1/implementation_qualification_20261014/campaign_ledger.json)
   and [acceptance record](../build/aor_s1/implementation_qualification_20261014/closeout_reconciliation_01/acceptance.json)
   retain the completed status. Prior HOLD and pending-stage records describe
   historical gates and remain unchanged. The latest integrated-context CPU candidate has placement PASS for 51,197
   cells; routing/timing is blocked by incomplete timing coverage. The earlier
   1,800-second baseline timeout remains a historical result. See the
   [CPU closeout](../build/spu_surd_register/backend_compatibility_20261012/integrated_context_closeout_01/REVIEW.md).
3. Complete selected GPU release provenance: identify source/tool/constraint
   snapshots for the retained images or mark each unavailable field. Image-byte
   hashes already match the artifact plan; that alone does not reconstruct a build.
   The [local catalogue review](GPU_RETAINED_ARTIFACT_PROVENANCE_2026-10-14.md)
   now identifies T1G's clean recorded commit and selected XDC, while preserving
   T1H's dirty-source gap. Executed PNR binary, chipdb and packing-dependency
   identities remain unresolved; no rebuild/release acceptance is claimed.
4. Triage current user-path documentation findings before historical archive
   findings. Each proposed fix must retain original evidence boundaries.

No verification rerun or renewed CPU attempt is needed for the unchanged GPU
sources. The isolated AOR-S1 campaign is closed. SGN Phase B remains deferred.

The [follow-up check records](../build/parallel_tranches_20261014/followup_checks_01/checks.json)
retain successful S1/S2/S3 reruns and the three newly documented inspection
commands. The AOR JSON received format, ID uniqueness and count-sum checks only;
these checks do not validate its arithmetic against a candidate. Existing
documentation audit findings remain separate from these scoped successes.

A later [short AOR review](../build/parallel_tranches_20261014/aor_literal_review_01/review_result.json)
adds bounded exact value witnesses, rational-isolation comparator witnesses and
alias-map consistency. It preserves the distinction between mathematical review
and unexecuted candidate/refusal/work/mutation checks. The updated GPU catalogue
and fixture proposals received documentation/JSON validation separately; existing
GPU software sources were unchanged, so no repeated GPU regression was needed.

## Review and promotion boundaries

The current engineering checkout is dirty. A fresh output bundle identifies the
tested sources; it is not a clean default-branch release or independently reviewed
package. Publication and package download/restoration acceptance remain pending.
CPU repair, GPU physical acceptance and AOR software qualification retain their
own contracts. The initial offline increment changed documentation and wrote ignored evidence.
The subsequent authorized AOR-S1 campaign added isolated software and ran the
existing Padé FPGA regression build. It performed no board programming or
transport operation. Publication packaging remains separate from this closeout.

The [publication evidence package](PUBLICATION_EVIDENCE_PACKAGE_2026-10-14.md)
provides the reconciled claim table, portable selected evidence and publication text.
