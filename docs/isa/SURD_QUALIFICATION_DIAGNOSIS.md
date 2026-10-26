# Surd qualification failure diagnosis

Date: 2026-10-09. Allocation02 closed: three attempts consumed. No retry/build
launched. Preserve these two conclusions separately:

- Directed mapped arithmetic: PASS within the recorded test scope.
- Overall qualification: FAILED. Integrated timing: unresolved.

## Clock auditor root cause

The third attempt stops at `audit_mapping.py:23` with `KeyError: mem_burst_rd`.
The hierarchy walker assumes every child module port is bound by its parent:
`bindings[port]`. The retained benchmark omits multiple optional core ports,
including output `mem_burst_rd`; omitted outputs have private child nets and
need not have parent nets. Valid omitted outputs therefore crash before clock
coverage is examined. This is an auditor assumption defect, not an arithmetic
comparison failure or a timing PASS.

The retained core also has omitted inputs on disabled optional interfaces.
A repair must distinguish output omissions from inputs: skip only the parent
union for unbound outputs while retaining child internal traversal; require a
reviewed inactive-feature/unused-cone proof for an omitted input. Never silently
skip a required clock, data, enable or reset input. Validate port directions,
connection widths, unknown parent ports and hierarchy recursion.

Before another campaign, the revised helper needs synthetic controls for omitted
outputs, used/unused input omissions, missing required clock, mismatched width,
unknown port, nested hierarchy and aliasing, plus the retained netlist inventory.
Its clock/SDF coverage must still reject every unconstrained required endpoint.
This diagnosis does not change frozen preparation_08 or repair production RTL.

## Deadline accounting root cause

The worker records duration with `date +%s` but enforces timeout through GNU
`timeout`. Unit start: 2026-10-07T23:21:21Z. Suspend requested about 24 seconds
later; suspend entered at23:21:46Z. System resumed 2026-10-09T05:49:40Z, then
the command failed at05:50:54Z. The result records 109773 elapsed seconds.
The unit journal reports1 min 41.141 s wall clock and1 min 38.299 s CPU consumption.

The journal establishes a long suspend interval covering nearly all of the
reported overrun. The timeout did not expire across that suspend before the
command resumed. UTC elapsed accounting and the timeout's suspend behavior
therefore do not implement the same deadline contract. This is not evidence of
30 hours of active arithmetic work, and not compliance with a hard elapsed 1200s
budget. Retain FAILED exit 1 as the recorded command outcome; annotate deadline
noncompliance separately rather than rewriting historical markers.

Proposed runner amendment, before another expensive launch: define elapsed
versus active-time budget explicitly; retain both CLOCK_BOOTTIME and
CLOCK_MONOTONIC plus UTC samples; use an independent suspend-aware elapsed
deadline watchdog and record which deadline fired. On resume after expiry,
terminate work before accepting a result. Keep command exit, budget breach and
terminal recording separate. A reviewed policy may additionally inhibit sleep
for a bounded campaign, but no system sleep setting was changed here. Shared
runner changes require their own tests/full gates and budget; existing timeout
options alone are not a demonstrated fix.

## Retained passing stages and limits

Two seeded 256-cycle known-input Verilator mapped/reference comparisons passed;
the deliberately corrupt expected value exited nonzero. Full 84-bit product
checks passed 177 rows / 708 comparisons; their defect control was rejected. Fresh
connectivity identity reuse and legacy REGEN checks passed. Selected products
map to24 DSPs. These are directed two-state simulation and standalone mapping
results, not exhaustive/formal verification, integrated resource confirmation,
routed timing, silicon evidence or speedup.

The clock/SDF auditor controls did not complete. No `focused_results.json`
complete PASS exists. Total 234/240DSP remains projected.

## Evidence

[Raw diagnostic package](../../build/repo_audit/reconciliation_20261009_01/)
contains original document snapshots, unit/suspend journal commands and logs,
missing-port inventory and hashes.
[Terminal review](../../build/repo_audit/canonical_path_20261009_01/qualification_review.json)
preserves the campaign result and directed stage identities.
Frozen failed job: `build/spu_surd_register/main_cpu_integration_20261007/`
`selective_regen/qualification_02_attempt_03/`.

No automatic retry, integrated build or deadline extension is authorized by
this diagnosis.

## October 10 repair status

Maintained helper `tools/audit_surd_cpu_mapping.py` handles omitted outputs
(including Yosys empty arrays), accepts omitted inputs only when their bits
are unused by the child, and rejects malformed widths/unknown ports/required
flop pins and untimed endpoints. The retained mapped netlist and negative
clock/port controls pass focused checks. Frozen campaign scripts remain intact.

`tools/run_elapsed_deadline.py` now supervises the worker using CLOCK_BOOTTIME
including suspend, records active/elapsed clock samples, and rejects late
completion even when the child returns0. Process-group termination is bounded.
Synthetic clock-jump and worker-protocol checks pass; no physical suspend test
or full regression qualification is claimed. The failed historical allocation
and integrated timing status are unchanged.
