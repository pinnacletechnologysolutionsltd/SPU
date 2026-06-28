# SPU-13 as a Quantum Error Correction Co-Processor

**Date:** 2026-06-28 18:11 NZST
**Status:** Parked strategic opportunity
**Relevance:** Future deployment; not on the current southbridge bring-up critical path

**Decision:** Keep this as a use-case note and revisit after RP2350 southbridge,
SD hydration, and RPLU v2 table consumption are proven in hardware.

---

## Executive Summary

The SPU-13 Rational Manifold Engine is a plausible research fit for the
**classical decoding bottleneck** in real-time quantum error correction (QEC):
syndrome bits must be reduced into correction decisions with strict latency,
bounded jitter, and predictable resource use. SPU-13's useful angle is not that
it is the only path to sub-microsecond QEC. Current FPGA/RFSoC work already
reports sub-microsecond decode-feedback paths. The opportunity is narrower and
more defensible: a lean, deterministic, symbolic co-processor that can explore
code-family-adaptable decoders without inheriting a general CPU/GPU runtime.

This is a future application thesis. It should not consume bench time until the
basic FPGA/RP2350/SD/RPLU bring-up path is stable.

---

## The Problem: Quantum Decoding Bottleneck

### Current State (2026)
When running a fault-tolerant quantum processor (superconducting, photonic, trapped-ion):
- **Coherence window:** ~1.25 µs (superconducting), ~10 µs (trapped-ion)
- **QEC cycle:** Measure syndrome → Decode error → Apply correction → repeat
- **Typical hard target:** Full decode + feedback in **< 1 µs** for fast
  superconducting control loops

### Why This Matters
If classical decoding and feedback cannot keep up with syndrome measurement,
errors accumulate faster than correction can remove them. Classical control
latency becomes part of the quantum error budget.

### Current Industry Approaches
| Approach | Latency | Limitation |
|---|---|---|
| Generic CPU (Xeon, EPYC) | 10–100 µs | Cache misses, context switching |
| FPGA/RFSoC decoders | sub-us reported for small/current demos | tight coupling to code/control stack |
| Neural-network decoders on FPGA | sub-us reported | training/robustness/verification burden |
| Custom ASIC/controller blocks | potentially lowest latency | code and hardware lock-in risk |

Recent examples worth tracking:
- FPGA neural-network surface-code decoder: reported deterministic closed-loop
  latency of 550 ns, including 124 ns decoding, for distance-3 superconducting
  QEC: https://arxiv.org/abs/2605.04892
- RFSoC open-source integrated QEC system: reported 446 ns end-to-end
  decode-feedback latency for distance-3 surface code: https://arxiv.org/abs/2603.16203
- FPGA quantum-LDPC/GARI decoder: reported 596 ns average latency per decoding
  round for a [[144,12,12]] bivariate bicycle code case study:
  https://arxiv.org/abs/2605.01035

---

## Why SPU-13 is the Right Match

### 1. Deterministic Execution as a Design Constraint

**Current Architecture Advantage:**
```
RP2350B PIO (cycle-accurate)
    ↓ [DMA, zero-jitter streaming]
Dedicated QEC ingress path (future, not current SPI)
    ↓ [atomic snapshot or syndrome frame latch]
FPGA local fabric / BRAM / PSRAM bridge
    ↓ [bounded arbitration]
RPLU 2.0 (Fibonacci-gated dispatch)
    ↓ [deterministic latency per opcode]
Correction output latch / controller feedback
```

Why this works:
- RP2350B's **PIO state machines** eliminate OS jitter entirely
- **Fibonacci-gated sequencer** means every instruction dispatch is predictable (not data-dependent)
- **Atomic manifold snapshots** at Southbridge level eliminate race conditions
- No cache hierarchy, no branch prediction → zero timing side-channels

Critical caveat: the current 2 MHz SPI southbridge is for bring-up, telemetry,
and table hydration. It is not a QEC feedback-loop transport. A QEC variant
would need a different ingress/egress path: direct parallel GPIO, PIO/DMA lanes,
LVDS/SerDes, RFSoC integration, or a tightly coupled controller fabric.

### 2. Native Field Arithmetic for Syndrome Decoding

