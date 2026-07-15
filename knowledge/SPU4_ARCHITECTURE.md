# SPU-4 Sentinel Architecture

**Status:** Silicon-proven (2026-07-08, Tang Primer 25K)  
**Role:** Dual-role Edge Compute and Cluster Satellite  

---

## 1. Overview

The SPU-4 ("Sentinel") is a minimal Euclidean edge core and sensor preprocessor. Unlike the SPU-13, which is a deterministic rational field processor containing a rotating Q(√3) manifold (Davis Gate, Pell Octave, etc.), the SPU-4 focuses on standalone scalar/Euclidean arithmetic or acting as an axis-specific satellite for the SPU-13 governor. 

For full details on how the SPU-4 integrates into the broader spatial statistics hierarchy, see `knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7 ("Deployment Architecture: The Arlinghaus Constellation").

## 2. Dual-Role Deployment

The SPU-4 operates in two distinct modes depending on its synthesis wrapper:

### A. Standalone Edge Node
In standalone mode (`spu4_standalone_top.v`), the SPU-4 operates independently on minimal-fabric FPGA targets (e.g., Tang 20K/25K, iCE40UP5K). It features:
- **Euclidean ALU:** Scalar and basic vector arithmetic without the overhead of the SPU-13's rational field logic.
- **Micro-cell Invariant Checking:** The SPU-4 checks its own local ΣABCD integrity natively, attempting Henosis locally.
- **Resource Envelope:** Approximately 400 LUT4-equivalents (including its UART fixture), easily fitting into commodity edge fabrics.

### B. Cluster Satellite (Meso-cell)
In a larger cluster deployment, SPU-4 cores act as peripheral satellites to an SPU-13 governor (`spu4_top.v` / `spu4_cluster_bridge.v`).
- One Sentinel per manifold axis preprocesses sensory/Euclidean work and reports coherence to the central SPU-13.
- Satellites communicate with the SPU-13 over the `spu4_cluster_bridge`, passing dissonance frames upward rather than raw state, adhering to the principle that only unrecovered deviations propagate.

## 3. RTL Module Map

The core logic resides in `hardware/rtl/core/spu4/`:

- **Core Logic & Sequencing:**
  - `spu4_core.v`, `spu4_top.v`, `spu4_standalone_top.v`: Wrappers and top-level integration.
  - `spu4_sequencer.v`, `spu4_dream_sequencer.v`: Instruction scheduling and sleep/wake management.
  - `spu4_decoder.v`: Minimal ISA decoder for Euclidean and control operations.
  - `spu4_regfile.v`: Core register file.

- **Arithmetic & Intelligence:**
  - `spu4_euclidean_alu.v`: The primary execution unit for standard Euclidean math.
  - `spu4_som_edge.v`: A lightweight 4-node register-backed Self-Organizing Map (SOM) / Best Matching Unit (BMU) classifier tailored for ~400 LUT edge nodes.

- **Interconnect & Communication:**
  - `spu4_cluster_bridge.v`: Handles the framing and signaling between an SPU-4 satellite and an SPU-13 governor.
  - `spu4_sovereign_bus.v`: Defines the mastership protocol for a satellite population.
  - `spu4_boot_master.v`: Orchestrates boot sequencing across the cluster.

## 4. Cluster Bridge Frame Format

The `spu4_cluster_bridge` encodes the hierarchical invariant rules:

* **SPU-4 (Satellite) → SPU-13 (Governor) [16-bit frame]**
  `{ snap_locked[1], dissonance[8], status[7] }`
  *(Note: An extended 24-bit frame with SOM label has also been TB-verified as of 2026-07-09).*
  
* **SPU-13 (Governor) → SPU-4 (Satellite) [32-bit frame]**
  `{ prime_anchor[16], davis_integrity_tag[8], command[8] }`

This asymmetry guarantees the SPU-13 does not micromanage the SPU-4's state; it only receives *dissonance* (the unrecovered Davis ratio) and issues high-level commands downward.

## 5. Hardware Evidence & Test Coverage

The SPU-4 design is highly verified in RTL and silicon. The first standalone silicon proof was achieved on 2026-07-08 (Tang Primer 25K). 

| Component / Subsystem | Verification Level | Reference Testbench |
| --- | --- | --- |
| Standalone Core / Top | **Silicon-verified** (2026-07-08) | `spu4_standalone_top_tb.v` |
| Euclidean ALU | RTL / Formal verification | `spu4_euclidean_alu_tb.v`, `spu4_euclidean_alu_formal.sby` |
| Decoder | RTL | `spu4_decoder_tb.v` |
| Register File | RTL | `spu4_regfile_tb.v` |
| Precession | RTL | `spu4_precession_tb.v` |
| Cluster Bridge | RTL | `spu4_cluster_bridge_tb.v` |
| SOM Edge Node | RTL | `spu4_som_edge_tb.v` |

See `docs/hardware_evidence.md` §3.2j for detailed bitstream records.
