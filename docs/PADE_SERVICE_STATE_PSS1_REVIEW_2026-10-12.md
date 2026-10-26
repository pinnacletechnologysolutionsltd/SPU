# Padé service-state PSS-1: preparation review

Date: 2026-10-12. Status: DRAFT; source audit only. Software implementation and
qualification have not run. The active Artix-7 attempt remains independent.

Review [the proposed contract](../spu_strategy/contract_pade_service_state_pss1_2026-10-12.md).
The selected surface is the A31 `rplu_thimble_pade` evaluator, not the separate
Q32/Q16 approximation engine or a CPU retirement interface.

| Question | Source evidence | Classification / disposition |
|---|---|---|
| Held DONE/SINGULAR and acknowledgement? | `docs/STATE_MACHINE_HARNESS.md:151`; `hardware/rtl/gpu/rplu_thimble_pade.v:354` and `:387` | CONFLICTING descriptions. Test the RTL pulse/return-to-idle protocol; held-state abstraction is not implemented. |
| Singularity writes zero? | Evaluator `:361` versus success write `:389` | CONFLICTING with older description. Preserve the known previous result; before first success the result is unspecified. |
| Admission while busy? | Evaluator `:251` | Source-level: start is sampled only in IDLE. Busy starts are ignored; held start can re-admit after completion. Execution UNVERIFIED by this tranche. |
| Multiplier backpressure? | Evaluator port `mult_busy`, launches `:271`, `:316`, `:347`, `:381` | UNSUPPORTED here. Owner must make every emitted request admissible. |
| Inverter acknowledgement? | Evaluator `:354` | Source-level: repeated inv_start until inv_busy; count one accepted request. Response timing remains an explicit environmental obligation. |
| Reset clears coefficients/result? | Initial table `:76`, independent write process `:104`, reset `:235` | Neither is reset by this evaluator. Configuration persists; no valid result is implied by retained bits. |
| Snapshot of inputs? | Saddle rereads `:312` and `:343`; coefficient rereads during Horner | UNSUPPORTED live reconfiguration. Keep saddle and coefficients stable throughout an evaluation. |
| Stale response detection? | Untagged multiplier/inverter completion ports | UNSUPPORTED intrinsic detection. External owner must reset or drain outstanding engines before reuse. Checker ownership labels cannot be attributed to RTL. |
| Pipeline variant? | Evaluator `:138` | Separate PADE_PIPELINED 0/1 profiles; result equivalence does not imply equal latency. |
| Sidecar retirement / shared ownership? | `hardware/rtl/core/spu13/spu13_rplu2_pade_sidecar.v:138`, `:296`, `:435`, `:451` | DEFERRED integration surface. Initial model does not qualify arbitration, instruction acknowledgement or lane commit. |

First deliverable after review: a bounded software model plus an independent
obligations checker. Exercise success, both zero and nonzero singular cases,
recovery, ignored/held starts, variable engine latency, reset in every active
phase, and registered-handoff cancellation. Require negative controls for
premature/duplicate completion, stale ownership, bad phase, partial writes and
singular-result consumption.

Proposed focused software budget: one attempt, 900 seconds maximum and
cumulative. It is not authorized by this draft. A future RTL trace qualification
needs its own contract, full required gates and separately authorized Padé build.
No physical job is launched as part of this preparation.

Existing tests `hardware/tests/spu13/rplu_thimble_pade_tb.v` cover six stored
arithmetic vectors and a nonzero singular denominator. Their source is retained
for reuse; this review does not infer reset/drain or service-state qualification
from arithmetic checks. Existing composition tests exercise policy outcomes,
not this evaluator's request/response lifecycle.

Under [AGENTS.md](../AGENTS.md), “HALT immediately and flag the flaw” applies to
implementing a contradictory incoming state description. The minimal correction
is the proposed source-faithful lifecycle. No production change is necessary to
prepare it. Ratify that lifecycle before implementing the model.