Quantum error syndromes are **inherently symbolic**, not numeric:
- Bit-flip syndrome: `s_x ∈ {0,1}^n` (which qubits flipped?)
- Phase-flip syndrome: `s_z ∈ {0,1}^n` (which qubits dephased?)
- **Bosonic codes** (cat, binomial kitten): photon-number parity → mod-2 arithmetic in high dimensions

**SPU-13's Advantage:**
```
Standard FPGA approach:
  Syndrome string → massive lookup tables → binary logic → output
  Problem: O(2^n) states, unpredictable routing latency

SPU-13 approach:
  Syndrome pattern → symbolic reduction in Q(√3,√5,√15)
  → F_{p^4} field collapse → direct parity equation solve
  Problem: O(n) symbolic operations, deterministic latency
```

The **RPLU 2.0's F_{p^4} arithmetic** (M31 multiplier, conjugate-reduction inverter) is precisely what you need to:
- Collapse high-dimensional error spaces
- Evaluate parity constraints in non-binary fields (bosonic codes)
- Explore deterministic syndrome-equation transforms without large lookup-table
  scans

### 3. Lean Architecture = No Wasted Cycles

| Component | Generic FPGA | SPU-13 |
|---|---|---|
| Instruction fetch | Multistage, data-dependent | Fibonacci-gated, known latency |
| Memory access | Shared SDRAM arbiter | Dedicated PSRAM bridge |
| DSP utilization | Sparse (high fan-out overhead) | 16-lane M31 multiplier (tight packing) |
| Total per-cycle power | 50–200W | 5–15W estimated |

**Research thesis:** SPU-13 may offer a useful power/latency/adaptability point
for symbolic or field-based decoders, especially where deterministic behavior is
easier to certify than learned or heavily heuristic decoders.

---

## Technical Fit: Syndrome Decoding as RPLU Operation

### Bosonic Code Example (Cat Code)

In a **cat code**, qubits are encoded in photon-number parity:
```
|ψ⟩ = (|α⟩ + |-α⟩) / √2   [two coherent states]
```

Error syndromes include:
- **Photon-number parity:** (-1)^n_photons
- **Multi-mode correlations:** Parity over subsets of modes
- **Non-local checks:** Requires evaluating symmetric polynomials

**SPU-13 Mapping:**
1. **Syndrome input:** RP2350B reads quantum measurement (ADC or detector array)
2. **DMA stream:** Syndromes → PSRAM via Southbridge
3. **RPLU operation:**
   - BTU layer (spatial routing) → group syndrome bits by error class
   - F_{p^4} arithmetic → evaluate parity polynomials over bosonic basis
   - Thimble-Padé approximant → solve for most-likely error
4. **Output:** Correction pulse parameters → RP2350B feedback loop

**Latency budget target:** sub-microsecond end-to-end on future hardware. Tang
25K is suitable for proof-of-concept algorithm validation, not for claiming a
production QEC feedback loop.

### Surface Code Example (Superconducting)

For **surface codes** on superconducting qubits:
- Syndrome: 2D array of parity checks (X and Z stabilizers)
- Classical problem: 2D Minimum-Weight Perfect Matching (MWPM)
- Standard approach: Blossom algorithm (~1–10 µs on CPU)

**SPU-13 Advantage:**
- Treat 2D syndrome grid as a **symbolic graph reduction problem**
- Use BTU spatial routing to map lattice neighbors directly
- F_{p^4} field operations handle graph weights naturally
- Target deterministic latency after a dedicated QEC ingress/egress path exists

---

## Resource Requirements (Rough Estimate)

### Modifications to Current SPU-13
| Component | Current | QEC Variant | Delta |
|---|---|---|---|
| M31 multiplier | 16 DSP48E1 | 16 DSP48E1 | — |
| F_{p^4} inverter | 76 cycles | 40 cycles (optimized) | –52% latency |
| Syndrome input FIFO | — | 128 × 32-bit | +2 BRAM |
| Correction output latch | — | 64-bit pulse params | +0.5 BRAM |
| Total LUT overhead | — | ~500 LUTs | — |

**On Tang 25K:** This is not a free add-on at the current near-full utilization.
Use Tang 25K only for a stripped proof-of-concept. A credible QEC variant belongs
on a larger FPGA or controller platform after the core architecture is validated.

