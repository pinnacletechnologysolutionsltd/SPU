# Bounded Exact Quadratic-Surd Registers with Atomic Retirement

**Working manuscript — updated 2026-10-15. Results and conclusions are provisional.**
This draft describes implemented architecture and retained evidence. It is not
submission-ready: integrated timing/resource review and
related-work comparison remain open. No novelty, CPU speedup, energy or board
performance claim is made.

## Abstract

We describe a processor-visible register bank for exact arithmetic over
rational quadratic surds with radicand three. Each finite-width register stores
signed integer coefficients and a positive explicit denominator. Multiplication,
denominator-aligned addition/subtraction and deliberate normalization operate
on full-width intermediates. Results retire atomically: successful operations
commit an exact representable tuple; invalid inputs, engine faults and
unrepresentable results preserve the destination. Source capture permits
source/destination aliases, and reset cancels pending retirement.

The implementation has eight 192-bit registers and a W=64 arithmetic engine
with five integer multiplication lanes and a shared GCD/exact-quotient
normalizer. Directed RTL simulation establishes agreement with an independent
oracle on selected inputs and on 128 retained forward/recovery kernels. Those
kernels execute 5,632 scheduled boundary reductions without observed kernel
failures or fallbacks. Their total measured simulation costs range from 3,378
to 50,764 cycles across chain lengths one through twelve, including tuple
transfers and issuer control. Standalone FPGA routing records characterize
lane-count and normalization costs. The corrected integrated candidate synthesized and packed with 234 DSP48E1s
out of 240 available in a historical mapping attempt. A subsequent frozen
backend candidate passed placement checks for 51,197 cells and a later route
passed an independent all-net integrity audit. Timing qualification remains
blocked by incomplete active-arc and corner coverage [E12–E14]. A historical
qualification failed in its clock auditor despite passing directed mapped
arithmetic stages; that record is separate from the corrected candidate. The evidence supports an implemented exact
retirement contract and scoped cost measurements, not general software
conformance or a demonstrated advantage over equivalent integer execution.

## 1. Motivation and contribution

Exact geometric calculations can require repeated products, sums and reductions
of rational algebraic quantities. Encoding these quantities in ordinary integer
registers requires software to manage coefficients, denominators, intermediate
widths, normalization and failure. This work investigates moving that contract
into a separately addressed arithmetic bank while retaining visible failure
semantics and the existing processor's scalar/Quadray state.

The research question is: **what correctness and implementation costs follow
from a bounded exact quadratic-surd register contract with atomic retirement?**
The contribution presented here is the combined representation, operand
interface, overflow-rescue policy, scheduled normalization and implemented
retirement behavior. Exact represented values do not imply unlimited range,
constant latency, low resource cost or application speedup. Integer and
fixed-scale computation may also be exact within their supported domains.

The present manuscript fixes the radicand at three. General quadratic-field
support, PCIe, SOM routing, full VM parity and concurrent CPU/GPU integration
are outside the evaluation. A complete comparison with rational arithmetic
processors, exact geometric number types and custom arithmetic extensions is
required before submission; this draft asserts no priority or novelty claim.

## 2. Representation and architectural contract

For coefficient width W, an initialized register contains

\[
(a,b,d),\qquad -2^{W-1}\le a,b<2^{W-1},\quad 0<d<2^W,
\qquad V(a,b,d)=\frac{a+b\sqrt3}{d}.
\]

Different tuples can represent the same value. Architectural tuple identity is
therefore distinct from value equality. These registers represent a bounded
subset of Q(√3), not a finite-width domain closed under every field operation.
At W=64, eight tuples contain 1,536 data bits, excluding validity, transfer
staging, ports and control logic. This storage count is not the resource count
of the complete arithmetic engine.

### 2.1 Arithmetic and intermediate widths

For operands `(a,b,d)` and `(c,e,f)`, multiplication forms

\[
(A,B,D)=(ac+3be,\;ae+bc,\;df).
\]

