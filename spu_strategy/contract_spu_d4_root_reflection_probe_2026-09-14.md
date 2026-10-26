# Engineering Contract: SPU D4 Root-Reflection Hardware Probe

Date: 2026-09-14  
Contract ID: `contract_spu_d4_root_reflection_probe_2026-09-14.md`  
Status: **P0/P1 PASS; P2 HALTED ON XDC ERROR, CORRECTED RETRY BUDGET PENDING**  
Target: Wukong Artix-7 using the project-pinned FOSS flow

The owner initially authorized P0 software-oracle work, then authorized P1 RTL
verification and a two-attempt P2 campaign. P1 is complete. The first P2
attempt was consumed and failed before placement because the LED IOSTANDARD
wildcard in the XDC did not bind to the ports. The XDC is corrected below, but
the original budget is not extended; a fresh matched retry budget requires
owner approval. Neither phase authorizes board programming, ISA allocation,
procurement, or P3 power measurement.
The historical T1d telemetry limitation remains recorded; later T1g and GPU
physical results establish the separate dynamic-scene capability. P0 is
software-only and does not depend on either hardware claim.

## 1. Decision question

Can a fixed D4 simple-root reflection unit be implemented correctly with a
measured resource, latency, throughput, or controlled-energy advantage over a
fair integer implementation of the same operation?

A correct but uncompetitive implementation is a useful negative result. It
does not invalidate the geometry or existing SPU work.

## 2. Frozen first-probe mathematics

For `v=(v0,v1,v2,v3)` and a root of squared norm two,

```text
r_alpha(v) = v - (v dot alpha)*alpha.
```

Use four signed 16-bit lanes and this fixed simple-root set:

```text
alpha0 = e0-e1   swap v0,v1
alpha1 = e1-e2   swap v1,v2
alpha2 = e2-e3   swap v2,v3
alpha3 = e2+e3   (v2,v3) -> (-v3,-v2)
```

The three swap roots accept every signed 16-bit lane value. For `alpha3`, an
input is invalid if either negated source lane is `-32768`. The unit asserts
`invalid_flag`; output bits on invalid input are unspecified and must not be
consumed. Every valid result is exact in ordinary signed-integer arithmetic.
Modular wraparound is excluded and may not be called norm-preserving over the
integers.

The oracle must check reflection involution, exact squared-norm preservation on
valid inputs, root norms, pairwise inner products, and the chosen D4 Cartan
relations. Cartan entries do not bound `v dot alpha` for an arbitrary vector.

## 3. Proposed isolated interface

```verilog
module spu_d4_reflection_unit (
    input  wire [63:0] in_v,
    input  wire [1:0]  root_sel,
    output wire [63:0] out_v,
    output wire        invalid_flag
);
```

The first unit is combinational. A separately measured clocked wrapper must
define reset, acceptance, latency, initiation interval, and status alignment.
Capturing a combinational result at an edge is not automatically a one-cycle
pipelined datapath.

A programmable arbitrary `(i,j)` selector is a different hardware cost point.
Exclude a vector register file, full permutation crossbar, Weyl-chamber
canonicalizer, opcode decode/writeback, and all neural-attention machinery.

Mapping claims must distinguish three cases:

1. a compile-time-fixed swap may disappear into routing and has zero
   arithmetic/DSP cost;
2. a runtime-selected fixed-root operation requires selector decode and output
   multiplexers; and
3. the signed swap also requires two's-complement negation and detection of
   `-32768`.

A registered wrapper consumes registers and a defined pipeline latency even
when its underlying permutation is routing-only. No unmeasured case may be
described simply as “zero-cost” or “zero-latency.”

## 4. Evidence phases

### P0 — independent software oracle — AUTHORIZED

Run this exact command from the repository root:

```bash
python3 software/tests/test_d4_reflection_oracle.py
```

Implement both the mathematical formula and an independently written
swap/sign-swap specialization. Compare them over all `16^4 = 65,536` vectors
whose lanes are signed 4-bit values and all four root selectors (262,144
input/root cases). The formula uses unbounded Python integers; the
specialization applies signed 4-bit representability checks to `alpha3` and
marks `v2 == -8` or `v3 == -8` invalid. For each valid case, check reflection
involution and exact squared-norm preservation. Then check every selector on
all `7^4` signed-16 lane tuples formed from:

