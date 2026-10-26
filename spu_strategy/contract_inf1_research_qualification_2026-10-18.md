# Engineering contract: INF-1 research qualification infrastructure

## INF-1R proposed narrow amendment — 2026-10-19

**R_HOLD.** This reviewable amendment does not adopt standing execution
authority. The owner must accept this exception and an enforcing execution
path before R becomes available. The deferred INF-1A–D toolkit, its dependency
gates and every existing Q/H authorization remain unchanged.

Preparation check (does not execute research):
`python3 -B tools/doc_audit.py --actual-pass 238`

After that acceptance, an individual locally supervised Class R operation
needs only an experiment script, assertions/tests and a short
[FINDINGS.md](../docs/INF1R_FINDINGS_TEMPLATE.md). It needs no per-experiment
campaign packet or INF-1 provenance toolkit. Classify the operation, not the
project. R findings are preliminary CONFIRMED/FALSIFIED/INCONCLUSIVE results;
qualified claims require a frozen-input Q rerun under existing rules.

The standing envelope is 60 seconds wall time, at most two concurrent logical
CPUs and 120 CPU-seconds across the entire process tree, 1 GiB enforced memory
(report address-space or cgroup method), and 100 MiB aggregate scratch output.
An address-space limit alone cannot bound a multiplying process tree; either
enforce the tree's memory ceiling or prohibit subprocess creation.
Only a fresh experiment-owned scratch subtree is writable. Reads expose only
declared non-sensitive source/fixture inputs and necessary runtime files; no
network, hardware devices, privileges, detached/escaping descendants, package
operations, shared-state writes or repository mutation. Controller outputs and
temporary files count toward the output cap. Descendants inherit enforcement;
the controller must terminate and reap them before returning. No retry after
timeout, splitting or looping to evade limits. Failure to establish any control
means R_HOLD, without falling back to weaker execution.

ISA/RTL/constraints/source changes, preservation/Q/H evidence writes, hardware,
network, excess resources or qualified acceptance claims stop R and require
existing explicit Q/H authority. Authoring scripts and findings uses normal
explicit edit authority outside the isolated runtime; R itself cannot publish
into the repository. Successful R work ordinarily retains script + tests +
findings only; scratch is disposable, subject to existing retention review and
separate cleanup approval. Q promotion deliberately freezes necessary evidence.

Implementation inspection: tools/run_detached_job.sh and its worker provide
execution records and a timeout, not the required filesystem/network/device
sandbox or aggregate CPU/memory/output ceilings. RET-1 restored-only path
checks likewise make no OS isolation claim. /usr/bin/bwrap and unshare exist,
but installation is not tested enforcement. No existing qualified R execution
path was established by this bounded review; no isolation tests or experiments
ran. No wrapper is added that would suggest otherwise.

Smallest remediation: separately accept this policy exception and validate one
existing sandbox/resource-control composition, including short positive and
negative wall/tree-cleanup, CPU, memory, aggregate-output, undeclared-read,
write, network and device controls. A timeout, per-file limit or manifest alone
is insufficient. Reuse installed mechanisms; do not build an orchestrator.
Until then use existing separately authorized procedures. No Q/H, FPGA or
preservation controls are relaxed, and no research experiment is authorized here.

Date: 2026-10-18. Status: CONTRACT DESIGN ACCEPTED FOR FUTURE PLANNING — IMPLEMENTATION DEFERRED.
Roles: spec author prepares this contract; later owner-assigned implementer
halts on defects; independent auditor checks each bounded stage after approval.

## 1. Review the named references; do not start implementation

Targeted read-only reference commands:

```bash
sed -n '1,190p' spu_strategy/contract_ssm4_m2_dependency_boundary_2026-10-18.md
sed -n '1,130p' research/ssm3_baseline_20261018/README.md
sed -n '1,100p' research/sg0_baseline_20261018/README.md
sed -n '1,170p' ../spu-sim/docs/SIM_G2A_QUALIFICATION_2026-10-18.md
sed -n '1,110p' docs/SIM_G3_QUALIFICATION_2026-10-18.md
sed -n '1,150p' spu_strategy/contract_sim_g3_r1_manifest_staging_2026-10-18.md
sed -n '1,145p' docs/RET1_RESTORATION_REVIEW_2026-10-18.md
sed -n '1,100p' docs/ret3_review/README.md
```

Controlling design:
[INF-1 architecture](../docs/INF1_RESEARCH_QUALIFICATION_ARCHITECTURE_2026-10-18.md).
No command below authorizes edits, migration, scans, archives or replay now.

## 2. Current scope and prohibited actions

This tranche may add only these two design documents. Read named reference
documents, metadata and existing tool sources. Do not run dependency discovery
across the repository, import experiments, execute replay, create archives,
alter historical manifests, install dependencies or launch any campaign.

No changes to SSM-4-M2, SSM/SG-0/SIM implementations, RET policy/tools/review packet,
qualification commands, GPU/CPU/FPGA flows or external simulator checkout.
No new executable framework, generic CI system, database, daemon, scheduler,
workflow DAG, cloud service, archival destination, pruning or publication.

