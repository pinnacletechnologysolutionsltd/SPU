# SSM-4 design: certified geometric state

Status: IMPLEMENTATION CONTRACT PREPARED FOR REVIEW, 2026-10-18. SG-0 is now
focused-software-qualified and [preserved locally](../research/sg0_baseline_20261018/README.md).
The [bounded SSM-4 draft contract](../spu_strategy/contract_ssm4_certified_geometric_state_2026-10-18.md)
freezes candidate inputs, outcomes and proposed gates. No SSM-4 implementation,
campaign or new instruction encoding is authorized.

## Purpose and sequence

The qualified [SSM-0–3 architecture](SSM_ARCHITECTURE_2026-10-18.md) supplies exact
families, correlations, relations and replayable derivations. The next integration
experiment is [SG-0](SG0_SYMBOLIC_GPU_INTERFACE_DESIGN_2026-10-18.md): verified
parameters produce a procedural two-triangle scene for the current T1d workbench.
Use that bridge to determine what geometric machine state actually needs.

The draft now targets uniquely observable vertices from unresolved rational
parameter families. It records that S2-P stores basis vectors as rows, checks
empty families before annihilation, retains differing latent families even when
their visible patches coincide, and requires SG-0 scene/packet byte parity without
changing SG-0's unique-parameter admission. The candidate details below remain
design context; the draft contract specifies the proposed bounded tranche.

1. Finish consolidation and preserve SSM-3's qualified evidence.
2. Freeze and implement the bounded SG-0 interface in Python.
3. Ratify/implement SSM-4 against the concrete bridge requirements.
4. Qualify SSM-4 independently before any C++ simulator or FPGA promotion.
5. Follow with the separate SOM–SSM/adaptive-memory experiments.

These are dependency gates, not a calendar delay or a requirement that SIM-G2A,
Router-F1 or every GPU/FPGA workstream finish first. Design work proceeds now.

## Smallest candidate geometric state

Retain a verified rational parameter family theta in Q^k with k<=3 for the first
pilot, its original inputs, proof identity, immutable recipe and exact transform
history. Define each derived vertex by an affine expression

```
v_i(theta) = M_i*theta + b_i,  v_i in Q3
```

Four derived vertices need not become twelve independent solver unknowns. Keep
the low-dimensional parameterization and vertex recipes; do not silently raise
the existing eight-dimensional Family limit or promise a general Q12 solver.
Topology/flat colors are explicit recipe data. Their admissibility needs checks
separate from a proof about theta.

Candidate descriptor fields, subject to SG-0 freeze:

- Original-input and independently verified proof digests, parameter order/domain.
- Canonical parameter family or persistent reference to it.
- Vertex affine recipes, topology, color identities and their source/schema pins.
- Exact transform descriptions plus coordinate-domain/inverse obligations.
- Materialization request: required observable vertices and target conversion profile.
- Receipt binding resolved geometry, proof, recipe, transform and quantized scene.

This is a proposed semantic object, not a 128-bit register allocation, binary ABI
or addition to SSM0_V1. Decide which fields must become new executable state only
after SG-0 shows which checks and dependencies recur.

## Candidate operations and proof boundaries

Investigate narrow operations: retain geometric parameterization, compose exact
affine maps, constrain parameters, request observable geometry, materialize
admissible coordinates, and independently replay the resulting evidence.
SSM-3's row certificates remain proofs relative to their original linear inputs.
Any transformation of parameter equations must preserve or explicitly transport
those equations, with checked domain and inverse rules.

A checked affine recipe gives exact derived coordinates. It does not prove an
arbitrary geometric assertion. Planarity shared by the frozen patch, transform
properties and index/topology validity need explicit checks. Squared distances,
Gram-zero, collision constraints and general rigid mechanisms introduce polynomial
conditions; surd domains introduce different encodings and equality rules. They
remain outside the first scope rather than being implied by exact arithmetic.

SG-0 initially requires unique parameters. SSM-4 design should ask whether uniquely
observable vertices may be materialized even with unresolved latent parameters:
this is allowed mathematically when every required vertex map annihilates every
remaining family direction. That rule would need its own exact acceptance cases,
not an arbitrary witness policy. Freeze the choice after the SG-0 handoff review.

The finite-width T1d boundary is an explicit conversion with rounding and refusal
rules. A successful mathematical proof does not imply that quantized geometry or
rasterized pixels preserve the same relationship. Record exact and quantized
states separately; verify conversion/profile provenance and report model differences.

## Proposed falsifiers and acceptance questions

- Can a stale/changed proof or parameter order be rejected before geometry output?
- Do symbolic composition and explicit exact stepping yield the same required
  vertices, with original unresolved state retained until the declared observation?
- Does every materialized coordinate have unambiguous proof/recipe/transform lineage?
- Are empty, unresolved, resource-exhausted and quantization-invalid states distinct?
- Are two distinct internal families that currently render identically still
  distinct when a later transform exposes their hidden differences?
- Can changed topology, out-of-range depth, quantization collapse and finite-width
  model deviations be detected without claiming the renderer disproves the algebra?

Do not turn these questions into acceptance claims before an implementation exists.
A finite generated scene is the proposed integration target, not a general shader,
mesh kernel, geometric theorem prover or nonlinear solver.

## Gates and exclusions

SG-0 interface freeze is required before SSM-4 implementation: versioned schemas,
exact recipe, supported materialization policy, finite-width boundary, reference
outputs and failure semantics. SSM-4 then needs its own frozen source identities,
resource/campaign budget, tests, independent replay and repository qualification.
Rendering, C++ parity and FPGA qualification remain separate evidence dimensions.

No Soul memory, SOM training, automatic invention of axioms, general nonlinear
geometry, surd/lattice expansion, GPU RTL or ISA promotion is included now. The
[SOM interface design](SOM_SYMBOLIC_INTERFACE_DESIGN_2026-10-18.md) remains useful
follow-on work, with adaptive hypotheses separate from certified deductions.
