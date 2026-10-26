# Sparse Jet MAC RTL review

Status: COMPLETE within standalone RTL simulation scope; full frozen
qualification PASS. [Implementation contract](../spu_strategy/contract_sparse_jet_mac_rtl_2026-10-11.md).

The 112-line MAC captures coefficients and tags on acceptance. A separate
25-line index module schedules order-major window intersections using tags
alone. Results and tags retire together; busy covers retirement and done
pulses once. The primitive uses an external shared multiplier; valid A31
addition/products, including nonunits, leave err_zero_divisor clear.
Dense MAC, shared multiplier, core dispatch and Surd/REGEN are unchanged.

| Surface | Evidence and classification |
|---|---|
| N=2/N=4 arithmetic, tags and counts | Matching under all 305 window pairs, add/multiply, independent polynomial expectations and rectangular source-index enumeration |
| Directed values | Basis products, canonical residue extrema, cancellation, nonzero zero divisors and dense-tagged all-zero coefficients; no value-based skip or tag sharpening |
| Completion | Matching under direct real-multiplier responses and delayed responses with per-product jitter; source mutation and busy-time starts cannot replace the accepted operation; prior result/tag held through retirement |
| Shared reset/drain | Matching in exclusive-owner harness: common reset cancels ISSUE/WAIT/RETIRE; MAC-only reset retains ownership until old response disposal; withheld response holds busy; following-edge reuse succeeds |
| Invalid tags/coefficients | Explicitly rejected by simulation monitors; hardware relies on valid issuer provenance, with no new fault encoding |
| Other orders and integration | Unsupported qualification scope; N15 checks only five-bit tags and six-bit sums. Multi-client arbitration and core integration are unverified |
| Mapping, timing, silicon, performance | NOT RUN; speedup, energy and board performance unmeasured |

[Focused evidence](../build/sparse_jet_mac/rtl_focused_05/report.json) binds
source and generated fixture hashes. There are 118 N2 and 532 N4 fixture
vectors, each run with delay settings 0, 3 and 7: 1,950 fixture executions.
Each configuration also exercises reset/drain, stalled response and immediate
following-edge acceptance. Delayed responses add product-dependent jitter.
Nine negative controls detect mistagging, malformed tags, noncanonical
coefficients, wrong count/result, premature reuse, early busy drop, unsolicited
completion and extra multiply issue. The driver refuses an existing output.

Two fixture defects were corrected during development: a malformed N2 tag
initially wrapped before reaching the monitor, so the negative vector now uses
the representable invalid window [2,0]; drain setup now lets the registered
launch reach the supplier before resetting only the MAC. These are harness
corrections, not changes to the qualified arithmetic or reset/drain policy.

```bash
python3 -B software/tests/test_sparse_jet_mac_rtl.py
```

The standalone primitive cannot identify an untagged stale response inside a
new WAIT. Its owner must establish fabric idle by common reset or explicit
drain before reuse. The premature-reuse negative test demonstrates this
ownership requirement; no top-level arbiter correctness is inferred.

Full qualification must run on an isolated frozen snapshot with source checks,
the focused driver, existing dense/scoped regression, all mandatory trace/math
and repository gates, and the separate 25 MHz Padé build. The recorded qualification budget covers one completed attempt only; further
long jobs require separate owner-frozen budgets. The Padé image does not contain
or qualify the sparse primitive's physical timing.

The owner approved one 7,200-second full qualification attempt. The isolated
[preparation](../build/sparse_jet_mac/rtl_qualification_preparation_01/preflight_review.json)
freezes 2,050 source files over the qualified software baseline and proves
that failed source checks or missing budget approval prevent launch.
The output is `build/sparse_jet_mac/rtl_qualification_01`; qualification completed with exactly one COMPLETE marker, exit 0, in
2,072/7,200 seconds. All 14 gates passed, including repository 244/0,
scoped 68/0, software/RTL oracles, ROTC/IROTC, math, documentation, the separate
25 MHz Padé build and before/after source checks.
[Closure record](../build/sparse_jet_mac/rtl_qualification_01/qualification_review.json)
binds all 2,050 tested source hashes and individual gate exits. The standalone
RTL tranche is closed within this frozen simulation scope. Core integration,
multi-client arbitration, sparse-specific mapping/timing and board work remain
NOT RUN.