## 3. Reference identities and readiness gate

Use the existing M2 metadata as the primary reference: 148 research-domain files
and 2,188 execution-envelope files, including the original mixed 238-entry set.
Do not rescan those sources or promote the proposal to a frozen manifest here.
Research proposal SHA-256:
`e1783dcc1dd1d8a1bec19c9fb97e75abe8642c325b0ba06439f95c786a846bab`.
Execution proposal SHA-256:
`50a26954c9552b920b0bebfa77265409079093f4897975d23e036479cd246d86`.

Reference states observed in this targeted review:

- SSM-3: original qualification plus scoped restored executable proof replay.
- SG-0: focused software qualification plus member/bundle restoration checks;
  that restoration did not rerun proof/render execution.
- SIM-G2A: bounded qualified dirty overlay/executable, with separate R1/R2 records.
- SIM-G3: passing packet/RGB evidence, failed original closeout; R1 harness repair
  prepared and focused-tested, with qualification not established by that draft.
- RET-1: reusable strict archive/tree/Git verification, within its recorded limits.
- RET-3: review-only 31-member closure; no replay, stopped writers or destinations
  confirmed; all seven retention artifacts remain PROTECT.

Do not begin INF-1 implementation until SSM-4 independently closes its M2 and
qualification, SIM-G3 independently closes its verifier repair/native rendering
demonstration, and the owner reviews their final evidence for extraction into
INF-1 fixtures. Their current execution authorizations are neither expanded nor
consumed here. CPU physical qualification remains independent, not an INF-1 gate.

## 4. Proposed smallest implementation boundary

After separate authorization, add only `tools/research_qualification/`, synthetic
fixtures at `fixtures/research_qualification_v1/`, scoped tests and documentation.
Cap production code at ten single-purpose modules, each at most 150 lines.
No third-party dependency or custom archive format. Reuse existing RET-1 APIs,
detached execution, experiment-owned verifiers and compiler dependency evidence.
Do not refactor existing experiments to use the new tools.

Required interfaces are offline candidate discovery, explicit snapshot identity
capture/check, evidence validation and summary generation. Experiment commands
remain ordinary argv lists launched by the existing detached runner under their
own contracts. INF-1 must not allocate retries or infer execution permission from
an experiment descriptor, output path or historical qualification.

Use additive versioned INF-1 schemas; no rewrite of old manifests. Preserve
logical root IDs, exact paths/modes/member sets, research/execution overlap,
conditional edges and unresolved dependencies. Canonical encoding, external
manifest pins, trust anchors, root-manifest staging and supported-link rules must
match the architecture. A changed schema needs review before emitting new data.

## 5. Independently qualified future stages and resource ceilings

Each stage requires its own exact implementation/test contract and owner budget
before edits. The figures below are proposed ceilings, not a pooled execution
allocation. Unused time/attempts cannot transfer to another stage.

| Stage | Permitted objective | Maximum test envelope | Exit acceptance |
|---|---|---|---|
| INF-1A | Canonical two-level identity and typed evidence records | One attempt, 180 seconds | Stable identities, strict validation, research/execution distinctions and negative controls pass on synthetic fixtures |
| INF-1B | Bounded Python/C++/RTL/shell discovery profiles and membership guards | One attempt, 300 seconds | Deterministic candidate sets with guards/unknowns; declared reference sets reproduced without importing or executing experiments |
| INF-1C | Snapshot/environment/drift checks and a narrowly qualified runtime-input observer adapter | One attempt, 240 seconds | Stopped-source boundary, copy/member checks, tool/config attestation and covered unexpected-read detection pass; unavailable observation stays NOT_VERIFIED |
| INF-1D | RET-1 adapter, replay receipts and offline reviewer/publication summaries | One attempt, 240 seconds | Synthetic package restore/replay and semantic summaries preserve every claim/failure and pass tamper controls |

Total proposed command time across all four independently approved stages is
at most 960 seconds. Per-subprocess limit: 60 seconds; stage-wide outer limit
is binding. Work expected over 60 seconds must use the current detached runner.
End the agent turn at LAUNCHED and interpret exactly one terminal marker later.
No automatic retry, timeout extension, alternative method or full repository gate.
These limits apply to the isolated new tools and fixtures only. If a stage needs
to alter shared verification infrastructure, stop for a new scope/gate/budget
review under AGENTS.md instead of substituting focused checks for required gates.
An unavailable observer leaves INF-1C partial and its runtime-input claim
NOT_VERIFIED; passing identity checks alone cannot close that entire stage.

For initial fixtures bound descriptors to 3 named roots, 4,096 entries, 256 MiB
of declared file bytes, 1,024 discovery edges, 8 directory levels and 16 MiB of
observer trace; reject limit exhaustion explicitly. Depth/edge limits are initial
profile ceilings, not claims that the complete live M2 graph fits. Review an
explicit increase or smaller conservative profile if it does not. No live
repository-wide scan, large historical replay or FPGA action is covered.

