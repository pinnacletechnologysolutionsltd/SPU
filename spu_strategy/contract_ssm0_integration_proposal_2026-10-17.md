# SSM-0: bounded symbolic machine integration proposal

**Date:** 2026-10-17
**Status:** ACTIVE — owner conditionally ratified design; prerequisite resolved; one implementation/verification attempt authorized
**Roles:** current agent performs specification, implementation and audit sequentially.
**Prepared against HEAD:** `963a685004b96e275e7e58ebefac98c6e1321597`, dirty workspace.

## 1. Preserve qualified foundations

Keep `research/symbolic_registers/` (S1) and
`research/symbolic_projection/` (S2-P) unchanged. Add only a future adapter in
`research/ssm0/`. Do not modify GPU, simulator, RTL, ISA, learning or Soul code.
Keep implementation modules within the repository's Lithic size rule.

Prior evidence, independently attributed:

| Tranche | Terminal evidence | Scope |
|---|---|---|
| S1 | `build/symbolic_registers/s1_20261017_01/result.json`, COMPLETE/0 | 244 repository passes; symbolic transformation store |
| S2-P | `build/symbolic_projection/s2p_20261017_01/result.json`, COMPLETE/0 | 244 repository passes; exact affine families and observability |
| G3 | `build/exact_geometry/g3_20261017_01/result.json`, COMPLETE/0 | Rational isometries, explicit inverses and a declared reversal map |

G3 is already software-qualified. Extending its results to an integrated
symbolic machine or to internal constraint-network dynamics is a new task.

An additional `research/symbolic_family_store/` exists under
`contract_symbolic_s3_family_store_2026-10-17.md`. Its job directory
`build/symbolic_family_store/s3_20261017_01/` has no terminal marker at
preparation time. Preserve it. Do not infer qualification from its presence.
Its S3 label means typed family storage here, not the proposed neural/SOM S3.
Before implementation, inspect its terminal evidence. Reuse its public API if
qualified; if unavailable or unsuccessful, stop the integration decision and
report the dependency rather than duplicate the store or relaunch its gate.

## 2. Pre-execution domain review

Flag and resolve this before code: S1 VALUE canonicalization removes the common
Quadray gauge component. S2-P's four coordinates are independent. Passing an
independent Q^4 family through S1 VALUE would silently discard state.

Correction: keep families entirely in S2-P. Import S1 TRANSFORM descriptions
only, through an explicitly tagged matrix action. Never use S1 VALUE for an
independent family. Distinguish:

- `Q4`: four independent rational coordinates, including genuine hidden state.
- `Q3_QUADRAY`: zero-sum rational four-tuples; three independent coordinates.

SSM-0's first demonstration uses Q4 plus observable Q3 images. A tagged
`S1_LIFT_Q4(word)` explicitly imports S1's full 4x4 gauge-preserving matrix,
whose inverse G3 checks on all four coordinates. This is an ordinary Q4
linear action; do not claim it preserves the standard Q4 Euclidean metric.
Do not identify gauge freedom with hidden independent state.

Use distinct Q4 map names A=T1, a=T1^-1, B=T2 from S2-P. B is self-inverse.
These are not aliases for S1's R,r,H. Projection P is rectangular and has no
inverse. No arbitrary map-inversion algorithm is part of this tranche.

## 3. One coherent software interface

Use eight adapter registers with store-local immutable typed handles.
Keep raw predecessor handles private to their owning store and access them
only through public methods. Do not rely on either store's internal lists.
Adapter kinds:

| Kind | Meaning |
|---|---|
| FAMILY | Canonical S2-P family, ambient dimension retained even when empty |
| TRANSFORM | Bounded immutable sequence of typed invertible generator references |
| MAP | Exact rational matrix with declared input/output dimensions |
| OBSERVATION | Immutable pair (map, exact measurement vector) |

A result FAMILY already expresses empty, unique or unresolved status; do not
create a second solution encoding. Define software methods, not binary opcodes:

1. `load(dst, handle)`: validate ownership/type before replacing a register.
2. `compose(dst,a,b)`: a after b; construct an execution-order sequence b+a.
3. `inverse(dst,src)`: reverse sequence and invert registered generators only.
4. `apply(dst,transform,family)`: materialize one composed matrix, image family.
5. `project(dst,map,family)`: exact rectangular family image.
6. `observe(dst,family,observation)`: intersect with the declared measurement.
7. `resolve(src)`: return immutable canonical family plus status/dimension.
8. `serialize(src)`: return canonical JSON bytes for the semantic object.

Compose/inverse must not evaluate matrices or family coordinates. Adjacent
certified inverse cancellation is sufficient; do not claim full semantic
canonicalization of transformation sequences. Exact matrix comparison is a
separate evaluated operation. Old handles remain valid after all operations.

## 4. Frozen demonstration and acceptance

Store S0=(1,2,3,0)+span(e4). It has a singleton initial observable image.
Build C=B after A symbolically, verify C^-1 after C reduces to identity,
then apply C once to S0. Project and compare against explicit A-then-B images.
A maps the known visible coordinates to (-2,1,3); B reveals hidden h.
The evolved family projects to (0,1,3)+span(e1).
Observe P*x=(11,1,3): the evolved family becomes the unique point
(11,1,3,-2). Apply C^-1 to recover the unique initial point (1,2,3,11).

Independent branches start from the same original evolved-family handle:

- Observe only x2=1: retain an unresolved one-dimensional family.
- Observe P*x=(11,99,3): obtain empty, not unresolved and not an exception.
- Observe P*x=(11,1,3): obtain the unique point above.

