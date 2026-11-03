# SYMREG-0 through SYMREG-3 — research summary

This is an informal research index, not an architectural contract or a v0.2
qualification claim. The preserved experiments are at commit `c002164`.

| Study | Bounded result | Limits and negative findings |
|---|---|---|
| [SYMREG-0](qaf_symreg_0/FINDINGS.md) | Checked shadow facts, version invalidation and norm reuse in a small software model. | REVISE: a manually hoisted baseline did the same norm work faster in the observed workload; no hardware performance claim. |
| [SYMREG-1](qaf_symreg_1/FINDINGS.md) | Composed equality, conjugation, scaling and norm relations with immutable value identities; tested branch intersections and a narrow multiply refusal. | PASS within tested cases; directed inference is incomplete, retention is bounded, branch feasibility is supplied and the ISA is not fully modeled. |
| [SYMREG-2](qaf_symreg_2/FINDINGS.md) | Sparse paths and rooted canonical descriptors recovered some relations with fewer stored facts and inspectable provenance. | PASS within scope; arbitrary pair queries, some zero-scaled chains and conclusions using different branch paths can remain unknown. Python timings do not imply hardware benefit. |
| [SYMREG-3](qaf_symreg_3/FINDINGS.md) | A query-directed semantic join retained a common conclusion with separate proofs for all declared-feasible branches. | PASS within scope; proofs are bound to one in-process context, no post-join `DISPROVEN` is emitted, and branch feasibility remains an assumption. |

Across all four, algebraic norm is distinct from the ISA's tuple-normalizing
`SNORM`. Finite tests and bounded solver results do not prove the full Python
implementation, 64-bit ISA behavior, RTL or physical hardware. Important open
questions include portable proof replay, trustworthy premise and branch-set
binding, bounded certificate size and identity lifetime, completeness at joins,
and comparison against ordinary compiler dataflow on realistic traces.