Future detached command shape, NOT runnable now because the stage scripts do
not exist and have not been reviewed:

```bash
tools/run_detached_job.sh --output build/inf1/stage_a_01 --timeout 180 --notify-desktop -- bash tools/research_qualification/check_stage_a.sh
tools/run_detached_job.sh --output build/inf1/stage_b_01 --timeout 300 --notify-desktop -- bash tools/research_qualification/check_stage_b.sh
tools/run_detached_job.sh --output build/inf1/stage_c_01 --timeout 240 --notify-desktop -- bash tools/research_qualification/check_stage_c.sh
tools/run_detached_job.sh --output build/inf1/stage_d_01 --timeout 240 --notify-desktop -- bash tools/research_qualification/check_stage_d.sh
```

Every stage script/source hash, fixture set, environment, expected result and
command must be frozen before its authorization. A stage pass qualifies only
that scope; the current SSM-4/SIM budgets cannot be reused for INF-1.

## 6. Mandatory negative controls

INF-1A: reordered input dictionaries; duplicate/unknown keys; path traversal,
cross-root collisions, altered modes, unsupported links/types, missing/extra
members, self-referential identity graphs, wrong external pin and same-size
substitution. Identical semantics produce canonical bytes; distinct meaningful
source/environment inputs cannot silently share an identity.

INF-1B: newly discovered/deleted test; changed helper or include/ROM; different
module/include search order; shell child hidden behind an environment guard;
optional tool appearing/disappearing; stale compiler depfile; dynamic import with
no bound; archive/library versus archive/test exclusion; generated-output recursion.
Every unresolved relevant edge must fail closure or be covered by a reviewed
superset. A static profile must never report an observed runtime execution.

INF-1C: source changes during copy; unconfirmed writer boundary; symlink escape;
tool substitution; SKIP_TESTS/TB_FILTER or module-path bypass; undeclared external
root; unexpected child-process file read; generated input reused without a pin;
incomplete/truncated observer trace. Stable double hashes alone must not establish
quiescence. Observer absence cannot produce runtime-input PASS.

INF-1D: omitted root manifest (SIM-G3 regression); altered payload with updated
untrusted manifest; malformed RET package; extra restore member; replay reaching
the original tree; missing interpreter/tool; source-mode normalization; a skipped
GPU path presented as tested; COMPLETE with a failed closeout; RGB equality
presented as depth equality; missing historical log hidden; same-disk copies
reported as independent recovery. Use RET-1 controls rather than duplicate its
extractor or claim its existing qualification automatically covers the adapter.

## 7. Evidence, acceptance and stop conditions

Each stage emits exact argv, time/exit records, input/code/tool identities,
claim-level JSON and matching Markdown. Keep semantic identities separate from
volatile runtime metadata. Validate summaries against the ledger and bind every
claim to a specific verifier/artifact/scope. Public output generation is offline;
no upload, git commit/tag/push or automatic release is included.

Source reconstruction, executable rebuild, deterministic replay, mathematical
correctness, restoration, independent-storage recovery and hardware observation
are separate claims. NOT_RUN/NOT_VERIFIED/SKIPPED/INCOMPLETE cannot become PASS
through aggregation. Preserve failures and amendment lineage verbatim. Historical
adapters may identify missing evidence, but cannot fabricate or retroactively
strengthen the original qualification.

Stop on any pin drift, unsupported dependency, resource breach, failed negative
control, original-tree mutation, contradictory status, missing evidence, unsafe
archive/source boundary or needed out-of-scope edit. Preserve partial outputs;
report the minimal correction instead of weakening the test or growing the scope.

Existing original archives and retention decisions remain protected. Synthetic
local RET-1 package tests in a future approved stage are not production archival
authorization. External destinations, copying valuable evidence, replay and
deletion remain governed by RET contracts and independent owner decisions.

## 8. Current completion criteria

Deliver the architecture and this contract with reference-case limitations,
reuse map, stages/budgets, falsifiers and acceptance gates. Check only these
documents' links/whitespace and scoped documentation hygiene. Do not invoke the
global documentation audit because this tranche prohibits repository-wide scans.
No new executable tool or qualification result is delivered.
Do not request implementation authorization now. Keep INF-1 as a future
consolidation tranche after the current independent work closes.

## 9. Owner review disposition

The owner accepts this contract design as the future planning baseline. All four
implementation stages remain unimplemented and unauthorized until SSM-4 and
SIM-G3 close independently and separate execution authorization is given. Their
closure does not automatically launch INF-1. CPU/backend qualification remains
separate, and INF-1 is not a prerequisite for a first SPU-R1 public release.

The owner reported receiving this contract twice rather than the separate
architecture document. Contract acceptance therefore does not establish an
independent owner review of every architectural detail. The architecture remains
available at `docs/INF1_RESEARCH_QUALIFICATION_ARCHITECTURE_2026-10-18.md`.
The future SPU-R1 consolidation audit is a separate planning task; no repository
audit, file migration, deletion or publication is authorized by this disposition.
