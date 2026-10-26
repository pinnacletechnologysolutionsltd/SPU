# Post-GPU Lattice, SOM Allocator, and LLM Research Roadmap

Date: 2026-09-15  
Status: **PARKED — research roadmap only**  
Owner: SPU research track

This document authorizes no RTL, fixture generation, model download, training,
benchmark run, synthesis, ISA allocation, bitstream, board programming, or
hardware purchase. The current priority remains the Wukong VGA/GPU prepared-
scene bring-up. Any phase below requires a separate owner-authorized contract
with frozen commands, inputs, limits, and stop conditions.

## 0. Entry gate: close the GPU evidence loop

Lattice work may not begin until the Wukong GPU is demonstrably programmable
hardware rather than only synthesized RTL.

The gate is deliberately split into two tranches:

1. **T1d — one-scene physical UART integration.** Load its one frozen
   64-byte wire transaction, activate its prepared scene atomically, and close
   its simulation, routed-timing, and five-attempt hardware evidence.
2. **T1e — dynamic reload, separately contracted.** Without rebuilding the
   bitstream, load at least two distinguishable frozen scenes in a declared
   order and prove stable repeated activation. T1d does not authorize or
   establish this result.

Both tranches must preserve the framebuffer-less streaming GPU. Record source
and bitstream hashes, routed timing, wiring, exact commands, attempt logs, and
labelled photographic evidence. Atomic frame-boundary activation is established
principally by self-checking verification, not by a photograph.

**Exit condition:** T1d and T1e are closed with interpretable evidence and no
unresolved canonical-GPU regression.

## 1. Exact mathematical foundation: A3 inside D4

The first lattice deliverable is software-only and establishes exactly what is
true before attaching neural or hardware claims.

Define the integer Quadray hyperplane

```text
H0 = {x in Z^4 : x0 + x1 + x2 + x3 = 0}.
```

The reference package must:

1. generate all 24 roots `+-e_i +-e_j` of D4;
2. identify the 12 A3 root vectors `e_i-e_j` in `H0`, representing six
   distinct reflections;
3. identify the remaining 12 root vectors, representing six distinct
   reflections that do not preserve `H0` in general;
4. enumerate the 24-element `S4` subgroup fixing
   `n=(1,1,1,1)`, the 48-element setwise stabilizer of `H0` that sends
   `n` to `+n` or `-n`, and the full 192-element Weyl group `W(D4)`;
5. verify integrality, norm and inner-product preservation, reflection
   involution, closure of `H0` under A3, and equivalence of A3 reflections
   with coordinate swaps; and
6. measure how the non-preserving reflections mix the Quadray component and
   the component parallel to `n`.

For a general `v in Z^4`, define

```text
s = sum_i v_i
t = s / 4
q = v - t*n
```

`t` and `q` need not be integral. Software may operate exactly over `Q^4`, or
use the integral scaled representation

```text
Q = 4*q = 4*v - s*n
v = (Q + s*n) / 4,
```

where `Q in Z^4` and `sum_i Q_i = 0`. A later finite-width implementation must
freeze one representation and its overflow semantics; it may not silently
truncate `s/4`.

“Exhaustive” testing means exhaustive enumeration over a contractually frozen
finite-width domain, supplemented by symbolic or exact algebraic proofs for
the unbounded identities. It never means enumeration of all `Z^4`.

Terminology must remain exact: the full tetrahedral symmetry group has 24
elements and is isomorphic to `S4`; its orientation-preserving rotational
subgroup has 12 elements and is isomorphic to `A4`. `S4` must not be called
the orientation-preserving tetrahedral group.

**Exit condition:** the algebraic checks and frozen finite-domain tests pass,
with no neural-network or hardware-performance claim.

## 2. Positioning and claim boundaries

The strongest permitted working position is:

> SPU-13 investigates whether native integer lattice operations—particularly
> fixed Quadray coordinate permutations, exact deterministic metrics, and
> inexpensive signed D4 reflections—can reduce the cost of specific spatial,
> allocation, and quantization workloads. The coordinate system alone does not
> establish an advantage; equivalent conventional integer baselines must be
> beaten on the same task.

Apply these boundaries to prior-art, competitive-positioning, and experiment
documents:

- A compile-time-fixed coordinate permutation can disappear into routing and
  has zero arithmetic/DSP cost. A runtime-selected `S4` member requires decode
  and multiplexing; a registered instruction consumes a pipeline stage; signed
  D4 operations may require two's-complement negation and overflow detection.
  Do not describe all of these cases as a zero-cost wire permutation.
- Quadray Euclidean quadrance is exact and can compare distances without a
  square root, but Cartesian integer arithmetic can also compare squared
  distances without a square root. General sums of squares still require DSPs,
  LUT multipliers, shift-add logic, or serialized arithmetic. `L1` and
  `L-infinity` can be multiplier-free but are different metrics.
- `SO(3)`, `SE(3)`, finite rotation groups, and permutation groups belong to
  established equivariant-ML work. E8 is a root system and lattice, not a
  mainstream continuous physical symmetry used interchangeably with those
  groups. Cohen and Welling's
  [Group Equivariant CNNs](https://proceedings.mlr.press/v48/cohenc16.html)
  concerns group convolutions over discrete translations, reflections, and
  rotations. Lattice codebooks and learned lattice vector quantization are a
  separate compression line, exemplified by
  [QuIP#](https://arxiv.org/abs/2402.04396) and
  [learned lattice vector quantization](https://proceedings.neurips.cc/paper_files/paper/2024/hash/c09916f6f0c428a97a09a53648e5002e-Abstract-Conference.html).
- “Parity with INT4” is not a result definition. INT4 is a scalar format;
  A3, D4, and E8 are geometric structures. Every comparison must freeze bits
  per weight/vector, metadata, reconstruction error or perplexity,
  nearest-point throughput, LUT/DSP/BRAM cost, energy per assignment where
  physically measured, and any routing or cache-locality metric being claimed.

## 3. Keep the research hypotheses separate

| Track | Decision question | Initial status |
|---|---|---|
| A — lattice quantization | Do D4 or E8 blocks improve weight compression against equal-bit conventional baselines? | First software probe |
| B — reflection layers | Can short reflection products retain useful model quality while reducing multiplication, parameters, or hardware cost? | Parked until Track A passes, except for a separately authorized tiny falsifier |
| C — spatial/latent coupling | Can D4 transformations usefully mix a Quadray spatial state with one explicitly defined latent channel? | Speculative and parked |

The closed SPU-4 SOM tranche is not reopened by this roadmap. The allocator
hypothesis below is a new workload and requires a new owner-authorized contract,
an exact oracle, conventional allocation baselines, and an explicit reason to
revisit the closure in `docs/SOM_RESEARCH_CLOSURE_2026-09-11.md`.

## 4. First post-GPU application probe: SOM allocation

Only after the ordinary GPU and dynamic scene loading are stable, evaluate the
narrow proposition

```text
rational topology
  -> deterministic work placement
  -> fewer conflicts or migrations.
```

This does not claim that Quadray universally improves Euclidean GPU arithmetic.
The probe order is:

1. Capture and freeze ordinary GPU memory/work traces without changing GPU
   scheduling.
2. Replay those traces in software through a frozen Nguyen-initialized SOM.
3. Compare deterministic placement with round-robin, hashing, and simple
   locality heuristics under identical capacity and safety rules.
4. Measure conflicts, migrations, locality/cache proxy, imbalance, allocation
   latency, metadata, and deterministic reproducibility. Predeclare the primary
   metric and acceptable regressions.
5. Only after a software advantage, specify a bypassable allocation sidecar.
   The SOM may return a bank or workgroup identifier; conventional hardware
   remains responsible for capacity, bounds, hazards, and safety.
6. Use bypass versus sidecar selection for exact matched A/B traces and builds.

If graphics traces show no advantage, close or park this allocator hypothesis.
Do not proceed to hardware merely because the SOM is already implemented
elsewhere in the project.

After a graphics result passes, the same frozen allocator interface may be
tested in software on separately sourced LLM traces: KV-cache placement,
token-block routing, expert routing, or associative-memory allocation. These
are new workloads, not evidence inherited from graphics. Epoch-based adaptation
is gated until static allocation demonstrates value. Separate LLM compute
hardware comes later, if at all.

**Exit condition:** the frozen SOM allocator beats named conventional
heuristics on a predeclared trace metric without violating safety or capacity.

## 5. Track A: weight-quantization software probe

Use a small public model that can be evaluated on the existing PC. Do not train
an LLM from scratch.

Compare:

- FP16 or FP32;
- scalar INT8;
- scalar INT4;
- blockwise D4;
- blockwise E8; and
- a conventional vector quantizer at the same effective bit budget.

Before execution, freeze each lattice codebook/domain, block size, coordinate
normalization, coset and parity rules, scale/zero-point metadata, packing, and
decoder. Equal-bit comparisons must include all scaling, indexing, padding,
and codebook metadata.

Measure reconstruction error, task accuracy or perplexity, effective bits per
weight, encoding time, decoding operations, estimated memory traffic, and
deterministic bit-for-bit reproducibility.

**Exit condition:** lattice quantization beats or meaningfully complements a
conventional equal-budget baseline on at least one predeclared metric without
unacceptable task-quality loss. Otherwise close the LLM-weight track while
retaining the mathematics for geometry, coding, or other uses.

## 6. Track B: reflection-parameterized layer probe

Only after Track A passes, or under a separate cheap-falsifier contract, test

```text
W = D2 * S_m * S_(m-1) * ... * S_1 * D1,
```

where each `S_i` is a root reflection or permutation, `D1` and `D2` are
learned diagonal scales, and residual paths preserve expressivity.

Compare dense linear layers, low-rank layers, signed permutations,
Hadamard-style structured transforms, and other multiplier-reduced layers.
Quantization alone is not evidence of reduced multiplication.

**Exit condition:** comparable task quality with a measured reduction in a
predeclared multiplication, parameter, latency, throughput, or hardware-cost
metric.

## 7. Isolated SPU instruction and hardware cost model

Hardware investigation begins only after a named workload justifies it. The
parked D4 probe is specified separately in
`spu_strategy/contract_spu_d4_root_reflection_probe_2026-09-14.md`.

Candidate operations for later contracts are:

```text
qperm       permute four Quadray lanes
qswap       exchange one lane pair
d4ref       apply one selected D4 root reflection
weylword    execute a short encoded reflection sequence
latdec4     decode one D4-quantized block
latdec8     decode one E8-quantized block
```

Each operation must freeze register representation, doubled-coordinate rules,
overflow/status semantics, latency and handshake, fixed versus runtime
selection, treatment of the fourth D4 component, preservation or intentional
violation of the Quadray zero-sum invariant, and an independent oracle.

Synthesize isolated candidates on Wukong against directly specialized and fair
integer baselines. Record LUT, FF, CARRY4, DSP, BRAM/LUTRAM, routed Fmax,
critical path, cycles per block, and warnings. Energy may be claimed only from
a controlled physical measurement, never inferred from LUT count.

**Exit condition:** a workload-relevant isolated operation demonstrates a
useful measured advantage. Synthesis supports FPGA resource/timing claims only,
not model-quality or LLM-performance claims.

## 8. Narrow accelerator demonstrator

Do not begin with a full LLM accelerator. Under a new contract, build exactly
one narrow demonstrator such as a lattice-quantized linear layer, small
classifier, token-embedding lookup/decoder, or reflection-based feature mixer.
Stream frozen inputs and reference outputs through a controlled interface and
require bit-exact agreement with the integer oracle.

The decision question is:

> Does the lattice representation retain a measurable hardware advantage after
> decoding and downstream arithmetic are included?

Decoder savings may not hide costs moved elsewhere in the pipeline.

## 9. Decision classifications

- **ADVANCE:** task-quality and hardware evidence establish a clear niche.
- **PARK:** the mathematics is valid but model or hardware benefit remains
  inconclusive.
- **CLOSE:** conventional INT4/INT8, vector quantization, or structured
  transforms dominate under the frozen comparison.
- **PIVOT:** A3/D4 is more useful for deterministic geometry, robotics, error
  coding, procedural materials, or another named workload than for LLM weights.

The required order is:

```text
T1d one-scene GPU proof
  -> T1e two-scene reload proof
  -> exact A3/D4 software foundation
  -> frozen GPU traces and software SOM allocator baselines
  -> bypassable SOM sidecar only if allocation wins
  -> equal-budget lattice quantization as a separate track
  -> reflection layers only if justified
  -> isolated FPGA cost probes
  -> narrow accelerator only after a hardware advantage
```
