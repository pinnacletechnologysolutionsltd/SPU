# Rational SOM v1 Product Contract

Date: 2026-07-16

## Product claim

SOM v1 is a deterministic, writable best-matching-unit classifier over
integer-coefficient `Q(sqrt(3))` feature vectors. Its useful distinction is not
"an FPGA SOM" by itself; it is exact field arithmetic, stable tie-breaking,
best/second-best evidence, and bit-exact replay across the software oracle and
supported FPGA targets.

The v1 deployment model is:

1. train a genuine SOM offline;
2. quantize its four-feature prototypes to signed 18-bit `Q(sqrt(3))` pairs;
3. hydrate the FPGA's writable map;
4. stream a feature vector and classify it deterministically;
5. return the winning node, label, runner-up, confidence gap, and ambiguity.

Winner-only dyadic adaptation exists in RTL and the VM, but it is a conservative
prototype-adaptation mechanism, not a claim of complete neighborhood SOM
learning in hardware.

## Canonical implementation

| Function | Canonical path |
|---|---|
| Exact oracle and stable tie-break | `software/lib/rational_som.py` |
| Writable map | `hardware/rtl/core/spu13/spu_som_weight_bram.v` |
| Serial BRAM-backed BMU | `hardware/rtl/core/spu13/spu_som_bmu.v` |
| Confidence/ambiguity reduction | `hardware/rtl/core/spu13/spu_cluster_reduce.v` |
| Optional winner adaptation | `hardware/rtl/core/spu13/spu_som_train.v` |
| Core opcodes and host hydration | `hardware/rtl/core/spu13/spu13_core.v` |
| Small standalone edge target | `hardware/boards/tang_primer_25k/spu13_tang25k_som_sidecar_top.v` |
| Host console and map uploader | `hardware/rp_common/spu_diag.c`, `tools/upload_som_weights.py` |

The old fully parallel `spu_som_node` / `spu_som_node_array` / cfg-bus
`spu_som_sidecar_top` implementation is archived under
`hardware/boards/tang_primer_25k/archive/`. It is historical reference code,
not an alternate v1 implementation and not part of the active regression gate.

`spu13_som_classify.v` and the PHSLK temporal-classification work are separate
research tracks. They are not dependencies of SOM v1.

## Arithmetic and behavioral contract

- A feature or prototype component is `{Q[17:0], P[17:0]}`, representing
  `P + Q*sqrt(3)` with signed coefficients.
- A node distance is `sum(r_j * (x_j - w_ij)^2)` in `Q(sqrt(3))`.
- Distances are ordered with the exact integer-only field comparison, not a
  lexicographic `(P,Q)` comparison and not floating point.
- Equal distances retain the lower node index because the map is scanned in
  ascending address order and only a strictly smaller distance replaces a
  candidate.
- The runner-up is retained. `confidence_gap = second_q - best_q`.
- With the default zero threshold, an exact zero gap asserts `ambiguous`; the
  deterministic winner is still returned. Ambiguity is evidence, not a fault or
  terminal state.
- Classification observes a feature snapshot captured on `start` and a map
  scanned from synchronous BRAM. Host writes and adaptation must not be launched
  concurrently with a classification.
- The seven-node classifier has a test-pinned latency of 434 clocks. The exact
  field comparator always executes its 33-step square schedule and each ranked
  node receives the same best/runner-up work, so input values do not alter the
  cycle count.
- `SOM_TRAIN` applies only to the last valid winner:
  `w <- w + ((x - w) >>> shift)`. Arithmetic right shift rounds negative odd
  deltas toward negative infinity, so this is bounded fixed-point adaptation,
  not exact rational division.

## Host-facing v1 operations

The standalone Tang sidecar accepts existing `0xA5` configuration writes:

| `sel` | Meaning | Address/data |
|---:|---|---|
| 4 | prototype write | `addr[4:2]=node`, `addr[1:0]=feature`; `data[35:0]={Q,P}` |
| 5 | feature write | `addr[1:0]=feature`; `data[35:0]={Q,P}` |
| 6 | classify | address and data ignored |

The RP2350 console exposes these as `somwrite`, `featwrite`, `classify`, and
`result`. `result` is a two-byte SPI transaction: command `0x01`, then a dummy
byte that receives `{valid,busy,label[1:0],4'b0000}`. UART telemetry currently
returns `{3'b000,label[1:0],best_node[2:0]}` as one byte.

That compact sidecar ABI proves live operation, but it does not yet expose the
runner-up or confidence gap. The v1 demo ABI must add a versioned result frame
before the product exit gate is complete; it must not silently reinterpret the
existing byte.

## Evidence as of 2026-07-16

| Evidence | Status |
|---|---|
| Python exact SOM oracle | PASS, 24 checks |
| C++ oracle parity | PASS |
| VM/RTL fixture trace | PASS |
| Core `SOM`/`SOM_TRAIN` opcode regression | PASS |
| Exact-order adversarial RTL regression | PASS; added after finding the old lexicographic comparator |
| Tang 25K fixed-map BMU probe | silicon PASS, `SOM:P T:2 B:6 E:00` |
| Tang 25K writable-BRAM hydration probe | silicon PASS |
| Tang standalone sidecar SPI/UART path | silicon PASS; SPI `80 A0 B0`, C3 UART `00 14 1E` |
| Artix-7 identical-fixture probe | built and testbench PASS; board run pending |
| Exact-order fixed-schedule comparator at HEAD | testbench/trace PASS; renewed Tang sidecar silicon proof PASS |

The rebuilt Tang sidecar uses 12,786/23,040 LUT4 (55%), 8/56 BSRAM, no DSP,
and closes at 77.61 MHz against its 12 MHz target. Packed bitstream SHA-256:
`8c6b6f8e2cc10f0668761ccb4e178b71499af5ef7c204b8cd47728ecd81c8e0b`.

The 2026-07-16 sidecar run is the renewed HEAD silicon proof after the
exact-order comparator and SPI repairs. It proves the repaired scheduled
datapath on three hydrated winner cases; the negative-surd and adversarial
ordering corpus remains an explicit v1 exit-gate item rather than an implied
claim from these three vectors.

## v1 exit gate

SOM v1 is complete only when all of the following are true:

- one checked-in offline-trained and rationally quantized map is reproducible;
- the map uploader validates dimensions, signed coefficient range, and all 28
  writes for the seven-node product fixture;
- a versioned result frame carries winner, runner-up, label, best distance,
  second distance, gap, ambiguity, and an error/status field;
- one host command performs hydrate -> classify corpus -> compare with oracle;
- ties, negative surd coefficients, the exact-order adversarial case, range
  rejection, and interrupted/partial hydration have explicit tests;
- the exact-order, fixed-434-cycle HEAD passes renewed Tang silicon proof;
- the identical golden corpus passes on Artix-7, establishing cross-vendor
  bit-exact behavior;
- all active SOM tests pass with no archived implementation needed.

## Non-goals for v1

- large-map throughput benchmarking;
- the archived seven-way parallel array;
- temporal PHSLK classification;
- full neighborhood adaptation or proof that the online update is a complete
  Kohonen training algorithm;
- automatic robotics/proprioception coupling.

Robotics integration comes after this contract is closed. It should supply
features through a versioned observation ABI rather than being wired directly
into the BMU datapath.
