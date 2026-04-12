RPLU (Rational Power-Law Unit) specification

Purpose
-------
The RPLU is a dedicated, pipelined RTL unit that evaluates the Morse potential (and its gradient) for a Quadray Delta and a material identity (De,a,re) stored in the Sovereign Identity Cache (SIC). It must be fixed-point (no floating) and deterministic, suitable for Tang Primer 25K prototyping.

High-level pipeline
-------------------
Stages (latency budget ~8 cycles, parameterizable):
1) Input capture & ΔQ compute
   - Accept inputs: two nodes as RationalSurd pairs (P,Q) or precomputed Quadrance Q (surd form).
   - Compute ΔQ (difference) and map to internal normalized r (scaled to fixed-point).
2) SIC lookup
   - Issue read of material constants (De,a,re) indexed by material ID.
   - Bring 32-bit/64-bit P/Q fields into pipeline; hold in register file.
3) Spread / lookup
   - Use Rational Sine / Spread ROM (4096 entries Q32) to produce base spread s for the phase derived from normalized r or quadrance.
4) Morse approximation
   - Compute e_term = exp(-a*(r-re)). Implement as: small ROM for exp(-x) (e.g., 256 entries) + multiply-add chain or a 2-term Taylor correction.
   - Compute V = De * (1 - e_term)^2 and dV/dr (force) if needed.
   - All arithmetic in fixed-point surd basis: P/Q fields for values that require sqrt(3) components.
5) Output packing
   - Produce force/displacement as P/Q surd pair (preferred 32-bit signed fields) and a dissociation flag when V >= De.

Fixed-point formats
-------------------
- Internal "surd" field: P and Q each signed 32-bit (Q32) representing value = P/2^31 + Q/2^31 * sqrt(3).
- Intermediate accumulators: 64-bit signed for multiplies, 96-bit for reductions as needed.
- ROM scales chosen to match these formats (e.g., spread ROM stores P32/Q32 entries).

Approximation strategy
----------------------
- Primary strategy: LUT-heavy with small interpolation/Taylor residuals to minimize DSP use.
- exp(-x) approximation: 256-entry LUT storing high-precision surd-encoded values for exp(-x) over x∈[0,Xmax], with 2nd-order correction using 1-2 multiplies.
- Option: evaluate e^{-a*(r-re)} by indexing per-material scaled domain (a*(r-re)) via small per-material scale factor.

Interfaces
----------
- Input: nodeA[63:0], nodeB[63:0] (two 32-bit P/Q each) or precomputed quadrance[63:0]; material_id[7:0]; start/valid handshake.
- Output: force_p[31:0], force_q[31:0], dissoc (1-bit), done/valid.
- Memory: SIC bus master (AXI-lite-like simple read), ROM port for spread and exp ROMs.

Timing / latency targets
------------------------
- Target combinational latency: 8–12 cycles from valid->done for single pipeline (can be TDM folded to share resources).
- Throughput: 1 result per cycle with pipeline filled OR 1 per N cycles if folded (parameter N).

Resource estimate (rough, prototyping on Tang 25K)
-------------------------------------------------
- DSP multipliers required (estimate per dedicated RPLU): 4–12 (depends on Taylor correction depth).
- BRAM/ROM: spread ROM (4096×64b ≈ 32 KiB), exp ROM (256×64b ≈ 2 KiB), material registry entries (e.g., 64×(P/Q/metadata) ≈ 32 KiB) — can be offloaded to PSRAM/SIC.
- LUT/FF: control/pipeline overhead ~2000–5000 logic cells.
Note: exact numbers must be confirmed by synthesis; Tang 25K is constrained — plan to fold pipeline and offload large identities to PSRAM.

Verification & testplan
-----------------------
- Use canonical CSV from Python reference (material_morse_vectors.csv) as golden vectors.
- RTL testbench steps:
  1) feed precomputed quadrance/r values and material_id; compare force P/Q and dissoc flag against CSV.
  2) stress test sequences (rapid consecutive queries) to validate pipeline backpressure.
  3) corner cases around De threshold and near re.

Incremental rollout
-------------------
1) Software reference (done) and canonical vectors (done).
2) Define precise fixed-point bit widths and LUT scales (this spec).
3) Implement minimal RPLU RTL: accepts scalar r (fixed-point), uses spread ROM + exp ROM -> compute V, flag dissoc. (no surd arithmetic yet)
4) Extend RTL to full surd P/Q pipeline and SIC integration.
5) Synthesis and P&R on Tang 25K with folded pipeline if required.

Open questions
--------------
- Final internal P/Q width: 32-bit chosen here; consider 48/64-bit for lower reconstruction error.
- exp domain max and LUT granularity to cover expected a*(r-re) range per-material.
- SIC protocol (PSRAM load latency) and caching policy: per-material prefetch vs on-demand.

Deliverables
------------
- hardware/docs/rplu_spec.md (this file)
- RTL skeleton for RPLU (rplu.v) with parameterizable precision
- Testbench/runners using hardware/common/rtl/gpu/material_morse_vectors.csv
- Synthesis report for Tang 25K

