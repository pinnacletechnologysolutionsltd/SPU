# E8 validated-state software prototype — 2026-10-13

Separate authorized preparation. The [contract](../spu_strategy/contract_e8_validated_state_preparation_2026-10-13.md)
implements IMPORT, LEFT-only TRANSFORM and two EXPORT boundaries as serial
software APIs, not SPU instructions. The original21,181-unit schedule and all
prior evidence remain unchanged. Independent sign-off and qualification remain HOLD.

A Session validates one immutable context, then admits externally serialized
descriptors into a private registry. Identity-only keys must actually belong
to that registry. Raw tuples, forged keys, other-session keys and retired keys
cannot assert validated state. The trusted-runtime/private-storage premise is
explicit; Python introspection or memory-fault protection is not established.

LEFT transformations preserve validity through the exact verified reflection
table. Only LEFT simple reflections are internally permitted; other group
operations remain separate references. Each transition retains the old state
until the new immutable descriptor is ready, then updates the registry atomically
at the API boundary. Other handles and previously exported snapshots remain
independent. No repeated full Gram admission runs on this internal path.

## Short measured boundaries

The specified register/array model records:

| Operation | Short literal work | Scope |
|---|---:|---|
| IMPORT | 11,391 | Packet copy/identity checks, full Gram admission and registry publication |
| Warm LEFT TRANSFORM | 117 | Guards, update, scratch ownership, publication and cleanup |
| Serialization EXPORT | 495 | Full76-byte record, result checks and leased buffer publication |
| Coordinate EXPORT, all-ones input | 28,302 | Input admission, exact basis decoding, coordinate computation and validation |

The materialization count depends on input/arithmetic paths; other prepared
vectors may differ. Export release and state retirement are charged separately.
The117-unit transition is a new complete software protocol schedule under its
stated premises, not a native cycle count or retroactive replacement of82.
Setup construction and context validation execute outside the metered schedule
and remain UNMETERED. No amortization threshold or matched-baseline speedup is
established. Table bandwidth, contention and physical resources are unmeasured.

Buffer lifetime is explicit: wire/vector exports remain owned until release.
The model includes metadata and registry storage, so an owned state costs384bits,
not just its64-bit payload. Input/scratch/workspace overlap and failure cleanup
are recorded. The context's307,680 static bits are shared by live handles within
one Session. This is not a global concurrent-system or host-memory measurement.

## Correctness and remaining gates

Six focused tests pass. They check all eight permitted generators against the
unchanged reference, absence of Gram work in TRANSFORM, exact noncommuting
coordinates, forged/foreign/stale capabilities, invalid packet/context rejection,
overflow/domain refusal without state mutation, capacity, handle independence,
export leases and independent event/lifetime replay. Three short preparation
scenarios cover identity, noncommuting order and an inverse pair.

The closure argument is orthogonality plus root-set preservation of the same
simple reflection applied to each admitted basis image, under the verified
immutable context and trusted registry. Independent mathematical/implementation
review still needs to sign that chain and check accounting completeness.
Emitted-event replay cannot detect every consistently omitted operation.

Prototype limits are eight live states/exports and checked signed64 normalized
values/signed256 raw temporaries. They do not qualify a finite processing element,
reset/ownership hardware protocol or the future K16/K64 workloads. Complete
setup, all-operation accounting and a reviewed common work/storage profile are
still required. No proposed64-million limit is adopted by this prototype.

Evidence: `build/e8_root_images_20261013/validated_state_preparation_01/`.
No full384-configuration or qualification campaign is launched. No FPGA, ISA,
RTL or physical backend changes occur; Surd CPU repair remains the priority.
