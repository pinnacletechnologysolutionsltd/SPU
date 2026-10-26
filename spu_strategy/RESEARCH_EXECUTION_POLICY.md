# SPU research execution policy

Owner direction adopted 2026-10-19; prospective execution governance.
Classify the operation by cost, effects and risk, not the project name.
This policy changes permission to investigate, not the strength of evidence.

## A — Exploratory software

Within an owner-approved software scope, implementation, assertions, ordinary
debugging, corrective reruns, comparisons and negative controls are authorized
together. No per-run approval, frozen campaign or contract amendment is needed.
Keep the experiment script, tests and one short findings note with inputs,
commands, results, limitations and preliminary claim boundary. Preserve honest
failures and material corrections; do not create a review packet for each one.

Use local foreground execution, an external wall limit of at most 60 seconds
per invocation, and a reported memory limit appropriate to the workload.
For the QSG-2 pilot use 30 seconds and 1 GiB address space per process; no child
processes, network, devices, installation or services. Existing shell timeout
and resource limits suffice for these cooperative local tests; they are not
a sandbox, aggregate output quota or protection against hostile code. Inspect
the script before running it. If its limits cannot be applied, stop and report
the missing control rather than claiming enforcement. No detached work,
automatic timeout retries or splitting a long job to evade expensive-job rules.

Runtime writes stay in experiment-owned disposable scratch; script/tests and
findings are authored under the approved research directory through ordinary
edit authority. Do not modify production code, ISA, RTL, constraints, installed
tools, frozen evidence or shared state. Small outputs only; an unexpectedly
growing output/workload stops the experiment for rescoping. No new mandatory
manifest, archival capsule, scheduler or isolation framework. Existing build
artifacts remain subject to retention policy; this is no deletion permission.

## B — Engineering validation

Approved engineering scope includes ordinary testing and debugging. Retain a
lightweight record of source revision/dirty changes, exact commands, relevant
environment, inputs, limits, results and known limitations. Agree task-specific
local resource bounds; repeat tests within that scope without treating each
as a new campaign. Existing AGENTS.md regression gates still apply to production
behavior and shared infrastructure changes. Long jobs retain the detached-runner
rules. This policy grants no blanket permission to reopen frozen campaigns.

## C — Physical and infrastructure qualification

Keep existing explicit permissions, pinned inputs/commands, attempt counts,
budgets, evidence and rollback requirements for FPGA routing, board operations,
installed-tool/service changes, destructive maintenance and expensive jobs.
ROUTE-D1 R3 remains frozen; I4, B1, F1, F2 and integrated routing gain no
authorization here. Ubuntu/Vivado work remains deferred by owner direction.

## Claims and explicit transitions

A research result, independent verification and architectural qualification
are independent claims, not sequential permissions to investigate. Report what
ran and failed separately from review status. Independent review is required
for publication-grade claims and architectural promotion. Such claims must
meet the existing qualified comparison/evidence gates; preliminary findings
cannot advance earlier acceptance counters or establish hardware qualification.

QSG-2 is the initial approved Class A scope: isolated software under
`research/qsg2/`, implementation and small correctness/comparison fixtures from
its existing mathematical specification, including debugging and reruns.
Its contract's prior implementation/execution HOLD, separate per-run approval,
frozen execution-hash prerequisite and mandatory build-child campaign records
are prospectively superseded. Keep its exact arithmetic, error precedence,
independent equally informed baselines, negative controls and scope exclusions.
Keep 100 repetitions, one warm-up and at most three measured samples per named
workload for the initial comparison; record timings as exploratory measurements.
This policy turn itself launches no experiment.

Other frozen contracts require an explicit named transition; none is silently
reclassified. The earlier proposed INF-1R sandbox envelope remains unimplemented
and HOLD as that specific profile; it is not a prerequisite for Class A work.
INF-1 qualification toolkit implementation remains deferred. Historical records,
QSG-0/QSG-1 outcomes, preservation and Q/H claim safeguards are unchanged.
