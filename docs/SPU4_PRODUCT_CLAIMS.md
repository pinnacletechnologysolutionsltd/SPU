# SPU-4 Sentinel — Product Claim Ledger (draft)

**Status:** T7.2 working draft — 2026-08-13  
**Product boundary:** reusable FPGA IP block. The Tang Primer 25K image is a
reference-validation vehicle, not the product.

This ledger separates what the SPU-4 can claim from what is still an
integration or productization task. `THEOREM`, `RTL`, and `SILICON` are claim
levels, not marketing adjectives.

| Claim | Level | Evidence / boundary |
|---|---|---|
| Four-axis Quadray datapath with deterministic Euclidean arithmetic | RTL | `hardware/rtl/core/spu4/spu4_core.v`, `spu4_euclidean_alu.v`, decoder, sequencer, and regfile; exercised by the SPU-4 RTL benches. |
| Standalone programmed execution with Quadray result and telemetry ports | RTL | `spu4_standalone_top.v` and `hardware/tests/spu4/spu4_standalone_top_tb.v`. The generic wrapper exposes program load, run/busy/done, A–D result, UART, and status signals. |
| Standalone probe executes the documented QROT path and reports the expected result | SILICON — scoped | Tang Primer 25K probe, 2026-07-08: `SPU4:P A=0000 B=0155 C=0155 D=0155`; build/load details, raw line, and bitstream SHA-256 are in `docs/hardware_evidence.md` §3.2j. This does not prove every opcode or target fabric. |
| Approximately 400 LUT4-equivalents including the UART fixture | Synthesis/P&R estimate | The figure is a resource estimate, not a silicon resource measurement. The exact probe build was rerun on 2026-08-13; its bitstream SHA-256 is `9599f5e420f46515d99b57d2b256489440341166941be3bc9992b0b827222664` and P&R closed at 168.58 MHz against 12 MHz. |
| Fits a customer's target FPGA | OPEN | Requires a target-specific synthesis/P&R report; the ~400-LUT estimate must not be presented as universal across vendors, wrappers, or constraints. |
| Cluster bridge and sovereign-bus integration | RTL/TB only | `spu4_cluster_bridge.v` and related benches exist, but the bridge is not instantiated in a board top and is not covered by the §3.2j silicon result. |
| SPU-4 SOM/BMU edge tier | RTL/TB experiment only | `spu4_som_edge.v` has no upload path, synthesis record, board top, or silicon evidence. It is not part of the base product claim. |
| Cross-vendor bit identity and bounded cycle contract | OPEN | To be specified and tested as product acceptance criteria; no claim is made here yet. |

## Current exclusions

The base SPU-4 claim does not include the cluster bridge, SOM/BMU edge tier,
PSRAM system integration, or cross-vendor timing/resource guarantees. Those are
separate integration packages until their interfaces and evidence are closed.

## Next acceptance work

1. Resolve whether the product wrapper is the minimal `spu4_standalone_top`
   interface or a smaller core-only interface.
2. Define the instruction/latency contract and a target-independent trace
   format.
3. Add a target matrix with independently generated resource and timing
   reports for each supported fabric.
4. Decide the fault-reporting contract together with T7.3; do not advertise
   self-detecting faults while `spu13_axiomatic_gatekeeper` remains outside the
   SPU-4 path.
