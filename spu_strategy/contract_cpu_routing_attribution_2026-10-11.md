# Engineering Contract: CPU routing attribution

**Date:** 2026-10-11  
**Status:** ACTIVE — owner authorized three attempts and repairs  
**Roles:** Codex drafts, implements observational tooling and audits its controls; owner authorizes the bounded campaign.

Owner authorization: “Authorized. 3 attempts, repairs authorized.” Freeze three total attempts at 1,800 seconds each and 5,400 seconds cumulative. Diagnostic tooling repairs may use the spare slot; no launch follows an exhausted budget.

Launch the first stage:

```bash
python3 build/spu_surd_register/routing_diagnosis_20261011/preparation_03/launch_diagnostic.py build
```

Record the detached unit and output directory, then end the turn. In a later invocation, interpret exactly one terminal marker. Only after a recorded tool build has exactly one `COMPLETE` marker and `PASS_TOOL_BUILD_AND_SMALL_CONTROL`, run:

```bash
python3 build/spu_surd_register/routing_diagnosis_20261011/preparation_03/launch_diagnostic.py route
```

Record the detached unit and output directory, then end the turn. The shared campaign ledger is `build/spu_surd_register/routing_diagnosis_20261011/campaign_budget.json`. Preserve `preparation_01` and `preparation_02`; use repaired `preparation_03`. Do not change the approved timeouts or reuse output directories. A routing launch selects a recorded build with exactly one COMPLETE marker and passing controls.

## Scope and frozen inputs

Prepare routing observations under `build/spu_surd_register/routing_diagnosis_20261011/`; modify no CPU RTL, ISA, arithmetic, reset, retirement, transports, or experimental profiles. Preserve the completed regression and the original timeout artifacts.

Reuse `decoder_campaign_20261011/timing_01/cpu_1.json`, its `constraints.xdc` and `build/chipdb/xc7a100tfgg676.bin`. Their SHA-256 values are recorded in `preparation_03/inputs.json`, together with the observer, exact upstream source and selected compiler/library dependencies. Check every recorded hash before launch and inside the worker. Use Artix-7 100T, 40 ns primary clock, `--freq 25`, `--seed 1`. Do not rerun synthesis or substitute another CPU configuration.

Rebuild the installed tool's source revision, [openXC7 nextpnr-xilinx f681eb3a](https://github.com/openXC7/nextpnr-xilinx/tree/f681eb3a), with its original router2 implementation. The only source differences in the observed tool are the helper include and a call after `update_congestion()`, where routing workers have joined. `tool_source/router2_observe.patch` records these differences. Preserve the upstream license. Do not upgrade or substitute the routing backend.

The rebuild resolves current GNU 16.2.1, Boost 1.92 and Python 3.14.8 dependencies. The historical installed binary used a Boost 1.91 ABI shim. This is a reconstruction of the same routing source, not a reproduction of the historical binary. Record both baseline and observed binary hashes. A small control cannot establish identical CPU placement across different tool builds; the new capture attributes its own observed routing, not retroactively the old 747 resources.

## Authorized bounded diagnostic budget

| Stage | Maximum attempts | Per-attempt maximum | Gate |
|---|---:|---:|---|
| Observer tool build and small routing controls | 1 | 1,800 seconds | Frozen-input check and new owner budget |
| Frozen CPU routing capture | 1 | 1,800 seconds | Tool build COMPLETE and control PASS |

One additional repair/retry attempt is available for either stage: maximum **three total attempts**, **1,800 seconds each**, **5,400 seconds cumulative**. Repairs require refreshed source hashes, focused controls and a new isolated preparation before launch. Retry decisions occur in a later invocation after terminal review. No automatic retry, timeout extension or transfer between stages. The launcher conservatively consumes a reservation before submission; a submission failure requires review and owner authorization before another attempt. Each detached command includes desktop notification; notification delivery is not evidence.

This is an attribution campaign, not full CPU timing qualification. Full repository qualification is not claimed for these preparation artifacts. Any later RTL or production build-flow repair retains AGENTS.md §4 required gates and needs its own reviewed implementation scope and budget.

## Current evidence and limits

The preceding `timing_01` has exactly one `TIMEOUT` marker and exit 124 after 7,200 seconds. Its final aggregate report was iteration 30: 747 overused wires and total overuse 748. It contains no routed JSON, FASM, SDF or per-wire ownership checkpoint. Therefore the historical contested nets cannot be identified from those artifacts. Placement's estimated 27.07 MHz is not routed acceptance.

The resource audit of this **exact-digital** candidate reports 80 DSPs, all in Surd. The earlier 234/240 DSP projection belongs to a different candidate. Do not conflate the builds.

