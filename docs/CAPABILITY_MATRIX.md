# SPU capability matrix

What exists, and **what kind of evidence** backs it. The five layers are independent: a result in one
does not imply any other. Layer definitions follow the [hardware evidence ledger](hardware_evidence.md#evidence-claim-boundaries)
and the [research identity](RESEARCH_IDENTITY.md). Dated 2026-10-20; each cell is scoped to the cited record.

| Layer | Meaning | Does **not** establish |
|---|---|---|
| **Math** | A derivation or proof written down in this repository, checked exactly in software where noted | That an implementation matches it |
| **Host software** | Python/C/C++ run on an ordinary computer against an independent oracle | Anything about RTL, timing or boards |
| **RTL simulation** | A named testbench on the Verilog | Synthesis, timing closure, interface wiring, silicon |
| **FPGA synthesis/P&R** | Tool-reported resources and timing for a stated device | A qualified timing result or a working board |
| **Physical hardware** | A ledger entry with the programmed artifact and the observed result | Correctness beyond what was observed |

"Not run" means exactly that. A blank is never a hidden pass.

| Capability | Math | Host software | RTL simulation | FPGA synthesis / P&R | Physical hardware |
|---|---|---|---|---|---|
| **Exact Q(√3) surd arithmetic** (Surd Register, AOR-S1) | Closed-form product/normalization; A₃₁ is an algebra with zero divisors, not a field ([foundations](../knowledge/MATHEMATICAL_FOUNDATIONS.md)) | AOR-S1: 91 operation cases, 29 kernel cases, 26 mutation controls ([introduction](START_HERE.md)) | Testbenches in the regression runner | Padé build completed; 34.80 MHz is a tool estimate, timing **not** qualified | Not run for this arithmetic |
| **Lucas / Z[φ] MAC** | Cyclotomic-Fibonacci oracle ([note](CYCLOTOMIC_FIBONACCI_ORACLE.md)) | Oracle tests (`test_lucas_mac_oracle.py`) | Yes | Builds recorded | Tang 25K and Wukong A7 probes, incl. 200-step zero drift ([§3.2e](hardware_evidence.md#32e-lucas-mac-fast-path-zero-drift-probe)–[§3.2e.7](hardware_evidence.md#32e7-wukong-j11-lucas-200-step-zero-drift-silicon-proof)) |
| **ROTC / IROTC exact rotations** | Rotation catalogs and the icosahedral derivation ([ROTC](../knowledge/rotc_tables.md), [IROTC](IROTC_SPEC.md)) | VM/RTL trace equivalence tests | Yes | Builds recorded | ROTC angles 0–5 ([§3.2g](hardware_evidence.md#32g-rotc-0-5-silicon-probe)); IROTC engine and conjugate catalog on Tang 25K ([§3.2k](hardware_evidence.md#32k-irotc-icosahedral-rotation-engine-silicon-probe), [§3.2k.1](hardware_evidence.md#32k1-irotc-spi-core-integration--conjugate-catalog-silicon-proof)) |
| **SPU-4 Sentinel edge node** | — | Python/C++ oracles | Yes | Builds recorded | Standalone core, ABI v1.1 and edge-node SOM on Tang 25K ([§3.2j](hardware_evidence.md#32j-spu-4-sentinel-standalone-silicon-probe)) |
| **SOM v1 classifier** (7 nodes, 4 features) | Exact surd ordering; full-domain arithmetic bounds derived ([SOM-RP0a](../research/som_rp0/FINDINGS.md)) | Python oracle; exact portable C99 BMU over the **full** signed-18-bit domain (host-only; Cortex-M33 compile-only) | Yes, incl. an exact-order adversarial case | Tang sidecar: 12,865/23,040 LUT4, 79.38 MHz vs 50 MHz clock (tool output) | Iris map: 150/150 FPGA winners equal the oracle on Tang 25K and Wukong A7 ([§3.2g.4–3.2g.6](hardware_evidence.md#32g4-reproducible-iris-som-corpus-silicon-proof)) — **inside the RTL-safe input region only**; see [limitations](#known-limitations) |
| **GPU (T1d rasterizer, depth, VGA)** | Exact reference renderer | Python ideal + finite-width device model (quickstart below); a separate C++ renderer matches byte-for-byte (not yet published) | Yes | Routed Artix-7 builds with tool timing per tranche ([ledger](hardware_evidence.md)); Vivado routed baseline of the standalone VGA image ([note](../hardware/boards/artix7/spu_a7_gpu_vga_vivado_baseline_2026-10-25.md); internal timing only) | First video, first triangle, two-triangle depth ([§3.8–3.10](hardware_evidence.md#38-first-video-output--640x480-vga-on-a-monitor-2026-09-04)); T1G visual switching passed ([§3.37](hardware_evidence.md#337--t1g-two-cycle-visual-acceptance-retry-2026-10-07)); T1H H1 **on hold** ([§3.38](hardware_evidence.md#338--t1h-scalar-diagnostic-visual-replay-2026-10-07)) |
| **Surd CPU** (integrated core) | — | Arithmetic accepted for its tested software scope | Yes | Placement audit passed (52,090 cells, 80 DSPs); one routed artifact passed an integrity audit with timing **unqualified** ([§3.39](hardware_evidence.md#339--packet-06-routed-cpu-integrity-audit-2026-10-15)); OpenXC7 routing did not finish in three bounded attempts | **Not run** |
| **Relational / hex geometry experiments** (PHY-R1–3, REL-1, HEX-C1, GEO-I1, NGW-H1) | Exact equilibrium family and strict-stability argument for rigid struts ([PHY-R3](../research/phy_r3/FINDINGS.md)) | Yes: exact arithmetic, independent oracles, negative controls | Not run | Not run | Not run |
| **Python VM, C++ VM, assembler** | — | Python VM: `spu_vm_test.py` 88 passed, 0 failed on the integration branch (the count is revision-dependent); C++ VM is a bounded subset ([conformance](isa/ISA_CONFORMANCE_2026-10-10.md)) | — | — | — |
| **RP2350 southbridge** (SPI/SD hydration) | — | Host client library | Not run | — | SPI/SD hydration verified ([§3.2b](hardware_evidence.md#32b-rp2350-southbridge-write--sd-hydration-proof)); USB/HID/sensors not wired or tested |

## Known limitations

Read these before relying on any row above.

1. **CPU timing and routing are not qualified.** The Surd CPU has no board result. Its OpenXC7 route did not complete in three
   bounded attempts (3 × 3,600 s, all timeouts); a routed artifact from a different backend passed an integrity audit, but its
   40.886 MHz figure is an unqualified tool estimate and 25 MHz is not established. A separate Vivado routed run of the Base CPU profile was made on another machine; its report has not yet been recovered into this repository, so this matrix claims no Base CPU figures ([RTL identity](../hardware/boards/artix7/spu_a7_surd_cpu_base_rtl_identity_2026-10-26.md)). A router-policy study
   ([ROUTE-ALG-1–3](../research/route_alg3/FINDINGS.md)) found no benefit from reopening the search and says nothing about why the CPU does not finish.
2. **SOM RTL arithmetic defect.** For inputs the uploader accepts, `spu_som_bmu.v` can return wrong distances without a flag
   (the difference field is 18-bit, terms are 36-bit, the P field is unsigned 32-bit). The Iris evidence lies inside the safe region.
   The exact C99 BMU in [SOM-RP0a](../research/som_rp0/FINDINGS.md) is the reference and returns `RTL_UNSAFE` where the current RTL cannot
   be trusted; the defect is tracked in a [repair backlog](../research/som_rp0/RTL_REPAIR_BACKLOG.md). **No RTL repair exists.**
3. **Negative memory-layout result (NGW-H1).** In a model-only cache simulation, a hierarchical aperture-7 layout never beat dense
   axial addressing overall, subtree weighting helped only hierarchical descent, and adaptive weighting did not improve on LRU/LFU
   ([findings](../research/ngw_h1/FINDINGS.md)). Not a hardware or speed claim.
4. **Relational/hex geometry is experimental.** Hierarchical certified queries used fewer exact *tests* in bounded fixtures
   (HEX-C1, GEO-I1) but the counts are not runtimes, weights are declared constants, and no optimized BVH was compared. The relational
   backend used about 1.3× more scalar operations than a coordinate backend while storing less state (REL-1). It decides some states a
   rational-coordinate backend cannot materialize; that is a representation property, not a performance result.
5. **Software scope.** The Python `spu-sim` entry point is a legacy VM; the C++ VM covers a bounded subset; the standalone SIM-1
   simulator lives in a separate repository that is not yet published. Software results are not hardware results.

## Reproduce the software layer

```bash
python3 -m venv build/newcomer_venv
build/newcomer_venv/bin/python software/spu_vm_test.py          # ends: N passed, 0 failed / PASS
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/quickstart/device_01
```

The [software quickstart](NEWCOMER_SOFTWARE_QUICKSTART.md) has the full list with expected outputs. Research experiments each carry
their own test command in their `FINDINGS.md`.