The signed real accumulator requires `2W+2` bits. With all four coefficients
at `−2^(W−1)`, its value is `2^(2W)`, which exceeds the maximum of a signed
`2W+1`-bit accumulator. W=64 consequently requires 130 real-accumulator bits.
The radical sum requires `2W+1` signed bits and the denominator product `2W`
unsigned bits. Inputs must not be narrowed before these calculations and checks.

Addition/subtraction first computes `g=gcd(d,f)`, `u=f/g`, `v=d/g`, then

\[
(A,B,D)=(au\pm cv,\;bu\pm ev,\;du).
\]

Here `u,v` are unsigned scale factors; values above `2^63−1` must not become
negative through signed interpretation. The implementation sign-corrects the
coefficient products and retains wide sums before testing representability.
The oracle review independently checks component values using rational
fractions and checks the chosen aligned tuple representation [E3].

### 2.2 Fit, rescue and canonicalization

The accepted FIT_RESCUE policy has three outcomes:

1. Valid raw results fitting all architectural widths commit unreduced.
2. Raw overflow invokes exact normalization; fitting reduced results commit.
3. Invalid operands, unrescued overflow or an engine fault commit no destination
   change and retire a distinct status.

Canonical reduction divides all three components by
`G=gcd(abs(A),abs(B),D)`. It preserves the positive denominator and maps valid
zero to `(0,0,1)`. Signed-minimum magnitudes must be represented without
signed negation overflow. Quotient engines verify zero remainder before a
successful commit.

A fitting raw zero intentionally retains `(0,0,D)`. Explicit SNORM and
normalization rescue use canonical zero. Historical S0 canonicalized every
zero; its evidence is retained as a different policy and is not reused as the
CPU tuple-identity oracle.

### 2.3 Register transfers and instruction interface

The extension uses the canonical 64-bit instruction layout, retaining existing
R/QR meanings. It is enabled explicitly and does not use the separate WF
adapter profile. Source/destination indices address S0–S7.

| Opcode | Operation | Operand interface |
|---|---|---|
| 0x70 SLI | Stage a 32-bit slice | R1 destination, R2 slice, P1_A/P1_B payload |
| 0x71 SLD | Atomically load staged tuple | R1 destination |
| 0x72 SRD | Read a 32-bit slice | R1 source, R2 slice |
| 0x73 SMUL | Exact product | R1 destination, R2 first source, P1_A low8 second source |
| 0x74 SADD | Exact aligned sum | Same three indices |
| 0x75 SSUB | Exact aligned difference | Same three indices |
| 0x76 SNORM | Canonical reduction/copy | R1 destination, R2 source |
| 0x77 SSTAT | Read held status | No operands |

Slice order is `a-low,a-high,b-low,b-high,d-low,d-high`. SLD rejects incomplete
staging and denominator zero. Full indices and reserved fields are validated
before narrowing; malformed indices do not wrap. Status values are OK=0,
INVALID=1, OVERFLOW=2, ENGINE_FAULT=3 and BAD_ENCODING=4. The frozen boundary
and implementation source identities are retained in [E1].

### 2.4 Acceptance, retirement and reset

Only one arithmetic instruction is in flight. On acceptance, the engine
captures both operand tuples and destination identity. Subsequent completion
therefore uses accepted operands even when destination equals either source.
The issuer waits for retirement. A successful operation causes one atomic
bank write; failure reports status without partially replacing components.
Reset clears validity, cancels pending work and prevents a stale completion
from writing the bank. These properties are implemented commit conditions and
directed verification targets, not an exhaustive proof over all sequences.

## 3. Microarchitecture

The frontend separates tuple transfer/staging, bank access, arithmetic and
retirement. The arithmetic engine shares an exact normalizer between explicit
SNORM, denominator alignment and overflow rescue. Scheduled normalization must
execute even when preceding arithmetic fits; FIT_RESCUE alone does not satisfy
an application boundary-reduction policy.