`static_inventory_02/summary.json` and `mapped_nets.jsonl` flatten the saved mapped hierarchy and retain aliases, source locations, driver pins and sink pins: 61,588 logical nets and 158,985 sink pins. Packing can transform this topology. The following are candidates for inspection, **not measured contested owners**:

| Logical signal | Sink pins | Mapped source reference |
|---|---:|---|
| Internal active-high reset | 6,045 | Frozen `surd_exact_quotient.v:5`; 6,032 sinks in Surd, 13 in annealer |
| External active-low reset | 5,562 | Frozen `spu_quadray_regfile_ecc.v:15` and other aliases; shared across units |
| QR `rd_lane[2]` | 1,492 | Frozen `spu_quadray_regfile_ecc.v:16`, `spu_quadray_regfile.v:24` |
| QR `rd_lane[0]` | 1,126 | Same lane-selection interface |
| Surd `aligned` | 963 | Frozen `spu13_surd_arith.v:20`, `surd_cpu_products.v:3` |
| QR `rd_lane[1]` | 863 | Same lane-selection interface |

The clock has 12,892 logical sinks and uses clock resources; its fanout alone is not evidence of general-routing congestion. Do not attribute the reset to REGEN merely because an alias sorts first.

## Observer verification and capture

Execute the focused preparation controls:

```bash
python3 build/spu_surd_register/routing_diagnosis_20261011/preparation_03/test_net_inventory.py
python3 build/spu_surd_register/routing_diagnosis_20261011/preparation_03/test_diagnostic_gate.py
python3 build/spu_surd_register/routing_diagnosis_20261011/preparation_03/diagnostic_worker.py preflight unused
```

Recorded preparation evidence: 10 synthetic logical inventory controls; nine synthetic observer controls; two positive and nine negative intercepted launch controls; real router API syntax check exit 0. Full linked-tool execution and CPU conflict capture remain **NOT RUN**.

The build worker compiles the unmodified tool, then incrementally compiles the observed router in a private source copy. Run the same small counter fixture with the baseline tool, observer disabled and observer enabled. Require exact equality of parsed placed/routed JSON, no records when disabled, and consistent published ownership counters when enabled. This control establishes only the named small fixture. Synthetic multi-owner and cycle/fault controls supplement it.

At each completed CPU routing iteration, capture:

1. Contested wire names, owner counts, owning nets and driving pips.
2. Implicated net drivers and users, with packed cell/port names and BEL coordinates.
3. Actual routed sink arcs traversing each contested wire, distinguished from other sinks of that net.
4. A summary published last, whose overused/overuse counts match router counters.

Ignore `.tmp` files and any iteration without its summary. On timeout, retain complete iteration captures as partial diagnostic evidence; do not call the route successful. If capture itself fails, flag the tooling failure separately from CPU routing. Measure observer overhead before making any comparative runtime claim.

## Analysis and repair gate

After a terminal marker, rank contested resources by tile/region and implicated nets by contested wires, actual affected sink arcs, fanout and endpoint span. Join packed names to mapped aliases/source references where possible; explicitly record unmatched or packing-transformed names. Distinguish ownership evidence from causal interpretation. Compare early and late iterations to identify persistent conflicts.

Write a source-referenced bottleneck table before proposing a repair. A repair must name the implicated net, endpoints, physical region, proposed RTL change and expected measurable effect. Select among local selection logic, fanout reduction, bus organization or placement only after capture supports the choice. No arithmetic redesign follows merely from unit size or timeout.

Preserve ISA, exactness, destination-preserving faults and the five-lane Surd arithmetic. If a proposed repair introduces pipeline stages, draft a separate contract covering accepted issue-to-completion latency, exactly-once retirement, source snapshot/alias behavior, reset cancellation, drain and stale-response exclusion. Run falsifiable directed tests and the required full gates before accepting it.

**25 MHz remains unqualified until legal routing and complete required timing coverage pass.** This campaign does not authorize board programming or silicon claims.

## Attempt 1 review and authorized include-path repair

`tool_build_01/result.json` records FAILED, exit 1, 67 seconds. The unmodified baseline compilation failed at `common/placer_heap.cc:37`: `Eigen/Core` was absent from compiler include paths. The installed header exists at `/usr/include/eigen3/Eigen/Core`. The legacy CMake script uses `EIGEN3_INCLUDE_DIRS`; the current package configuration does not populate that variable. No observer execution or CPU routing occurred.

Pass `-DEIGEN3_INCLUDE_DIRS=/usr/include/eigen3` to both tool builds, preserving HeAP and all algorithm sources. Freeze the Eigen CMake package files in addition to the already hashed headers. Preserve prior sources/results; use `preparation_03`. Re-run launch controls and input checks before attempt 2. Require generated include flags and a syntax check of the previously failing placer source to pass. The repair consumes no extra launch slot until the detached attempt starts; attempt 1 remains consumed.