---

## Validation Roadmap

### Phase 0: Parked Until Bring-Up Is Done
- [ ] Finish RP2350 southbridge read/write bring-up
- [ ] Prove SD-card hydration independently
- [ ] Prove RPLU v2 table consumption path
- [ ] Capture stable latency numbers for existing SPI and core operations

### Phase 1: Proof of Concept (After Bring-Up)
- [ ] Implement `software/lib/rational_qec_decoder.py`
- [ ] Simulate 3-bit repetition code and 5/7-qubit stabilizer examples
- [ ] Define a minimal syndrome-to-equation representation that maps cleanly to
      RPLU/BTU primitives
- [ ] Compare against a conventional software decoder on identical syndrome sets

### Phase 2: Hardware Kernel Study
- [ ] Implement only the deterministic reduction kernel in RTL
- [ ] Measure kernel latency on Tang 25K or Wukong, separate from transport
- [ ] Identify the required non-SPI QEC ingress/egress interface
- [ ] Decide whether the kernel still looks useful after honest I/O accounting

### Phase 3: Scalability Study
- [ ] Extend to 5-qubit and 7-qubit codes
- [ ] Benchmark against Blossom algorithm (MWPM)
- [ ] Characterize F_{p^4} field collapse efficiency
- [ ] Write research note for quantum computing community

### Phase 4: Hardware Integration (Contingent on external collaboration)
- [ ] Partner with quantum lab (e.g., Delft, Jiuzhang, IBM)
- [ ] Design FPGA → quantum controller bridge
- [ ] Implement real syndrome data ingestion
- [ ] Measure end-to-end QEC cycle latency on hardware

---

## Competitive Landscape

**Who is solving this problem now?**
- RFSoC and FPGA control-stack groups targeting closed-loop superconducting QEC.
- FPGA neural-network and graph/message-passing decoder researchers.
- Quantum hardware companies with custom controller and decoder blocks.
- Trapped-ion teams with more relaxed cycle timing but still serious control
  complexity.

**SPU-13 possible advantage:** deterministic symbolic computation in a small
resource envelope, with a path toward code-family-adaptable kernels if the
RPLU/BTU mapping proves real.

---

## Open Questions for Research

1. **Can F_{p^4} field collapse handle all modern codes?**
   - Bosonic codes: Yes (photon parity is inherently mod-2 algebra)
   - Surface codes: Likely (MWPM is graph-theory, fits symbolic reduction)
   - Stabilizer codes (general): Needs investigation

2. **What is the latency limit?**
   - Unknown until a kernel exists and transport is separated from compute
   - Current SPI southbridge cannot be used as the QEC critical path

3. **Can we adapt the BTU collision resolver for error decoding?**
   - BTU currently selects Kohonen BMU from 7 nodes
   - Error decoder needs to find minimum-weight error from 2^n candidates
   - Novel application of hardware that might significantly reduce complexity

4. **Is determinism achievable across all code families?**
   - Challenge: Some codes require adaptive thresholding based on error statistics
   - Opportunity: Hard-code threshold tables in BRAM, lookup in <1 cycle

---

## Conclusion

The SPU-13 Rational Manifold Engine was designed for lean, deterministic
symbolic computation. Quantum error correction decoding is a plausible and
interesting future application, but it must earn its place with small, testable
decoder kernels and honest end-to-end latency accounting.

If pursued seriously, this could position the SPU project at the intersection of:
- **Hardware architecture innovation** (field-based computing)
- **Quantum systems scaling** (fault tolerance bottleneck elimination)
- **Real-time embedded systems** (deterministic sub-microsecond loops)

For now, the right move is to finish bring-up. More use cases will emerge once
SPU-13 is a working object that people can test, abuse, and repurpose.

---

## Files to Update When Pursuing This

- `docs/QUANTUM_ERROR_CORRECTION_APPLICATIONS.md` (this parking-lot note)
- `knowledge/isa_reference.md` (add QEC-specific opcode templates)
- `software/lib/rational_qec_decoder.py` (proof-of-concept decoder)
- `hardware/tests/qec_simulator_tb.v` (QEC testbench suite)