The normalizer combines bounded binary GCD and exact quotient engines built
from shifts, comparisons and subtraction. Synthesizable runtime `/` and `%`
operators and inferred divider/modulo hardware are prohibited. This is still
mathematical division: the permitted implementation generates exact quotients
and verifies remainders. The engine is not advertised as a general division
instruction.

One-, two- and five-multiplier schedules have been evaluated with the same
Surd product semantics. The current CPU candidate uses five lanes; normalization
is serviced separately. A one-cycle product fit path does not imply one-cycle
addition, normalization or complete CPU execution.

## 4. Verification and evidence boundaries

The W=32/64 revalidation contains 654 distinct oracle inputs exercised across
three lane schedules, giving 1,962 directed RTL executions [E2]. Cases include
signed extrema, raw-fit commits, normalization rescue, invalid denominators,
unrepresentable results and the 130-bit real-accumulator witness. Agreement on
this cohort does not establish universal or formal correctness.

Focused CPU execution passed the retained 128-kernel cohort and the declared
interface checks [E4]. A subsequent directed verification update adds aliases,
whole-bank/validity failure-preservation checks and injected terminal failures;
its focused result does not renew historical full regression or synthesis
qualification [E5]. Oracle host checks are separately classified: they verify
reference calculations, not RTL timing or implementation.

The selective REGEN mapping qualification later completed two seeded 256-cycle
known-input mapped/reference comparisons and 177 rows / 708 full 84-bit product
comparisons, with deliberately corrupt expectations rejected. Fresh mapping
connectivity and legacy checks also passed. The campaign then failed in the
clock auditor: its hierarchy walker assumed every child port had a parent
binding. **Directed mapped arithmetic PASS and overall qualification FAILED
are both retained** [E8]. The Verilator checks are two-state checks, not a
four-state X/Z equivalence proof.

System suspension explains the campaign's large UTC duration relative to its
frozen timeout: the old enforcement and accounting clocks differed across
suspend. A maintained auditor repair now handles optional outputs while
rejecting required missing inputs/clocks; a CLOCK_BOOTTIME supervisor accounts
for elapsed time including suspend and rejects late completion. Repair qualification
completed on attempt 1 with a durable COMPLETE marker, exit 0, in 2,122 seconds.
Auditor, deadline and canonical Python/C++ control checks passed, together with
242 repository tests, 151 scoped tests, trace/math gates and the mandatory
standalone Artix-7 Padé build [E9]. Suspend coverage uses synthetic clock jumps;
a physical suspend exercise remains unmeasured. The three-attempt repair
allocation is closed with two unused attempts. These results neither rewrite
the failed historical qualification nor establish integrated Surd CPU resources
or routed timing. Subsequent mapping and backend placement campaigns are reported separately
in §6.3; their allocations and configurations are distinct from this repair.

## 5. Retained kernel evaluation

Thirty-two frozen input vectors are evaluated at each chain length N=1,3,6,12.
The schedule includes inverse-coefficient preparation, forward transforms,
reverse inverse transforms, spills/reloads and complete readback. All four
components, including unchanged A, receive SNORM at each forward and recovery
joint boundary. Thus a record executes `8N` scheduled reductions, and the
cohort executes 5,632.

Joint coefficients are rational-only (`b=0`). Nonzero-radical directed cases
exercise arithmetic and interfaces separately; they are not a representative
radical-heavy application workload. The exact operation schedule and source
input/program hashes are retained with the CPU campaign [E4].

### 5.1 Measured simulation costs

Each row aggregates 32 cases. Cycles include CPU dispatch-port execution,
tuple transfers and issuer control; boot/reset are excluded. These are simulated
cycle counts, not operating-time, board-throughput or host-transport measurements.

| Chain length | Cases | Total cycles | Min–max cycles per case | Retired instructions | Scheduled reductions |
|---:|---:|---:|---:|---:|---:|
| 1 | 32 | 139,591 | 3,378–4,509 | 9,216 | 256 |
| 3 | 32 | 399,323 | 9,526–12,919 | 22,784 | 768 |
| 6 | 32 | 789,125 | 18,748–25,543 | 43,136 | 1,536 |
| 12 | 32 | 1,568,084 | 37,192–50,764 | 83,840 | 3,072 |

