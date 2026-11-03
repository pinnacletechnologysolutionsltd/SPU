# SYMREG-1 bounded relational model

This is an experimental mathematical specification, not an ISA or hardware
contract. Values are integer pairs `(a,b)` denoting `a+b√3`; algebraic norm is
`a²−3b²`. It is not the existing ISA's tuple-normalizing `SNORM` instruction.

## Identities and values

Eight registers hold immutable value identities, or `None` for unavailable.
Each successful write allocates a new identity even if the value is equal to an
old value. Previously created values remain accessible as historical identities
on paths where they exist. This model retains them until its 64-value capacity
is exhausted; it then explicitly raises `OverflowError` before changing a
register. There is no garbage collection or cross-process identity guarantee.

`write` is an abstract integer-load helper with signed width bounds, not a full
SLI/SLD implementation. The limited `multiply` operation models the existing
SMUL behavior only for integer inputs with denominator one: a fitting exact
product commits, overflow or uninitialized inputs preserve the destination,
and status becomes `OK`, `OVERFLOW` or `INVALID`. With denominator one there
is no common denominator factor that could rescue an overflowing coefficient.
The full [Surd ISA](../../knowledge/isa_reference.md), staging, non-unit
denominators, normalization, flags and other instructions are not modeled.

## Facts and derivations

A value fact `(source, target, k, flip)` asserts
`target = k * conjugate^flip(source)`, where `k ∈ {-2,-1,0,1,2}`.
`flip` is boolean; zero scaling is canonicalized to `flip=False`. A norm fact
`(source, target, k)` asserts `N(target)=k*N(source)`, with
`k ∈ {-4,-2,-1,0,1,2,4}`. Equal norms do not imply value equality.

Concrete admission compares both immutable values exactly and returns no fact
for a false or unsupported assertion. Each stored immutable fact has a
validity flag, rule and parent facts. Only admitted facts and facts produced by
the supported rules enter the store through the model API. A caller-created
lookalike is rejected as a composition parent. This is an API invariant, not a
security boundary against mutation of Python internals.

Value composition multiplies scales and XORs conjugation flags. Norm projection
maps a value fact's scale `k` to `k²`. Norm facts compose by multiplying their
scales. The result is retained only when its scale is in the corresponding
finite set; unsupported combinations return no derivation, not a false fact.
There are at most 256 facts per path; adding a distinct fact at capacity raises
`OverflowError` without eviction. Identical facts are deduplicated. Explicit
composition and norm projection inspect provenance, not concrete values.

## Queries and branches

Queries resolve *current* register bindings and perform a bounded directed
search of same-kind trusted facts. The returned proof path supplies provenance.
`PROVEN` means the supported rules establish the query; `DISPROVEN` requires an
optional exact concrete counterexample; `UNKNOWN` means neither was established.
A true concrete observation is not silently promoted to a proof. Search is
sound but deliberately incomplete: it does not infer reverse edges, division,
out-of-vocabulary scales or arbitrary relations. A historical fact remains
valid for its old identities and cannot answer a query about overwritten
bindings unless a new fact establishes the relationship.

A branch accepts `True`, `False` or `None` (unknown). The first two create one
declared feasible path; unknown creates both. Paths get independent register,
status and fact maps, with a shared immutable-identity allocator and
path-specific known-identity sets. A branch group joins all of its declared
feasible paths: facts are intersected, with merge provenance, and a differing
register binding or status becomes unknown. Conditions are externally supplied
and treated as truthful; this model does not solve branch feasibility or derive
facts from conditions. It does not merge arbitrary unrelated domains. It does
not silently discard stored facts except at an explicit merge, whose discarded
path-specific facts are absent from the result.
