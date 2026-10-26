# SPU-4 Sentinel — Product Claim Ledger (draft)

**Status:** T7.3 contract attached — 2026-08-13
**Product boundary:** reusable FPGA IP block. The Tang Primer 25K image is a
reference-validation vehicle, not the product.

This ledger separates what the SPU-4 can claim from what is still an
integration or productization task. `THEOREM`, `RTL`, and `SILICON` are claim
levels, not marketing adjectives.

| Claim | Level | Evidence / boundary |
|---|---|---|
| Four-axis Quadray datapath with deterministic Euclidean arithmetic | RTL | `hardware/rtl/core/spu4/spu4_core.v`, `spu4_euclidean_alu.v`, decoder, sequencer, and regfile; exercised by the SPU-4 RTL benches. |
| **Customer integration interface (ABI v1.0)** | RTL | `spu4_customer_wrapper.v`, frozen 2026-08-16, contract in `docs/SPU4_ABI.md`, asserted by `hardware/tests/spu4/spu4_customer_wrapper_tb.v` (19 checks). **This is the interface a customer integrates against.** |
| Standalone programmed execution with Quadray result and telemetry ports | RTL — **bring-up vehicle, NOT the product interface** | `spu4_standalone_top.v` and `hardware/tests/spu4/spu4_standalone_top_tb.v`. Corrected 2026-08-16: this module was previously named here as the product interface, which was wrong on evidence. Its `uart_tx` and `node_tx[31:0]` are declared outputs with **no drivers at all** (both read `z`, verified in simulation), its register-file read ports are dangling so the programmable path is not closed, and `sentinel_mode`/`piranha_pulse` are research-era concepts. It remains the correct bring-up and probe vehicle. See `docs/SPU4_ABI.md` §1. |
| Standalone probe executes the documented QROT path and reports the expected result | SILICON — scoped | Tang Primer 25K probe, 2026-07-08: `SPU4:P A=0000 B=0155 C=0155 D=0155`; build/load details, raw line, and bitstream SHA-256 are in `docs/hardware_evidence.md` §3.2j. This does not prove every opcode or target fabric. |
| 835 LUT4, 390 ALU, 336 DFF on GW5A-25A including the UART probe fixture | Synthesis/P&R measurement, one fabric | Re-derived from the nextpnr-himbaechel utilisation report on 2026-08-14 (`bash build_25k_spu4_probe.sh`); Yosys pre-pack reports 445 LUT1–4 / 356 ALU. Not a silicon resource measurement. The build is bit-reproducible: bitstream SHA-256 `9599f5e420f46515d99b57d2b256489440341166941be3bc9992b0b827222664`, independently regenerated 2026-08-14, P&R closing at 168.58 MHz against 12 MHz. Supersedes an earlier "~400 LUT4-equivalents" figure that understated the build by roughly 2×. |
| Defined base fault/telemetry contract | RTL contract | `docs/SPU4_FAULT_REPORTING_CONTRACT.md`; the base core reports completion, normalization events, and residual telemetry, not comprehensive self-fault detection. |
| Fits a customer's target FPGA | OPEN | Requires a target-specific synthesis/P&R report. The GW5A-25A figures above must not be presented as universal across vendors, wrappers, or constraints. Specifically withdrawn: the claim that the core fits a Gowin GW1N-1 "with room to spare" — 835 LUT4 + 390 ALU exceeds that part's 1152 LUT4 slots, since Gowin ALU cells occupy LUT positions. iCE40UP5K is plausible on headroom but unverified. |
| Cluster bridge and sovereign-bus integration | RTL/TB only | `spu4_cluster_bridge.v` and related benches exist, but the bridge is not instantiated in a board top and is not covered by the §3.2j silicon result. |
| SPU-4 SOM/BMU edge tier | RTL/TB experiment only | `spu4_som_edge.v` has no upload path, synthesis record, board top, or silicon evidence. It is not part of the base product claim. |
| Bounded cycle contract | **SILICON — scoped** | Bounded, **not fixed**: contract bound **200 clocks**, simulation 180–183 over 124 operations, and **183 measured on Tang 25K silicon** via `spu4_abi_probe`, 10/10 loads (`hardware_evidence.md` §3.2j.3). Latency varies with operand values because the multiplier is serial. Scoped: one operand fixture, one board, one session — it does not probe the ABI's full input range. `docs/SPU4_ABI.md` §4. |
| Cross-vendor bit identity | OPEN | To be specified and tested as product acceptance criteria; no claim is made here yet. |

## Current exclusions

The base SPU-4 claim does not include the cluster bridge, SOM/BMU edge tier,
PSRAM system integration, or cross-vendor timing/resource guarantees. Those are
separate integration packages until their interfaces and evidence are closed.

## Next acceptance work

1. ~~Resolve whether the product wrapper is the minimal `spu4_standalone_top`
   interface or a smaller core-only interface.~~ **RESOLVED 2026-08-16:**
   neither. `spu4_customer_wrapper` is a new, smaller, single-operation
   interface; `spu4_standalone_top` is retained as the bring-up vehicle. The
   programmable path was excluded because it is not closed — see
   `docs/SPU4_ABI.md` §1.
2. ~~Define the latency contract.~~ **DONE 2026-08-16** (bounded, 200 clocks,
   see the table above). **Still open:** a target-independent trace format.
3. Add a target matrix with independently generated resource and timing
   reports for each supported fabric.
4. Treat hardened fault detection as a separate optional package; do not
   advertise self-detecting faults for the base core.
