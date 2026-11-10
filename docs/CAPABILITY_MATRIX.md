# SPU capability matrix

What exists, and **what kind of evidence** backs it. The five layers are independent: a result in one
does not imply any other. Layer definitions follow the [hardware evidence ledger](hardware_evidence.md#evidence-claim-boundaries)
and the [research identity](RESEARCH_IDENTITY.md). Originally dated 2026-10-20;
the CPU row was reconciled with later ledger entries on 2026-11-05. Each cell is scoped to the cited record.

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
| **HEX-SOM search research** | — | A handover reports fewer evaluations without an established accuracy gain, but the specific experiment and reproduction record have not been located in this checkout. Software validation, efficiency and negative accuracy results cannot yet be independently assessed here. | Not established | Not established | Not established |
| **GPU (T1d rasterizer, depth, VGA)** | Exact reference renderer | Python ideal + finite-width device model (quickstart below); a separate C++ renderer matches byte-for-byte (not yet published) | Yes | Routed Artix-7 builds with tool timing per tranche ([ledger](hardware_evidence.md)); Vivado routed baseline of the standalone VGA image ([note](../hardware/boards/artix7/spu_a7_gpu_vga_vivado_baseline_2026-10-25.md); internal timing only) | First video, first triangle, two-triangle depth ([§3.8–3.10](hardware_evidence.md#38-first-video-output--640x480-vga-on-a-monitor-2026-09-04)); T1G visual switching passed ([§3.37](hardware_evidence.md#337--t1g-two-cycle-visual-acceptance-retry-2026-10-07)); T1H H1 **on hold** ([§3.38](hardware_evidence.md#338--t1h-scalar-diagnostic-visual-replay-2026-10-07)) |
| **Surd CPU** (integrated core) | Frozen Gen-1 machine defined in the [architectural contract](GEN1_ARCHITECTURAL_CONTRACT.md) | Arithmetic accepted for its tested software scope; the C++ `gen1-surd` profile reproduces the seven RTL fixture frames, one RTL-derived fault-after-readback frame and the recorded silicon success frames (software conformance only; [usage](software_guide.md)) | Yes | Packet 06 routed-artifact integrity audit passed, timing unqualified ([§3.39](hardware_evidence.md#339--packet-06-routed-cpu-integrity-audit-2026-10-15)); later H0 UART image routed with tool-reported timing ([§3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc)) | Fixed-program single runs ([§3.40](hardware_evidence.md#340--cpu-board-4c-r1-first-fixed-program-surd-cpu-run-over-uart-2026-10-30), [§3.41](hardware_evidence.md#341--cpu-rom-2b-one-word-rom-variant-operand-variation-over-uart-run-2026-10-30-entry-prepared-2026-10-31), [§3.43](hardware_evidence.md#343--cpu-rom-2c-variant-b-denominator-25-operand-variation-over-uart-2026-10-31), [§3.49](hardware_evidence.md#349--gen1-variant-a-operand-variation-213-of-the-fixed-program-surd-cpu-over-uart-2026-11-06-utc)); 3/3 reloads in one session ([§3.47](hardware_evidence.md#347--gen1-repeat-1-three-independent-reloads-of-the-golden-fixed-program-surd-cpu-image-2026-11-05-utc)); KEY0 restarts ([§3.42](hardware_evidence.md#342--cpu-board-4c-step-b-single-key0-restart-of-the-resident-one-word-image-2026-10-31), [§3.48](hardware_evidence.md#348--gen1-key0-repeat-1-five-key0-restarts-of-the-golden-surd-cpu-image-after-one-load-2026-11-05-utc)) and 15/15 timed-pulse reset recovery, scoped ([§3.52](hardware_evidence.md#352--gen1-reset-edge-1-timed-key0-reset-recovery-of-the-golden-gen-1-image-2026-11-08-utc)); one golden load after a cold power cycle ([§3.51](hardware_evidence.md#351--gen1-power-cycle-1-run-03-golden-gen-1-load-after-a-cold-power-cycle-2026-11-06-utc)), flash boot not established ([§3.50](hardware_evidence.md#350--gen1-power-cycle-1-cold-power-cycle-observed-device-self-configured-from-flash-at-power-on-2026-11-06-utc)). Gen-1 golden image only, single unit; experimental H0: two UART-loaded programs in one session ([§3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc)). Not CPU qualification. |
| **Relational / hex geometry experiments** (PHY-R1–3, REL-1, HEX-C1, GEO-I1, NGW-H1) | Exact equilibrium family and strict-stability argument for rigid struts ([PHY-R3](../research/phy_r3/FINDINGS.md)) | Yes: exact arithmetic, independent oracles, negative controls | Not run | Not run | Not run |
| **Python VM, C++ VM, assembler** | — | Python VM: `spu_vm_test.py` 88 passed, 0 failed in a scoped smoke run (count revision-dependent). The dated [conformance review](isa/ISA_CONFORMANCE_2026-10-10.md) lists supported subsets and tested agreements alongside conflicts and unsupported Surd instructions; no release-wide conformance follows from the smoke run. C++ VM: an explicitly selected `--profile gen1-surd` executes the frozen Gen-1 contract (Surd subset only, conformance suite in the release regression); without `--profile` the legacy VM is unchanged and still rejects Surd opcodes. | — | — | — |
| **RP2350 southbridge** (SPI/SD hydration) | — | Host client library | Not run | — | SPI/SD hydration observed for the recorded setup ([§3.2b](hardware_evidence.md#32b-rp2350-southbridge-write--sd-hydration-proof)); USB/HID/sensors not wired or tested. The later H0 CPU session used onboard CH340 UART ([§3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc)); RP2350 was not required for that session. |

## Known limitations

Read these before relying on any row above.

1. **CPU timing and routing are not qualified.** The board observations above cover specific images and runs, not the CPU's full behavior or timing margins. The earlier OpenXC7 route did not complete in three
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
6. **GPU timing and physical scope.** The standalone VGA Vivado baseline reports internal timing for its specified clocks;
   board-level I/O timing and reset behavior remain unqualified ([baseline note](../hardware/boards/artix7/spu_a7_gpu_vga_vivado_baseline_2026-10-25.md)).
   The T1G result above is bounded operator-observed scene switching, not exact physical pixel verification.

## Reproduce the software layer

```bash
python3 -m venv build/newcomer_venv
build/newcomer_venv/bin/python software/spu_vm_test.py          # ends: N passed, 0 failed / PASS
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/quickstart/device_01
```

The [software quickstart](NEWCOMER_SOFTWARE_QUICKSTART.md) has the full list with expected outputs. Research experiments each carry
their own test command in their `FINDINGS.md`.