| Chain length | Transfer instructions | Transfer cycles | Alignment cycles | Normalization cycles | Issuer-control cycles |
|---:|---:|---:|---:|---:|---:|
| 1 | 7,712 | 15,424 | 66,735 | 31,992 | 18,432 |
| 3 | 18,272 | 36,544 | 200,211 | 95,976 | 45,568 |
| 6 | 34,112 | 68,224 | 400,395 | 192,186 | 86,272 |
| 12 | 65,792 | 131,584 | 800,820 | 383,904 | 167,680 |

All 128 cases matched the expected results; recorded kernel failures, fallbacks,
overflow-rescue requests and stalls were zero. Normalizer starts were not zero:
alignment and scheduled reduction are distinct reasons to invoke it. The traces
record 736,2,208,4,416 and 8,832 total normalizer requests by chain-length cohort.
Phase counters do not substitute for arithmetic readback comparison and are not
presented as a complete mutually exclusive decomposition of total cycles.

Alignment accounts for about 50.7% of the aggregate 2,896,123 cycles and
normalization for about 24.3%, using the retained phase-counter definitions [E6].
These measurements identify costs to investigate; they do not establish which
architectural change would improve total kernel performance.

### 5.2 Baseline limitation

An equivalent integer-only path is unsupported in the active canonical core.
It needs wide coefficient/denominator products, signed accumulation with
unsigned scale factors, exact GCD/quotients, representability checks, atomic
updates and executable sequencing. Existing opcode names do not establish
those capabilities [E10]. The kernel here executes through the CPU dispatch
port; no full program-fetch/PC/stack integration is claimed.

Consequently speedup, instruction elimination and energy benefit remain
unmeasured. Host Fraction timings, estimated MCU instruction counts or one
integer multiplication would not constitute the same exact computation and
failure contract.

## 6. FPGA implementation trade-offs

### 6.1 Product schedule

Standalone W=16 wrapper records report the following results [E7]. Normalizer
arithmetic is excluded from these lane-comparison wrappers.

| Lanes | Simulated fit latency | Simulated fit II | DSP48E1 | Reported LUTs | Reported FFs |
|---:|---:|---:|---:|---:|---:|
| 1 | 6 | 7 | 1 | 623 | 348 |
| 2 | 4 | 5 | 2 | 728 | 348 |
| 5 | 1 | 2 | 5 | 382 | 184 |

At W=64, corresponding isolated wrappers report 16, 32 and 80 DSPs, with 3,012,
4,042 and 4,483 LUT counters respectively. Those width-dependent costs cannot
be inferred from W=16 alone. Fit-path latency/II measurements do not include
normalization service or CPU transfer overhead.

### 6.2 Combined multiplier and normalizer

The standalone W=64 five-lane multiplier-plus-normalizer wrapper completed
routing on XC7A100T with a 25 MHz target, reporting 80 DSP48E1s, 15,341 LUTs,
4,683 FFs and 744 CARRY4s [E7]. Its post-route tool estimate is 46.90 MHz. This is
an existing standalone-wrapper record, not an integrated CPU timing result or
measured board clock. Resource labels follow the retained report; packed-site
occupancy must not be substituted for logical LUT counts.

In a separate 327-case synthetic W=64 correctness cohort, 49 raw products fit,
275 requested normalization and 3 were invalid. Five-lane normalized-operation
latency, including multiplication, ranges from 3 to 467 cycles with a 426-cycle
mean. The cohort is boundary-focused and does not estimate typical rescue
frequency. The retained rational kernels have a different request distribution.

### 6.3 Integrated route passes structural audit; timing remains unqualified

