# Experimental SOM Temporal-Adapter Study

> **Status:** historical design study for the experimental Wheeler–Feynman
> adapter profile. It is not the active SOM product datapath, the canonical
> silicon ISA, or a measured performance result. “Offer” and “Confirmation”
> below name paired data slots; they are not claims of physical retrocausality.

## Product baseline

The active SOM v1 path is the writable, BRAM-backed `spu_som_bmu.v`. It scans
seven nodes in ascending address order, computes exact weighted quadrances in
Q(sqrt(3)), and retains both the winner and runner-up. Its latency is fixed and
test-pinned at **434 clocks**. That exact-order path is silicon-proven on Tang
Primer 25K and Wukong Artix-7, including complete SOM1 result-frame agreement
with the software oracle.

The older fully parallel `spu_som_node` / `spu_som_node_array` implementation
is archived under `hardware/boards/tang_primer_25k/archive/`. It is not an
alternate SOM v1 implementation and does not establish a current five-cycle
product claim. See [`SOM_V1_PRODUCT_CONTRACT.md`](SOM_V1_PRODUCT_CONTRACT.md)
for the normative architecture and evidence boundary.

## Studied temporal adapter

This study proposed mapping each SOM prototype to an RPLU material record and
comparing an input/prototype pair through the adapter's PHSLK operation:

```text
OFFR  R1, [RPLU, input_addr]    ; paired input slot
CNFM  R1, [RPLU, cluster_addr]  ; paired prototype slot
PHSLK R2, R1, R0                ; exact coherence comparison
JC    #clustered
INVJ  R2, R2                    ; optional conjugate-domain study
```

The attraction was reuse of the adapter's rational cross-products. A
three-to-four-cycle classification was recorded as a design target, but no
integrated RTL or silicon result demonstrates that target. A single PHSLK
comparison also does not by itself replace a seven-prototype nearest-neighbor
search: a complete design would still need a specified scan or parallel
reduction, exact tie behavior, runner-up retention, and SOM1 evidence output.

## Proposed opcode mapping

The study reused opcode `0x2A` for a proposed `SOM_CLASSIFY` operation:

```text
SOM_CLASSIFY Rd, Rs, addr
```

That mapping is not the active implementation contract. In the canonical core,
`0x2A` launches the exact-order SOM/BMU path (or the separately selected
RPLU2 pipeline, depending on the build). The experimental adapter opcodes live
in a separate encoding selected explicitly by the adapter assembler mode.

## Component status

| Component | Status and role |
|---|---|
| `spu_som_bmu.v` | Active seven-node, exact-order product BMU; fixed 434 clocks |
| `spu_som_weight_bram.v` | Active writable prototype storage |
| `spu_cluster_reduce.v` | Active label, confidence-gap, and ambiguity reduction |
| `spu13_som1_frame.v` | Active 52-byte decision-evidence frame |
| archived `spu_som_node_array.v` | Historical parallel-array experiment; superseded |
| `spu_rau.v` PHSLK path | Isolated experimental adapter primitive |
| temporal SOM integration | Proposed only; no product RTL or silicon evidence |
| `rplu_thimble_pade.v` | Separate RPLU2 rational-approximation pipeline, not required by SOM v1 classification |

## Performance boundary

| Path | Cycle statement | Evidence status |
|---|---:|---|
| SOM v1 exact-order BMU | 434 fixed clocks | Test-pinned and cross-vendor silicon-proven |
| Archived parallel array | Historical implementation | Superseded; no product claim |
| Temporal PHSLK classification | 3–4 clock design target | Unimplemented integration; not measured |
| Full Thimble–Padé evaluation | Separate pipeline contract | Silicon-proven on Artix-7, but not a SOM v1 latency |

Host-side deterministic training and map hydration remain the product path.
Any revival of the temporal adapter should begin with a versioned contract that
preserves exact ordering, tie handling, runner-up distance, ambiguity, and the
SOM1 ABI before making throughput or resource claims.
