# SPU capability matrix

What exists, and **what kind of evidence** backs it. The five layers are independent: a result in one
does not imply any other. The physical-hardware layer is defined by the [hardware evidence ledger](hardware_evidence.md).
Dated 2026-10-20; each cell is scoped to the cited record.

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
| **Exact Q(√3) surd arithmetic** (Surd Register, AOR-S1) | Closed-form product/normalization; A₃₁ is an algebra with zero divisors, not a field ([foundations](../knowledge/MATHEMATICAL_FOUNDATIONS.md)) | AOR-S1 software qualification complete ([introduction](START_HERE.md)) | Testbenches in the regression runner | Padé build completed; 34.80 MHz is a tool estimate, timing **not** qualified | Not run for this arithmetic |
| **Lucas / Z[φ] MAC** | Cyclotomic-Fibonacci oracle ([note](CYCLOTOMIC_FIBONACCI_ORACLE.md)) | Oracle tests (`test_lucas_mac_oracle.py`) | Yes | Builds recorded | Tang 25K and Wukong A7 probes, incl. 200-step zero drift ([§3.2e](hardware_evidence.md#32e-lucas-mac-fast-path-zero-drift-probe)–[§3.2e.7](hardware_evidence.md#32e7-wukong-j11-lucas-200-step-zero-drift-silicon-proof)) |
| **ROTC / IROTC exact rotations** | Rotation catalogs and the icosahedral derivation ([ROTC](../knowledge/rotc_tables.md), [IROTC](IROTC_SPEC.md)) | VM/RTL trace equivalence tests | Yes | Builds recorded | ROTC angles 0–5 ([§3.2g](hardware_evidence.md#32g-rotc-0-5-silicon-probe)); IROTC engine and conjugate catalog on Tang 25K ([§3.2k](hardware_evidence.md#32k-irotc-icosahedral-rotation-engine-silicon-probe), [§3.2k.1](hardware_evidence.md#32k1-irotc-spi-core-integration--conjugate-catalog-silicon-proof)) |
| **SPU-4 Sentinel edge node** | — | Python/C++ oracles | Yes | Builds recorded | Standalone core, ABI v1.1 and edge-node SOM on Tang 25K ([§3.2j](hardware_evidence.md#32j-spu-4-sentinel-standalone-silicon-probe)) |
| **SOM v1 classifier** (7 nodes, 4 features) | Exact surd ordering ([contract](SOM_V1_PRODUCT_CONTRACT.md)) | Python oracle; an exact portable C reference over the full signed-18-bit domain exists (not in this release) | Yes, incl. an exact-order adversarial case | Tang sidecar resources and timing in the [contract](SOM_V1_PRODUCT_CONTRACT.md) (tool output) | Iris map: 150/150 FPGA winners equal the oracle on Tang 25K and Wukong A7 ([§3.2g.4](hardware_evidence.md#32g4-reproducible-iris-som-corpus-silicon-proof)–[§3.2g.6](hardware_evidence.md#32g6-cross-vendor-som1-replay-on-wukong-artix-7)), **inside the RTL-safe input region only**; see [limitations](#known-limitations) |
| **GPU (T1d rasterizer, depth, VGA)** | Exact reference renderer | Python ideal + finite-width device model ([quickstart](NEWCOMER_SOFTWARE_QUICKSTART.md)) | Yes | Routed Artix-7 builds with tool timing ([ledger](hardware_evidence.md)) | First video, first triangle, two-triangle depth ([§3.8](hardware_evidence.md#38-first-video-output--640x480-vga-on-a-monitor-2026-09-04), [§3.9](hardware_evidence.md#39-first-rasterized-geometry--gpu-triangle-on-a-monitor-2026-09-05), [§3.10](hardware_evidence.md#310-first-depth-resolved-image--two-triangles-on-a-monitor-2026-09-06)); later scene-update tranches are recorded separately |
| **Surd CPU** (integrated core) | — | Arithmetic accepted for its tested software scope | Yes | Placement audit passed; routing and timing **not** qualified ([introduction](START_HERE.md)) | **Not run** |
| **Relational / hex geometry experiments** | Exact equilibrium and stability arguments for rigid structures | Exact arithmetic with independent oracles | Not run | Not run | Not run |
| **Python VM, C++ VM, assembler** | — | Python VM tests ([software guide](software_guide.md)); the C++ VM is a bounded subset | — | — | — |
| **RP2350 southbridge** (SPI/SD hydration) | — | Host client library | Not run | — | SPI/SD hydration verified ([§3.2b](hardware_evidence.md#32b-rp2350-southbridge-write--sd-hydration-proof)); USB/HID/sensors not wired or tested |

## Known limitations

Read these before relying on any row above.

1. **CPU timing and routing are not qualified.** The Surd CPU has no board result. Its placement passed an audit; routing and 25 MHz timing
   are not qualified, and no tool-reported frequency should be read as a timing result.
2. **SOM RTL arithmetic defect.** For inputs the uploader accepts, `spu_som_bmu.v` can return wrong distances without a flag
   (the difference field is 18-bit, terms are 36-bit, the P field is unsigned 32-bit). The Iris evidence lies inside the safe region.
   An exact portable C reference detects the unsafe cases; it is not part of this release. **No RTL repair exists.**
3. **Negative memory-layout result.** In a model-only cache simulation, a hierarchical aperture-7 layout never beat dense
   axial addressing overall, subtree weighting helped only hierarchical descent, and adaptive weighting did not improve on LRU/LFU.
   Not a hardware or speed claim.
4. **Relational/hex geometry is experimental.** Hierarchical certified queries used fewer exact *tests* in bounded fixtures, but the
   counts are not runtimes, weights are declared constants, and no optimized BVH was compared. A relational backend used about 1.3× more
   scalar operations than a coordinate backend while storing less state; it decides some states a rational-coordinate backend cannot
   materialize, which is a representation property, not a performance result.
5. **Software scope.** The Python `spu-sim` entry point is a legacy VM and the C++ VM covers a bounded subset. Software results are not hardware results.

## Reproduce the software layer

```bash
python3 -m venv build/newcomer_venv
build/newcomer_venv/bin/python software/spu_vm_test.py          # ends: N passed, 0 failed / PASS
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/quickstart/device_01
```

The [software quickstart](NEWCOMER_SOFTWARE_QUICKSTART.md) has the full list with expected outputs.