A prior integrated campaign timed out during implementation. Its synthesis
reported 210/240 DSPs and packing reported 96% LUT-slot occupancy; placement did
not complete, so it establishes no routed timing or critical path. The selective
candidate restores four REGEN products to DSPs. Standalone attribution confirms
six DSPs per product, 24 total. The frozen preparation_11 integrated attempt
subsequently completed synthesis and packing with **234/240 DSP48E1s**:
154 with Surd disabled and 234 with Surd enabled, an increment of 80.
The selected four REGEN products account for 24 DSPs. Packing reported
103,775/126,800 SLICE_LUTX slots (81%); these tool slots are not a logical
LUT count or proof of routability.

That attempt ended with exactly one TIMEOUT marker, exit 124, after its
7,200-second frozen wall-clock limit during main analytical placement.
Placement and legal routing did not complete; required timing coverage and
PASS at the 25 MHz target are unavailable [E11]. This is confirmed synthesis
and packing usage, not accepted integrated fit or board performance. The
separate Padé qualification build does not qualify this image. Speedup,
energy and board performance remain unmeasured.

A subsequent frozen backend candidate completed placement in 637 seconds;
independent replay confirmed 51,197 cells in distinct BELs, logical topology,
five 16-DSP lanes, frozen DSP sites and carry segmentation [E12]. This is
placement PASS under the tested backend legality model. Its earlier comparison
baseline timed out in 1,800 seconds. Capped traces do not establish patch
causality or prove that the baseline can never place this design.

Packet 06 subsequently completed routing with nextpnr-himbaechel
`v1.2-typestate-187-g4e51d2f` for `xc7a100tfgg676-1`, router2, seed 1 and a
25 MHz constraint. An independent all-net audit passed for 61,113 nets,
1,061,576 routing resources and 192,229 physical sinks; all 51,197 cell
bindings passed preservation checks and no cross-net wire/PIP ownership
conflicts were found [E14]. This establishes route integrity under the
retained backend and audit checks, not timing closure or silicon behavior.

The timing report's **40.886 MHz** result remains an unqualified tool estimate.
The 20 absent CE summaries were traced to 19 constant-high and one
constant-low enable, so no switching CE check applies to those endpoints.
Synchronous reset/set setup/hold, asynchronous recovery/removal, and the
configured DSP active arcs still lack complete qualified timing data across
the required corners. Timing qualification remains HOLD; 25 MHz operation is
not established. The routed checkpoint is preserved and no reroute was needed
for this audit. The historical 234-DSP mapping counts above belong to a
different configuration and must not be combined with Packet 06's 80 DSPs.

Historical unsuccessful campaigns remain integration evidence. The arithmetic
representation and atomic retirement contract are unchanged. The separate
AOR-S1 software qualification and Padé build establish no Surd CPU timing,
silicon, speedup or energy claim.

## 7. Discussion and limitations

The register contract makes normalization policy and representability failure
explicit. It preserves the exact represented result on success and prevents
partial destination corruption on failure. Directed tests support this behavior
within their exercised scope; universal sequence correctness remains open.

Measured kernel costs show that denominator alignment, normalization and data
movement matter even when overflow rescue is absent. Increasing multiplication
parallelism alone does not establish a kernel speed benefit. Optional future
work includes radical-heavy workloads and different normalization/alignment
implementations under the same contract, each requiring its own measurements.

Canonical control compatibility repairs passed focused checks and the repair
regression campaign [E9],
but full software conformance is not established. They do not add missing core
fetch/PC/stack functionality. PCIe, SOM and further GPU bring-up are future work
and prerequisites for none of the scoped arithmetic conclusions here.

## 8. Provisional conclusion

The implemented CPU extension demonstrates bounded exact quadratic-surd
arithmetic, explicit normalization and atomic retirement on retained directed
simulations. Kernel traces and standalone routing records supply measured cost
material. The current evidence does not demonstrate integrated FPGA timing,
board operation, native integer speedup, energy advantage or full software
conformance. Repair qualification is complete; final results and conclusions
remain subject to evidence review. Unresolved integration may remain an explicit
limitation in a submitted paper.

## Evidence references

These repository records are implementation evidence, not a completed external
bibliography. The companion draft evidence manifest records their hashes.

