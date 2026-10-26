# Engineering Contract: symbolic S3 typed affine-family store

**Date:** 2026-10-17  
**Contract ID:** `contract_symbolic_s3_family_store_2026-10-17.md`  
**Status:** ACTIVE — bounded software tranche authorized by owner  
**Predecessors:** S1 symbolic register store; S2-P exact affine projection and observability

## 1. Objective and scoped files

Add a software-only typed object store that composes the qualified S2-P affine
family operations with immutable, store-local handles. Preserve S1 and S2-P as
independent foundations; do not change either package's semantics.

Create or modify only:

- `research/symbolic_family_store/`
- `spu_strategy/contract_symbolic_s3_family_store_2026-10-17.md`

The store is an experimental Python API. It is not an ISA, ABI, register-file,
RTL, simulator-profile, or hardware-cost proposal.

## 2. Typed object and operation contract

1. Support immutable, append-only, interned handles of exactly three kinds:
   `FAMILY`, `MAP`, and `OBSERVATION`. A handle is valid only in its creating
   store. Reject foreign, forged, out-of-range, and wrong-kind handles.
2. A `FAMILY` payload is the existing canonical
   `research.symbolic_projection.family.Family` over `Q^n`, `1 <= n <= 8`.
   Preserve the distinctions `empty`, `unique`, and `family`; do not represent
   uncertainty as probability.
3. A `MAP` payload is a canonical exact rational matrix with between 1 and 64
   rows, 1 to 8 columns, and coefficients within the S2-P 4096-bit limit.
   Map input and output dimensions may differ. `image` accepts only maps with
   1 to 8 output rows because `Family` state dimensions are bounded to 1..8;
   maps with 9..64 output rows are observation-only. Reject dimension
   mismatches.
4. An `OBSERVATION` payload is a canonical pair `(P, y)`, where `P` is a
   `MAP` from `Q^n` to `Q^m` and `y` is an exact vector in `Q^m`. Store the
   canonical matrix and vector values, not a borrowed mutable list.
5. Implement handle-returning `full_space(n)`, `family(origin, basis)`,
   `linear_map(rows)`, `observation(map_handle, y)`, `image(family_handle,
   map_handle)`, and `observe(family_handle, observation_handle)` operations,
   plus typed `get` and exact family status inspection. `image` and `observe`
   delegate to the existing S2-P `Family.image` and `Family.observe` methods.
6. Cap the store at 128 unique objects, matching S1's software guard. Repeated
   canonical objects return the same handle without consuming capacity. There
   is no deletion, garbage collection, serialization, or handle ABI.
7. Validate dimensions, exact coefficient types, and coefficient bounds before
   publishing a result. On every rejected operation, object count and all
   existing objects remain unchanged. Catch only documented validation and
   budget exceptions; do not convert programming errors into success values.
8. Store-local handle identity is not semantic equality. Family semantic
   equality uses the canonical `Family` value; map and observation equality
   uses canonical exact tuples.

## 3. Pre-execution halt-and-flag review

Before coding, verify these points against the existing S2-P APIs:

- `Family.image` supports rectangular maps while requiring the family input
  dimension to match the map column count.
- `Family.observe` checks the same input dimension and output measurement
  dimension, and returns a canonical empty/singleton/family result.
- All construction paths enforce the existing exact rational and coefficient
  guards before the store interns an object.
- Store insertion is last, after every operation that can reject the request.

If any point is false, halt and amend this contract before implementation.

## 4. Command-first implementation instructions

From the repository root:

```bash
mkdir -p research/symbolic_family_store
```

Implement the store in Lithic Python modules of 50–150 lines each. Reuse
`research/symbolic_projection/family.py` and `linear.py`; do not copy their
algorithms. Add focused unit tests for canonical interning, rectangular image,
consistent and inconsistent observations, empty/unique/family preservation,
foreign and wrong-kind handles, object-capacity exhaustion, dimension and
coefficient rejection, and failure atomicity. Add a deterministic demo that
prints the statuses of one family before and after image and observation.

Do not add floating point, random tests, S1 private-store access, ISA opcodes,
RTL, GPU/compute backends, nonlinear constraints, probabilistic semantics,
learning, or performance claims.

## 5. Verification and evidence

Run these short gates from the repository root:

```bash
python3 -m unittest discover -s research/symbolic_family_store -p 'test_*.py' -v
python3 -m research.symbolic_family_store.demo
python3 -m unittest discover -s research/symbolic_registers -p 'test_*.py' -v
python3 -m unittest discover -s research/symbolic_projection -p 'test_*.py' -v
git diff --check -- research/symbolic_family_store spu_strategy/contract_symbolic_s3_family_store_2026-10-17.md
```

Record exact commands, source revision, outcomes, test counts, and artifact
paths. S1 and S2-P evidence remains separately attributed; passing this tranche
does not requalify those predecessors or establish hardware performance.

Launch the shared repository gate exactly once, with a new output directory and
a 1800-second timeout:

```bash
tools/run_detached_job.sh \
  --output build/symbolic_family_store/s3_20261017_01 \
  --timeout 1800 \
  --notify-desktop \
  -- bash research/symbolic_family_store/check_repo.sh
```

The check script must run `bash tools/verify_repo.sh` and preserve its exit
status. Stop after the detached launcher reports `LAUNCHED`; do not poll. No
retry or substitute gate is authorized by this contract.

## 6. Acceptance and stop conditions

Accept only if all focused tests and the demo complete, cross-store misuse and
mutation controls fail as specified, failed calls leave the store unchanged,
and the shared repository gate has exactly one `COMPLETE` terminal marker with
exit code 0. A `FAILED`, `TIMEOUT`, unavailable result, or ambiguity is not a
pass and does not authorize a retry.

Halt if S2-P's API does not satisfy §3, any result can be interned before full
validation, or object/type/dimension semantics are ambiguous. Report bounded
software evidence only. Do not merge into ISA-A or ISA-B and do not infer an
instruction, silicon, acceleration, or physical result.