Also include a real S1 import in the acceptance sequence: construct an S1
RHR word and inverse with S1's public transform API, explicitly lift its matrix
action to Q4, and check image/inverse recovery of S0. This prevents an adapter
that merely bypasses the S1 component from satisfying integration acceptance.

Required negative control: (0,0,0,1) and (0,0,0,2) have identical initial P
images but different P*B images. Projecting first loses predictive information;
no API may silently infer a unique next observation from that image.

Additional acceptance:

- Compare composed and stepwise families exactly, including basis and origin.
- Verify original family, transform and observation payloads are unchanged.
- Compare sequential evolution/observation with directly stacked constraints
  on the initial state; distinguish recovered current versus initial state.
- Check wrong-kind, foreign, forged and stale-looking handles; reject domain
  and dimension mismatches, unsupported inverses and resource overflow.
- On failure, destination registers and published objects remain unchanged.
  Validate/compute first; intern the final result only after all checks pass.

## 5. Reproducible serialization

Serialize semantic payloads, never process-specific owner tokens, handle indices,
object addresses or timestamps. Use UTF-8 JSON with sorted keys, compact
separators, no floats and exactly one trailing newline. Encode every rational
as decimal-string pair [numerator,positive_denominator], reduced by Fraction.
Include schema `SSM0_V1`, kind, domain/dimensions and empty/status where relevant.
Families use canonical S2-P origin and RREF basis; empty objects retain ambient
dimension. Transforms serialize typed reduced sequences, not evaluated matrices;
semantically equal unreduced descriptions need not serialize identically.

Require byte-identical outputs from two fresh subprocesses with different object
allocation histories and PYTHONHASHSEED values. Equivalent presentations of the
same family must yield identical bytes. Canonical family serialization is not
a claim of general symbolic equivalence. Deserialization is outside this tranche.

## 6. Resource and verification budget

Freeze eight registers, 128 public adapter objects, at most 64 expanded transform
symbols, dimensions 1..8 and 4096-bit completed rational coefficients. Underlying
stores retain their own independent 128-object caps; report each count rather
than claiming a shared memory bound. No deletion or garbage collector. Arithmetic
temporaries and input conversion are not hard-isolated host resource usage.

Future implementation commands (not runnable until the proposed package exists):

```bash
python3 -m unittest discover -s research/ssm0 -p 'test_*.py' -v
python3 -m research.ssm0.demo
python3 -m unittest discover -s research/symbolic_registers -p 'test_*.py' -v
python3 -m unittest discover -s research/symbolic_projection -p 'test_*.py' -v
```

Provide `research/ssm0/check_repo.sh` to run scoped tests, the family-store tests,
the S1 and S2-P suites, existing geometry/trace/math checks and verify_repo once.
Inspect existing terminal markers first; never run concurrent shared regressions.
After implementation authorization, the proposed campaign is exactly one detached
attempt, 1800-second external timeout, no retries or extensions:

```bash
tools/run_detached_job.sh \
  --output build/ssm0/integration_20261017_01 \
  --timeout 1800 --notify-desktop \
  -- bash research/ssm0/check_repo.sh
```

If that output exists, halt rather than overwrite or silently consume another
attempt. End the agent turn after LAUNCHED. Interpret only exactly one terminal
marker in a later invocation. No synthesis is relevant to this adapter-only
software experiment; hardware behavior, interfaces and silicon are NOT RUN.

## 7. Proposal disposition and stop conditions

This document prepares a reviewable integration proposal only. No SSM-0 package,
new detached campaign, store modification or opcode is authorized by this draft.
Halt implementation on unresolved domains, failed prerequisites, semantic
contradictions, failing checks or inability to preserve failure atomicity.
Do not repair predecessor APIs by expanding scope without a revised contract.

Soul/adaptive memory, neural/SOM proposals, nonlinear dynamics and general
constraint networks remain separate experiments. Preparation verification:
run the documentation audit and scoped whitespace check; report pre-existing
findings separately from implementation evidence.

Preparation audit result: `python3 tools/doc_audit.py --actual-pass 238` exited 0
and scanned 246 tracked Markdown files. It reported 14 broken links, 30 uncited
claim findings, one stale total, 126 orphan documents and one superseded-status
finding in the existing tracked corpus. These are audit findings, not a clean
repository claim; this newly untracked proposal is outside that tracked sweep.
The 238 argument follows the documentation gate contract, not the latest
observed regression count (244). Future implementation commands above have not
been executed because their target package does not yet exist.


## 8. Ratification and execution record

Owner accepted the design and authorized implementation conditional on family-store
qualification. On the subsequent status invocation, the prerequisite had exactly
one COMPLETE marker with exit 0: 947 seconds, 244 repository passes, zero failures.
Record: `build/symbolic_family_store/s3_20261017_01/result.json`. The execution
hold is resolved. This ratification supersedes the proposal-only restrictions
in section 7; all technical boundaries and the single-attempt budget remain.

Implementation creates only `research/ssm0/` and updates this contract. No
predecessor implementation is changed. The adapter reuses the family store's
public family/map/observation/image/observe API and S1's public transform store,
reduction/inverse/materialization functions. Register APIs accept adapter handles
only; predecessor handles remain private. Mixed Q4 and explicitly lifted S1
words retain separate generator namespaces and one Q4 matrix-action domain.

Eight focused SSM-0 tests passed before the detached campaign. The runnable demo
recovers (1,2,3,11) from unique current state (11,1,3,-2), then separately checks
the S1 lift/inverse family round-trip. Repository qualification remains pending
the frozen detached campaign's terminal marker.