- **E1:** `main_cpu_integration_20261007/implementation_freeze_01/manifest.json`
  and `annex_draft_02/annex.md`, under `build/spu_surd_register/`.
- **E2:** `main_cpu_integration_20261007/wide_revalidation_01/coverage.json`
  and terminal result.
- **E3:** [Independent oracle review](../SURD_CPU_ORACLE_REVIEW_2026-10-07.md).
- **E4:** `main_cpu_integration_20261007/focused_01/cpu/results.json`,
  source/program identities, runtime and campaign terminal result.
- **E5:** `cpu_verification_update_20261007/verification_02/results.json`;
  the update's broader gates were not renewed.
- **E6:** `software_preparation_20261007/analysis_01/kernel_analysis.json`
  and [trace-analysis scope](../SURD_CPU_KERNEL_ANALYSIS_2026-10-07.md).
- **E7:** `mul_arch_20261007/architecture_comparison.md`, `wide_map_04/`,
  `combined_w64_lanes5_01/summary.md`, terminal records and nextpnr reports.
- **E8:** `main_cpu_integration_20261007/integrated_build_04/result.json`
  and `selective_regen/qualification_02_attempt_03/` stage/terminal records.
- **E9:** [Failure diagnosis](../isa/SURD_QUALIFICATION_DIAGNOSIS.md) and
  `build/repo_audit/repairs_20261010_01/qualification_closeout.json`;
  `build/repo_audit/repair_qualification_20261010_01/result.json`,
  `deadline.json`, individual gate exit records and raw logs. COMPLETE, exit 0,
  2,122 seconds; standalone Padé build only, no integrated CPU mapping.
- **E11:** [Integrated attempt result](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/integrated_mapping_01/result.json),
  [synthesis comparison](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/integrated_mapping_01/synthesis_resource_comparison.json),
  [REGEN attribution](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/integrated_mapping_01/cpu_1.regen_dsp_audit.json)
  and [packing/placement log](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/integrated_mapping_01/cpu_1.nextpnr.log).
  Configuration: XC7A100T, five W64 Surd lanes, four selected REGEN products,
  seed 1, target 25 MHz; source identities in the preparation_11 manifest.
- **E10:** [Equivalent integer baseline capability gaps](../../spu_strategy/spec_surd_integer_baseline_capabilities_2026-10-07.md).

- **E12:** [Latest candidate placement closeout](../../build/spu_surd_register/backend_compatibility_20261012/integrated_context_closeout_01/REVIEW.md): candidate placement PASS, baseline TIMEOUT; no route or board operation.
- **E13:** [Timing-model audit](../../build/spu_surd_register/backend_compatibility_20261012/routing_timing_preparation_01/timing_model_audit.json) and [routing/timing preparation](../../build/spu_surd_register/backend_compatibility_20261012/routing_timing_preparation_01/REVIEW.md): incomplete required timing coverage blocks qualification.
- **E14:** [Packet 06 master qualification](../../build/spu_surd_register/backend_compatibility_20261012/packet06_audit_reconciliation_01/packet06_master_qualification_20261015_rev05.json), [independent all-net audit](../../build/spu_surd_register/backend_compatibility_20261012/packet06_audit_reconciliation_01/packet06_all_net_audit_20261015.json), and [timing review](../../build/spu_surd_register/backend_compatibility_20261012/packet06_audit_reconciliation_01/packet06_timing_arc_mapping_20261015.md): route integrity PASS, timing HOLD. Exact route, executable and chip-database identities are recorded in hardware evidence §3.39.

## Before submission

- Completed: qualify auditor/deadline/control repairs through required gates [E9].
- Independently review original mapping/resource/timing counters and constraints.
- Obtain integrated routing/timing, or retain integration explicitly unresolved.
- Retain measured kernel costs with issuer/transfer scope and denominator policy.
- Provide an equivalent baseline before making any speedup claim.
- Complete related-work/novelty review and an external bibliography.
- Freeze the final manuscript and its reproducibility/evidence package separately
  from this working draft. Physical claims require the hardware evidence ledger.
