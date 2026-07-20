# SPU-13 Identity And Boundaries

Date: 2026-07-21

This document is the canonical semantic boundary for SPU-13. It exists to keep
the architecture broad enough for its real applications without diluting its
core purpose.

## One-Sentence Identity

SPU-13 is a deterministic exact-arithmetic geometric field processor for
bounded control, graphics, simulation, and topological classification.

The center of gravity is not quantum, neuromorphic, AI, robotics, or graphics
alone. Those are application domains. The architectural center is:

- exact rational and finite-field arithmetic
- deterministic cycle structure
- reproducible state transitions
- inspectable geometry and topology
- invariant-guarded commits and fallbacks

## What SPU-13 Is

SPU-13 is:

- A deterministic rational-field processor for `Q(sqrt(3))`, Quadray/IVM
  geometry, M31/A31 arithmetic, A₃₁ RPLU2 evaluation, and
  `Z[phi]/L_p` Lucas/phinary arithmetic.
- A geometric and graphics processor for exact rasterization, hex projection,
  rational rotations, quadrance, spread, and deterministic visual state,
  including the icosahedral IROTC rotation catalog (VM through silicon).
- A control processor and safety coprocessor for systems that need bounded
  arithmetic, replayable telemetry, invariant checks, and fallback commits.
- A deterministic simulation substrate for discrete rational lattices,
  including 60-degree/hex/triangular physics, chemistry, reaction-diffusion,
  lattice-fluid, particle, and finite-volume experiments.
- A native topological classification substrate: rational SOM/BMU, weighted
  quadrance, stable tie-breaking, confidence gaps, ambiguity flags, and
  Nguyen-style laminar/tolerance weighting — cross-vendor silicon-proven on
  the Iris corpus (Tang 25K and Wukong Artix-7, complete hardware records
  bit-exact to the software oracle).
- A deterministic supervisor for future non-von-Neumann substrates, including
  quantum-control sidecars, neuromorphic/event-driven sidecars, adaptive
  coprocessors, and analog or probabilistic proposal engines.
- FPGA/ASIC-oriented open IP, intended to be measured through VM, RTL,
  synthesis, and silicon traces.

## What SPU-13 Is Not

SPU-13 is not:

- A general-purpose CPU replacement.
- A throughput GPU replacement.
- A tensor-core, LLM, transformer, or backpropagation accelerator.
- A stochastic neuromorphic processor.
- A quantum computer.
- An analog physics oracle.
- A certified flight, medical, automotive, weapons, or life-support controller
  as delivered by this repository.
- A claim that continuous Navier-Stokes, chemistry, or physics is solved
  exactly. The claim is deterministic discrete arithmetic over explicit
  rational or finite-field lattices and update rules.

## Application Pillars

### 1. Deterministic Geometry And Graphics

The geometry stack is a first-class purpose, not a demo. Quadray coordinates,
ROTC, hex projection, Davis/VE invariants, rational spread, and exact raster
paths make SPU-13 suitable for reproducible geometry, graphics, CAD-like
inspection, and visual telemetry.

### 2. Deterministic Robotics And Control

The robotics/control use case is exact state evolution under bounded arithmetic:
rational kinematics, rotor closure, trajectory correction, collision envelopes,
guidance monitors, actuator-safe fallback vectors, and trace replay.

Public language should say "research and development platform" or
"deterministic coprocessor" unless a specific certified product exists.

### 3. Deterministic Physics, Chemistry, And 60-Degree Simulation

The 60-degree/hex/triangular lattice is native to the architecture. Appropriate
claims include deterministic lattice gas, lattice-fluid, reaction-diffusion,
molecular/crystal lattice, finite-volume, and particle/cell simulations.

The defensible claim is bit-exact discrete evolution: fixed update rules,
explicit boundary conditions, invariant checks, and replayable traces.

### 4. Native Rational AI

SPU-13's native AI substrate is deterministic topological classification, not
black-box generative AI. The canonical form is:

```text
input vector
  -> rational weighted quadrance
  -> BMU / second-best / confidence gap
  -> cluster label and ambiguity flag
  -> optional RPLU2/Lucas/Quadray guard projection
```

The strongest current native-AI claim is rational SOM/BMU classification with
Nguyen-style laminar or tolerance weighting. Nguyen-Widrow-style initialization
may be added as a deterministic boot-time seeding strategy, but it is not the
current core claim unless implemented and tested.

Do not claim SOM weights live in the Lucas ring unless that encoding is actually
implemented. The accurate relationship is:

- SOM/BMU supplies deterministic topological classification.
- Nguyen weighting supplies exact feature, memory, or sector priority.
- RPLU2 supplies bounded rational response/evaluation surfaces.
- Lucas MAC supplies exact phinary invariant checking and guarded projection
  when a classifier output enters `Z[phi]/L_p`.

### 5. Guarded Non-Von-Neumann Interfaces

Quantum, neuromorphic, analog, and adaptive substrates are downstream interfaces,
not the identity of the processor. The SPU-13 role is to provide deterministic
boundaries:

1. Close the input epoch or transaction.
2. Freeze the proposal vector.
3. Evaluate exact invariants.
4. Commit only if the guard passes.
5. Otherwise commit a deterministic fallback.

This keeps future-substrate work aligned with the same architecture thesis.
The tensegrity admission guard (`TENSEGRITYLINK`) is the concrete,
silicon-proven instance of this pattern today: a bounded structural
proposal is frozen, checked against exact equilibrium and topology
invariants, and either committed or rolled back, with corrupt-payload
rejection and recovery also silicon-proven. The active proposal/actuation
controller — deciding *what* structural change to propose, not just
guarding it — remains outside the current hardware claim.

## Claim Ladder

Use this ladder in papers, docs, and promotion:

| Claim Level | Meaning |
|---|---|
| Software oracle | Python/C++ reference passes deterministic tests |
| RTL verified | Verilog testbench or VM-vs-RTL trace passes |
| Synthesized | Yosys/Vivado synthesis and structural checks pass |
| Routed | P&R, timing, and bitstream/package complete |
| Hardware verified | FPGA SRAM/flash load plus captured telemetry |
| Integrated | Works inside the full southbridge/SPU-13 system |
| Certified | External process; not implied by hardware success |

Avoid promoting planned features as hardware-verified. Every claim should name
its evidence level.

## Recommended Public Framing

Use:

> SPU-13 is an open deterministic geometric field processor for exact control,
> graphics, simulation, and rational topological classification.

Use for future-facing work:

> SPU-13 provides deterministic algebraic guardrails for non-von-Neumann
> coprocessors.

Avoid:

- "General AI chip"
- "LLM accelerator"
- "Certified flight controller"
- "Quantum processor"
- "Neuromorphic processor"
- "Solves Navier-Stokes exactly"
- "GPU replacement"
- "Anything really"

The architecture can be broadly applicable, but the durable claim is narrower:
exact geometric state, bounded control, deterministic simulation, and
inspectable classification where reproducibility matters more than speculative
throughput.
