# Surd product routing attribution and placement proposal

**Status:** DRAFT placement proposal; read-only attribution complete. No new launch authorized by this document.  
**Date:** 2026-10-11

Reproduce the completed-capture analysis:

```bash
python3 build/spu_surd_register/routing_diagnosis_20261011/attribution_01/analyze.py
python3 build/spu_surd_register/routing_diagnosis_20261011/attribution_01/physical.py
```

Read `normalized.json`, `physical.json`, `dsp_lane_placement.json`, `affected_arcs.jsonl` and `job_reconciliation.json` in that directory. Preserve the frozen sources and original attempt outputs.

## Normalized comparison

The final completed iteration of the 1,800-second capture has 1,194 contested wires and 1,549 implicated nets. Exactly 1,547 names join to mapped aliases; the two remaining names are packing-generated constant nets. All eleven complete iteration records passed ownership-counter validation.

The baseline is **53,466 mapped nets with both a driver and sinks**, totaling 158,983 sink pins. This is pre-pack connectivity, not a complete physical net census. To keep classification consistent, the table assigns both the baseline and matched conflicts by mapped driver unit. This differs from the earlier quick ranking by packed net-name prefix, especially for boundary aliases.

| Driver unit | Mapped net share | Mapped sink-pin share | Matched conflicting-net share | Matched owner/wire incidence share | Mean mapped fanout | Mean fanout of conflicting nets |
|---|---:|---:|---:|---:|---:|---:|
| Surd products | 24.4% | 12.3% | 52.9% | 47.9% | 1.50 | 2.53 |
| Surd arithmetic excluding products/normalizer | 4.5% | 5.7% | 19.1% | 21.8% | 3.80 | 15.21 |
| Surd normalizer | 24.6% | 24.0% | 9.8% | 9.2% | 2.90 | 17.79 |
| Surd bank | 5.1% | 4.1% | 13.2% | 14.4% | 2.38 | 7.75 |
| QR/ECC | 23.3% | 16.3% | 0% | 0% | 2.07 | — |

Products contribute 819 of 1,547 matched conflicting nets versus 13,058 of 53,466 active mapped nets: roughly **2.17 times their net share**. Their conflicting-net median fanout is 2. This concentration is not explained by block size or extreme fanout alone. The mapped denominator and packed capture remain different representations, so enrichment is a diagnostic comparison, not a causal or statistical significance claim. Zero QR/ECC entries applies only to this final matched snapshot.

Product alias buses have a median declared width of 128 bits, weighted by named bits; normalizer aliases have 130 bits and a similar mapped net share, with fewer conflicts. Surd bank/dispatch expose 192-bit operand aliases. These widths do not count independent routed buses: aliases and unit ports overlap. They support investigating wide connectivity, but cannot identify width as the cause. Named product families `p0`, `p1`, `p2`, `p3` are 128-bit multiplication results; signed correction and final addition extend the arithmetic to 130 bits.

## DSP connections, boundaries and location

The capture contains **1,512 distinct affected sink arcs touching products**:

| Arc relationship | Count | Share of affected product arcs | Median endpoint Manhattan span |
|---|---:|---:|---:|
| Both endpoints inside products | 1,166 | 77.1% | 32 grid units |
| One endpoint outside products | 346 | 22.9% | 24 grid units |
| At least one DSP endpoint | 241 | 15.9% | 75 grid units |

DSP endpoint arcs overlap the internal/boundary categories. Most product arcs therefore have no DSP endpoint. The DSP subset has longer spans, but its whole-design baseline conflict rate is unavailable. Spans are placement-grid distances, not wire length or delay.

All 80 DSPs appear in the endpoint census and partition into five multiplication roots of 16 DSPs each. Three roots span multiple DSP columns. Their vertical grid spans range from 83 to 114 units. These are observed placements, not violations of an established ideal placement.

650 of 1,194 contested wire names fall in tile coordinates X20–39, Y80–89; the X20–29, Y80–89 bin alone contains 491. The largest individual tile has 15 contested wires. This establishes a location cluster. Without whole-design routed-wire occupancy, it does not establish excess congestion density there. Wire-name tile coordinates and endpoint placement-grid coordinates differ; no proximity to a DSP column is inferred by mixing them.

Source references in the frozen decoder `preparation_03/source_snapshot`:

- `hardware/rtl/math/surd_cpu_products.v:9–14`: operand selection and five unsigned 64×64 products; mapped multiplication roots retain these file/line identities.
- `hardware/rtl/math/surd_cpu_products.v:15–38`: exact signed correction, 130-bit extension and result recombination. The affected internal families include `p1`, `p0`, `p2` and generated add/subtract networks.
- `hardware/rtl/core/spu13/spu13_surd_arith.v:20–36`: alignment control and operand/product boundary.
- `hardware/rtl/core/spu13/spu13_surd_arith.v:52–81`: issue snapshots, PRODUCT capture, completion and normalization paths.

## Proposed first repair experiment: product-lane placement

Prepare a **placement-only candidate** on this exact frozen mapped netlist. Preserve arithmetic expressions, five lanes, 80 DSPs, signed correction, widths, clocks, state transitions, latency, reset and retirement. Make no RTL change in the first candidate.

1. Recover each multiplication root and its DSP fragment/cascade connectivity from the mapped netlist. Associate its partial-product adders and carry/recombination cells through exact net edges, not generated-name resemblance alone. Keep shared correction/final-combination cells explicit rather than assigning them arbitrarily to a lane.
2. Generate a reviewed pre-placement constraint file that groups each root's DSP fragments with its associated fabric logic. Validate site types, uniqueness, available capacity and existing packing/cascade-relative constraints. Avoid concentrating all five lanes into the same observed hotspot. Do not select hard BEL assignments solely from these summary statistics.
3. Use the existing router revision's `--pre-place` hook and `BEL` attributes only after checking their interaction with relative constraints. Source: frozen router `common/command.cc:119,336` and `common/placer_heap.cc:370–383`. The concrete assignment manifest and exact launch command remain pending implementation review; this proposal is not a runnable placement prescription.
4. Compare unchanged netlist connectivity and primitive counts before/after constraints; measure product endpoint spans, conflict persistence, per-lane conflict incidences and legal routing under identical declared tool/input/clock conditions. Retain whole packed-net and placement metadata so future comparisons have a physical denominator. Account for observer overhead and host contention.

This tests whether physical organization helps the measured product/recombination network. It does not assume DSP placement is the sole cause. If constraints make spans or congestion worse, reject the candidate. If a later connectivity rewrite is proposed, require bit-exact mapped equivalence of both output coefficients and denominator for all input bits, including negative coefficients and both aligned modes, plus the required full gates. Any pipeline proposal needs a separate latency, retirement, reset-cancellation and drain contract.

## Job and budget reconciliation before any launch

| Job unit | Purpose | Bound | Recorded state |
|---|---|---:|---|
| `spu-tool_build_01-20261011T003049Z-418688` | Observer baseline build | 1,800 s | FAILED, exit 1, 67 s |
| `spu-tool_build_02-20261011T005032Z-424056` | Repaired build and controls | 1,800 s | COMPLETE, exit 0, 388 s |
| `spu-routing_capture_01-20261011T010017Z-431170` | Conflict capture | **1,800 s** | TIMEOUT, exit 124, 1,800 s |
| `spu-timing_01-20261010T215210Z-398545` | Earlier decoder timing | 7,200 s | TIMEOUT, exit 124, 7,200 s |
| `spu-timing_01-20261011T012925Z-434289` | Separate bottleneck timing campaign | **14,400 s** | LAUNCHED; terminal result unavailable at reconciliation |

The diagnostic ledger authorizes three 1,800-second slots, 5,400 seconds cumulative; all three slots are consumed. Actual recorded diagnostic execution totals 2,255 seconds, including the two builds. The routing capture's allocation alone is 1,800 seconds.

The separate `bottleneck_audit_20261011/allocation.json` authorizes one timing slot of 14,400 seconds within a 21,000-second focused/regression/timing campaign. Its timing slot is consumed. Do not pool either campaign's remaining wall-clock allowance or treat identically named `timing_01` directories as the same job. The 14,400-second job launched 53 seconds before the short capture timed out, so the capture cannot support runtime comparisons assuming exclusive host use.

No result is inferred for the 14,400-second job from its logs, elapsed time or process state. Preserve that job and its frozen candidate. Before a subsequent launch, interpret exactly one terminal marker, review the proposed placement inputs and secure a fresh bounded budget; this exhausted diagnostic campaign authorizes no additional attempt.

**Legal routing and complete required 25 MHz timing remain unqualified.** No silicon, speedup, energy or full-CPU fit claim follows from this attribution.