```text
-32768, -32767, -1, 0, 1, 32766, 32767
```

Also check all four roots and selectors on 4,096 seeded signed-16 vectors
generated with Python `random.Random(0xD4_2026)`. For `alpha3`, `v2 == -32768`
or `v3 == -32768` must assert `invalid_flag`; invalid output bits are not
compared or consumed. Check root norms, the full pairwise inner-product matrix,
and the resulting D4 Cartan matrix. Print case counts and one final PASS/FAIL
line; return nonzero on any mismatch.

**P0 result: PASS.** `python3 software/tests/test_d4_reflection_oracle.py`
returned exit 0. The 262,144 reduced exhaustive cases, 9,604 signed-16
boundary cases, and 16,384 seeded cases passed. The oracle checked exact
formula/specialization agreement, invalid `alpha3` overflow signaling,
involution, squared-norm preservation, root norms, and the D4 Cartan matrix.
No RTL or hardware work was performed.

“Exhaustive” always means a stated finite-width domain; unbounded integer
identities require exact reasoning or proof rather than enumeration.

### P1 — RTL verification — PASS

`hardware/rtl/math/spu_d4_reflection_unit.v` implements the combinational
four-root signed-16 interface. The independent formula comparator is
`hardware/rtl/math/spu_d4_reflection_generic.v`. Both were compared with P0
over the same 288,132 reduced, signed-16 boundary, and seeded cases by
`python3 software/tests/test_d4_reflection_rtl.py`; exit 0 and all data/status
comparisons passed. Invalid alpha3 output bits were not consumed. Yosys
`hierarchy -check; proc; check` passed for both selected implementations with
zero reported problems, and the unit inferred no latches. This is simulation
and structural evidence, not formal proof or hardware evidence.

### P2 — matched synthesis and route — PREPARED

Freeze source revision, exact part, clock/I/O constraints, tool/database
versions, placement seed, comparator interfaces, detached commands, timeouts,
and campaign budget. Record LUT, FF, CARRY4, DSP, BRAM/LUTRAM, routed Fmax,
critical path, warnings, and constraint failures using the established Artix-7
flow.

The matched candidates use one shared route harness and constraints:

* Part: `xc7a100tfgg676-1` (Wukong Artix-7 100T chip database).
* Clock: 50.00 MHz, one 20 ns clock matching the Wukong board oscillator,
  fixed placement seed 1.
* Toolchain: Yosys plus nextpnr-xilinx 0.8.2-73-gf681eb3a, loaded by
  `source tools/env_openxc7.sh`.
  Yosys is `0.63+87` (`2f1cdc2df`).
* Harness: `hardware/boards/artix7/spu_a7_d4_reflection_bench_top.v`; a common
  on-chip changing vector/root source feeds the selected combinational unit,
  and registered lane-parity/status outputs keep its result observable.
* Constraints: `hardware/boards/artix7/spu_a7_d4_reflection_bench.xdc`.
* Runner: `bash tools/run_d4_reflection_p2.sh specialized <evidence-dir>` or
  `bash tools/run_d4_reflection_p2.sh generic <evidence-dir>`.
  Both use `--freq 50 --seed 1 --timing-allow-fail`; 50 MHz is a common
  timing-driven placement target, not a pass threshold. The measured final
  routed Fmax is reported as data for both candidates.
* Evidence: Yosys cell/resource report, nextpnr routed utilization/Fmax and
  critical-path log, packed/routed JSON, FASM, and tool output, retained in
  each detached job directory.

Compare both:

1. the directly specialized fixed swap/sign-swap implementation; and
2. a generic integer dot/reflection datapath implementing the same numeric and
   interface contract.

If the SPU candidate is identical to the specialized baseline, report that
fact. Comparing only with the generic datapath would exaggerate a gain.

Original P2 budget authorized two detached route attempts, one per candidate,
3,600 seconds per attempt and 7,200 seconds cumulative. Attempt 1 (specialized)
was consumed and failed in nextpnr packing before placement. Its terminal result
is `FAILED`, exit 255, after 5 seconds. The nextpnr error was:
`port led_out[0] of type PAD has no IOSTANDARD property`. Do not run only the
generic candidate: that would leave no routed specialized result for comparison.
The second original budget slot is held unused. A fresh two-attempt campaign is
proposed after the corrected XDC, with one run per candidate, 3,600 seconds per
attempt, 7,200 seconds cumulative, seed 1 and the same 50 MHz settings. Await
explicit owner approval before launching the corrected matched pair.

