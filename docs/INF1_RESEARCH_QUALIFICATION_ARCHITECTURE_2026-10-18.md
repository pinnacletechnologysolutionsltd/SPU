# INF-1: Reproducible Research and Qualification Framework

The [proposed INF-1R exception](../spu_strategy/contract_inf1_research_qualification_2026-10-18.md#inf-1r-proposed-narrow-amendment--2026-10-19)
separates disposable preliminary research from this deferred qualification
toolkit. R remains HOLD pending policy acceptance and enforcing isolation;
it does not change the Q/H architecture or its execution permissions.

Status: DESIGN ONLY, 2026-10-18. No implementation, migration, scan, experiment,
archive or publication is authorized. See the
[engineering contract](../spu_strategy/contract_inf1_research_qualification_2026-10-18.md).

INF-1 is a small set of offline provenance tools around existing experiments.
It records what was qualified, what could affect execution, and which evidence
supports each claim. It does not schedule experiments, replace their verifiers,
invent a CI graph, manage storage, or turn matching hashes into mathematical proof.

## Reference cases and evidence boundaries

| Reference reviewed | Reusable lesson | Limit retained |
|---|---|---|
| [SSM-4-M2](../spu_strategy/contract_ssm4_m2_dependency_boundary_2026-10-18.md) | Distinguish 148 research files from the proposed 2,188-file execution envelope; membership and conditional discovery matter | Proposal consistency passed; guard implementation/final freeze/qualification are not established by those records |
| [SSM-3 preservation](../research/ssm3_baseline_20261018/README.md) | Prelaunch 75-file overlay, ten proofs, restored-only proof regeneration and 14 focused methods | Original 244-test gate was not restored/rerun; captured modes were normalized; path audit is not an OS sandbox |
| [SG-0 preservation](../research/sg0_baseline_20261018/README.md) | Bind proof, geometry, quantization, packet and framebuffer evidence separately; preserve 159-file source identity and two 31-file bundles | Restore checked members and bundle manifests without rerunning proof/render execution; full repository suite was not run |
| [SIM-G2A contract](../spu_strategy/contract_sim_g2a_projected_scene_encoder_2026-10-18.md) and sibling qualification record | Identify base commit, dirty C++ overlay, fixtures, executable and ROM separately; preserve original halt and R1/R2 completion events | Executable replay is not a reproducible rebuild or symbolic reasoning in C++ |
| [SIM-G3 result](SIM_G3_QUALIFICATION_2026-10-18.md) and [R1 preparation](../spu_strategy/contract_sim_g3_r1_manifest_staging_2026-10-18.md) | Reference closure includes the root manifest, not only its listed payloads; replay and closeout are separate gates | Packet/RGB checks passed but original closeout failed; R1 preparation reports 12 focused tests, not completed R1 qualification |
| [RET-1](RET1_RESTORATION_REVIEW_2026-10-18.md) | Reuse strict tree/Git/member verification and archive restore; distinguish byte recovery from executable recovery | Stopped sources or an approved consistent snapshot are required; repeated hashes do not establish quiescence |
| [RET-3 review](ret3_review/README.md) | Distinguish runtime inputs, historical context, replay drafts and observed storage identities | 31-member review closure, no replay; destinations and stopped writers unconfirmed; all seven artifacts remain PROTECT |

The sibling SIM-G2A qualification record was read at
`/home/user/Projects/hardware/spu-sim/docs/SIM_G2A_QUALIFICATION_2026-10-18.md`.
It records bounded qualification, a 4/4 CTest result, and separate R1/R2 evidence
with an unchanged production executable. Earlier contract status headings are
historical, not substitutes for that evidence. No simulator execution was performed.

Primary M2 reference pins, read from existing reports without rescanning sources:

- 148-file research proposal SHA-256:
  `e1783dcc1dd1d8a1bec19c9fb97e75abe8642c325b0ba06439f95c786a846bab`.
- 2,188-file execution proposal SHA-256:
  `50a26954c9552b920b0bebfa77265409079093f4897975d23e036479cd246d86`.
- These describe a 75,926,095-byte conservative snapshot, not a universal default
  root list, newly approved manifest, or minimum proven dependency set.

## Small architecture

Use one experiment descriptor, two source manifests, environment attestation,
an evidence ledger and an offline summary. Their directed identity graph is:

```
reviewed descriptor + discovery profile + input identities
    -> candidate research/execution manifests + explicit unresolved edges
    -> owner-approved stopped-source/snapshot boundary
    -> immutable source capsule + environment/tool attestation
    -> existing authorized experiment runner and verifiers
    -> append-only evidence ledger -> offline reviewer summary
    -> existing RET-1 package/restore, if separately authorized
```

This graph records provenance; INF-1 does not execute a workflow DAG. Linux and
the existing detached runner own long jobs. Experiment contracts own commands,
limits, mathematical meaning and acceptance. RET tools own packaging/restore.

Proposed future implementation: one Python-standard-library package under
`tools/research_qualification/`, at most ten production modules of at most 150
lines each. Keep adapters narrow. Exceeding that cap requires scope review rather
than adding a plugin engine or general build system. Test fixtures are synthetic
unless a separately authorized reference profile permits named historical inputs.

## Identity contracts

| Record | Required meaning |
|---|---|
| Descriptor | Experiment ID/version, explicit named roots, research selectors, execution boundary, exclusions, discovery rules, commands, input/output roles, verifier identities and bounds |
| Research manifest | Behavior-defining implementation, mathematical fixtures and declared reference artifacts; may overlap execution identity |
| Execution manifest | All supported reachable repository inputs, runners/tests, discovery membership, ordered search paths, configuration and bounded conservative inclusions |
| Environment attestation | Tool paths and resolved executable hashes, versions, argv, relevant environment/settings, dependency/driver identities or explicit unresolved external dependencies |
| Evidence ledger | Per-attempt command, source/environment IDs, timestamps, terminal outcome, claim-level checks, outputs, skips, failures and amendment links |
| Summary | Human-readable projection of the ledger with artifact links, exact claims, limitations and reproducibility instructions |

Provisional schema names are `INF1_DESCRIPTOR_V1`, `INF1_RESEARCH_V1`,
`INF1_EXECUTION_V1`, `INF1_ENVIRONMENT_V1` and `INF1_EVIDENCE_V1`. They do not
replace RET-1, SSM0_V1 or historical experiment schemas. Read old records through
explicit adapters with their limitations preserved; never rewrite them.

Canonical semantic JSON: UTF-8, sorted keys, compact separators, integers/strings/
booleans/null only, no duplicate keys or nonfinite numbers, exactly one newline.
Preserve path bytes/case; reject ambiguous/control/traversing names rather than
normalizing distinct names into one. Reuse RET-1 path validation. Entries bind
logical root ID, relative pathname, type, mode, size/hash or link target. Named
root IDs distinguish SPU and spu-sim; historical absolute paths remain provenance,
not implicit permission to read an undeclared sibling or external installation.

Semantic identities exclude incidental timestamps and staging addresses; execution
records retain them separately. Environment identities include behavior-relevant
configuration. Preserve source modes as observed; never infer original modes from
an older archive that normalized them. Freeze Git HEAD/index/worktree inputs if
the experiment uses Git state. A commit alone does not identify a dirty experiment.

Hash the manifest externally; do not require it to contain its own hash. Stage a
referenced root manifest plus its exact declared member set, with separate digest
bindings. Reject missing root manifests, duplicate names, cycles in manifest
identity references and unexpected members. Hash integrity needs a reviewer-held
trust anchor; a hash supplied only by the same untrusted payload is insufficient.

## Dependency discovery with an explicit confidence boundary

Automatic discovery produces candidate edges with source location, guard,
resolution/search-order evidence and status: DECLARED, CONSERVATIVE, OBSERVED,
EXCLUDED_BY_ENFORCED_CONDITION, or UNRESOLVED. Never call static inference a proof
that arbitrary dynamic code cannot open another file. Unresolved relevant edges
block closure unless an approved bounded superset covers them.

| Language/workflow | Supported evidence | Required unresolved handling |
|---|---|---|
| Python | AST imports, explicit script/module calls, frozen module search roots, declared unittest/test discovery, literal data inputs | Dynamic import/eval/path construction and external packages remain explicit; do not import target modules to discover them |
| C++/CMake | Frozen source/header roots, build configuration, compiler argv and matching compiler-generated dependency records | Do not trust stale depfiles or assume text include parsing resolves macros, generated headers, flags or system headers |
| Verilog | Bench globs, parameter variants, include/-y search order, compile source lists, memory/ROM inputs and tool fallback branches | Preserve first-definition/source ordering; archived-test exclusion does not imply archived libraries are unused |
| Shell/runner | Declared argv, child scripts, environment guards, invoked helper identities and generated-output rules | Shell expansion, sourced scripts, platform branches and generated commands need explicit profile coverage or UNRESOLVED |
| FPGA | Existing reviewed build contracts, tool/chipdb/library/constraint identities and stage outputs | No synthesis/routing/hardware action or toolchain discovery scan is implied |

Recompute membership as well as hashes: new or removed tests, changed exclusion
rules, altered modes, helper substitutions and changed optional-tool availability
must change identity or fail a frozen guard. Conservative inclusion is permitted
and labelled; it is not evidence every included file executes. Enforced exclusions
need a frozen predicate and a check before dispatch, not an assumed environment.

Runtime-input checks are a separate capability. Consume existing qualified
execution/file-access traces where available; a future observer adapter must be
separately qualified for child processes, cwd-relative opens, links and generated
files. Compare observed reads/execs with declared input, generated-output and
external-runtime roles; unexpected inputs invalidate acceptance. Missing/incomplete
observation yields NOT_VERIFIED, never runtime closure PASS. This detects covered
observed accesses; it neither prevents reads nor proves all possible paths. Kernel
enforcement or hermetic execution would require a separate future contract.

## Immutable snapshots, replay and retention

Require owner-attested cessation of writers or an approved consistent snapshot
before copying source bytes. Record owner, scope and interval/snapshot identity.
Hash/recheck around copy, but do not use stable hashes as a substitute for that
boundary. Refuse links/special files beyond RET-1's qualified support. Never
silently follow an external dependency. Keep own output/capsule directories
outside their discovery boundary to prevent recursive capture.

Use fresh destinations, staging and a final publish step for local capsules;
retain failed attempts separately. Deterministic output requires fixed inputs,
tools/configuration and an explicit comparison criterion; byte equality is not
always the appropriate claim for performance/environment metadata.

Use `retention_archive.package/restore`, `verify_restore`, `retention_tree` and
`retention_git` for their qualified purposes. INF-1 supplies a reviewed descriptor,
member roles and an experiment-owned replay recipe, not another tar extractor,
Git migration tool, storage scanner, deduplicator or retention policy. The wrapper
itself still needs qualification. Rechecking a tree is not replaying the experiment;
replaying a staged executable is not rebuilding it; neither establishes recovery
from the loss of the development disk. Two independent recoverable copies and
stopped-source requirements remain RET policy matters. No PROTECT state changes.

## Evidence for reviewers and public releases

Generate offline JSON and Markdown from the same typed ledger. Each claim has
PASS, FAIL, INCOMPLETE, SKIPPED, NOT_RUN or NOT_APPLICABLE plus scope and evidence.
Terminal COMPLETE means exit 0, not that every required acceptance claim passed.
Refuse conflicting/missing terminal markers and missing required checks.

Keep proof replay, geometry, conversion, packet, RGB, depth, source identity,
environment, determinism, restoration and independent-copy status separate.
Preserve original failure events and missing-log disclosures; new amendments
append evidence instead of laundering an old failure into success. Report scope
and fixture counts, not an assumed historical full-suite total. Never infer
silicon observation from software output; an actual hardware claim must cite
the existing hardware evidence ledger.

Public summaries include a plain description, exact reproduction commands,
source/fixture/tool identities, supported platform, expected results, negative
controls, known differences, licenses/provenance and unavailable dependencies.
Do not expose credential-bearing environment values: attest only reviewed names;
use references for sensitive external configuration. Any redacted dependency
reduces the declared public replay scope rather than silently claiming completeness.
Generation is offline; upload, commit, tag and publication remain separate actions.

## Risks and sequencing

Main risks are false closure from static analysis, stale dependency records,
mutable tool installations, excessive conservative capture, concurrent writers,
manifest omission/self-reference, trust-anchor substitution and misleading summary
aggregation. Membership guards, explicit unknowns, strict staging and claim-level
records address these within stated bounds; no general hermeticity claim follows.

Finish SSM-4's own M2 guard/qualification and SIM-G3 verifier repair/closeout first.
Recheck their resulting evidence before selecting them as qualified INF-1 cases.
SIM-G2A and current focused results are reference observations, not permission to
rerun them. CPU physical routing remains independent. INF-1 is never a new gate
that either current workstream must wait for.
