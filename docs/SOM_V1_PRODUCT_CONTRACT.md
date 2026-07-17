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
| Reproducible Iris map/demo | `software/models/iris_som_v1.json`, `tools/iris_som_demo.py` |
| Host console and validated uploader | `hardware/rp_common/spu_diag.c`, `tools/upload_som_weights.py`, `tools/som_map.py` |
| Versioned evidence ABI | `docs/SOM1_RESULT_FRAME.md`, `spu13_som1_frame.v`, `software/spu_host/som1.py` |

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
- The four `r_j` feature weights are part of the checksummed map artifact.
  The Iris v1 map uses four exact unit weights.
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

The RP2350 console exposes these as `somwrite`, `somlabel`, `featwrite`,
`classify`, `result`, and `som1`. `result` is a two-byte SPI transaction:
command `0x01`, then a dummy
byte that receives `{valid,busy,label[1:0],4'b0000}`. UART telemetry currently
returns `{3'b000,label[1:0],best_node[2:0]}` as one byte.

`somlabel` uses `sel=7` to hydrate the seven semantic labels owned by the map.
The fixed 52-byte `SOM1` frame is read with sidecar-local SPI command `0x02` and
contains winner, runner-up, semantic label, exact distances, gap, ambiguity,
map/result generations, status, error, and CRC-32. The exact layout is
`docs/SOM1_RESULT_FRAME.md`. It is additive and does not reinterpret the
existing compact byte.

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
| Reproducible seven-node Iris map | PASS; checked JSON equals deterministic regeneration |
| Iris corpus on Tang sidecar | silicon PASS; 150/150 FPGA winners equal oracle, 147/150 labels correct |
| Artix-7 identical-fixture probe | built and testbench PASS; board run pending |
| Exact-order fixed-schedule comparator at HEAD | testbench/trace PASS; renewed Tang sidecar silicon proof PASS |
| SOM1 result encoder/SPI/host parser | RTL + malformed-frame host tests + renewed Tang build PASS; silicon replay pending |

The corpus-proven Tang sidecar uses 12,865/23,040 LUT4 (55%), 1,576 DFF,
1,192 ALU, 8/56 BSRAM, and no DSP. It closes at 79.38 MHz against the real
50 MHz board clock. Packed bitstream SHA-256:
`946574dc25ad7aada168f9f06af101cd0df747230c0fea0ca9dae0ad5d9e7c3c`.

The one-command proof is:

```
python3 tools/iris_som_demo.py --hardware
```

It validates/regenerates the checked map, performs all 28 prototype writes and
seven semantic-label writes,
classifies all 150 checked-in Iris samples, requires every FPGA winner to equal
the exact software oracle, and prints the oracle and FPGA confusion matrices.
Map SHA-256:
`3373e851c29450e37fca76281f9ea4dbbdf1b94b34cf1b7bd74f6d83fe8eaa15`;
dataset SHA-256:
`6f608b71a7317216319b4d27b4d9bc84e6abd734eda7872b71a458569e2656c0`.

The full corpus exposed a board-top packing error that the earlier three-vector
smoke test did not: `{F3,F2,F1,F0}` had been initialized as `{1,1,1,2}` while
the comment and oracle specified uniform weights. Iris sample 101 selected node
2 in silicon instead of oracle node 1, exactly as the unintended feature-0
weight of 2 predicts. The top now uses `{1,1,1,1}`; a dedicated RTL vector
changes winner if feature 0 is ever doubled again.

The compact sidecar still returns its legacy fixed raw-label LUT as compatibility
telemetry. The SOM1 tranche adds seven semantic-label hydration records and
returns the selected map-owned label in the evidence frame. This new path is
simulation/host and Tang-build verified and awaits renewed silicon evidence.

## v1 exit gate

SOM v1 is complete only when all of the following are true:

- one checked-in offline-trained and rationally quantized map is reproducible;
- the map uploader validates dimensions, metric weights, signed coefficient
  range, checksum, all 28 prototype writes, and all seven semantic-label writes
  for the seven-node product fixture;
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

## General CSV trainer

The hardware-independent dataset entry point is now
`tools/train_som_csv.py`; its exact input, quantization, schedule, and artifact
rules are documented in `docs/SOM_CSV_TRAINER.md`. It accepts a labeled CSV,
selects exactly four feature columns, trains the seven-node product map, writes
a checksummed artifact, and reload-validates it before reporting success. The
shared trainer reproduces the checked Iris artifact and map SHA-256 bit for bit.

## Synthetic sensor replay

`tools/som_sensor_replay.py` now closes the hardware-independent anomaly path:
deterministic 100 Hz integer current traces become four temporal features,
cross the Cartesian scalar boundary and explicit SOM18 widening adapter, enter
the exact BMU, and emerge as parsed `SOM1` frames. The checked holdout result is
18/18 semantic labels with zero ambiguity. This is a synthetic ABI proof only;
physical INA226 acquisition and renewed Tang corpus evidence remain open. See
`docs/SOM_SENSOR_REPLAY.md` for the equations, hashes, and commands.