Frozen comparison input hashes before launch:

| Input | SHA-256 |
|---|---|
| `build/chipdb/xc7a100tfgg676.bin` | `9d79e339c19fc3b42a5c409c47e58175ee199c2852d9096ea31c226e34398543` |
| `hardware/rtl/math/spu_d4_reflection_unit.v` | `5dbf69f431285a7bb55657d65bfd909c30efa981890ca42f766f13fde88425e8` |
| `hardware/rtl/math/spu_d4_reflection_generic.v` | `0bf1a808e3feda9b3008d808bc2aa62f22bd118a430f1fd7f4a11bff1ffbdd41` |
| `hardware/boards/artix7/spu_a7_d4_reflection_bench_top.v` | `ead6f0eec6065766a7e1cdac7641cd0604a02fd5649c56e98573975d45b778b1` |
| `hardware/boards/artix7/spu_a7_d4_reflection_bench.xdc` (corrected) | `7bb0c147051b0895962a27c2ab278fc76140111fe1bb7cd106adb3d83973d92b` |
| `tools/run_d4_reflection_p2.sh` | `e1a8e8d81c094cf3ec58761b03cf7151d601d745bd1a5de5c227d65510bc2e89` |

Proposed exact detached commands for the corrected matched pair, pending
approval of the fresh budget:

```bash
tools/run_detached_job.sh \
  --output build/d4_reflection_p2/corrected/specialized/run_01 \
  --timeout 3600 --notify-desktop -- \
  bash tools/run_d4_reflection_p2.sh specialized build/d4_reflection_p2/corrected/specialized/run_01

tools/run_detached_job.sh \
  --output build/d4_reflection_p2/corrected/generic/run_01 \
  --timeout 3600 --notify-desktop -- \
  bash tools/run_d4_reflection_p2.sh generic build/d4_reflection_p2/corrected/generic/run_01
```

### P3 — optional physical power

Claim energy per operation only with matched work and output rates,
idle-subtracted rail measurements, instrument uncertainty, and both candidates
on the same board. LUT count and estimates are not measured energy.

## 5. E8 follow-up gate

E8 sparse roots and half-roots are excluded from the first probe. Before any
E8 RTL, freeze the valid E8-lattice coordinate domain, half-root sign/parity
encoding, root list, intermediate widths, exact divisibility conditions,
overflow semantics, and conversion to any SPU format.

One candidate doubled-coordinate representation uses `x=2v` and

```text
c    = (sum_i x_i*s_i) / 4
x'_i = x_i - c*s_i,
```

but it is eligible only where lattice membership proves `c` integral. A signed
shift is not evidence of exact division without that proof. Eight signed
16-bit summands require a wider accumulator and wide output candidates before
16-bit range checks. Validate closure, norms, simple roots, and Cartan relations
independently. Do not assume E8 maps like the sparse D4 swaps.

## 6. ISA and workload gate

Consider ISA integration only after P0–P2 pass and a named workload benefits.
Then inspect current numeric/register formats, opcode map, ports, hazards,
overflow signalling, software support, and integration cost. No opcode is
reserved by this parked contract.

Root reflections do not themselves implement attention, softmax, arbitrary
root-orbit search, hyperbolic distance, semantic inference, or SOM learning.
The lattice/LLM and any reopened SOM hypotheses remain separate contracts.

Exact Quadray Euclidean quadrance also does not imply multiplier-free distance
hardware: a general sum of squares still requires mapped multiplication,
shift-add, or serialized arithmetic. Squared-distance comparison avoids a
square root in both Quadray and conventional Cartesian integer coordinates.

## 7. Later-phase boundary

P1 RTL verification is complete. P2 synthesis/route must use the matched
candidates, part, clock, seed, commands, and owner-approved bounded budget
above. P1/P2 do not authorize FPGA programming or P3 power measurement. Do not
infer a hardware advantage from P0/P1 or from synthesis alone.
