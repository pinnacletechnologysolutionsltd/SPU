# SIM-CAP1 SPREAD profile — preparation (software-only, 2026-10-25)

Authorization: owner decision B for `spread()`; QROT separate and open. Preparation only:
no implementation, baseline regeneration, RTL change or execution campaign. Findings below
are from source reading plus one inline arithmetic check (no files written by it).

## 1. Decision recorded
* Legacy `spread()` stays reproducible, labelled **unqualified**.
* New profile defines `B(a,b)=4*sum(a_i b_i)-sum(a_i)*sum(b_i)`, `spread=1-B(a,b)^2/(B(a,a)B(b,b))`,
  as numerator `B(a,a)B(b,b)-B(a,b)^2`, denominator `B(a,a)B(b,b)` (unreduced, as legacy).
* Do not touch QROT/`rotate()`; no `PELL_SCALE` rename now.

## 2. Normalization check (requested)
`quadrance() = sum_{i<j}(a_i-a_j)^2 = 4*sum(a_i^2)-(sum a_i)^2 = B(a,a)` exactly (factor 1,
algebraic identity for 4 components, valid over Q(sqrt3) since the ring is commutative).
Consistent: no rescaling needed. Legacy defect is only `dot()` = sum a_i b_i != B(a,b).
Consequence: legacy spread(A,A) = 1-(sum a^2)^2/Q^2 != 0 generally; Gram gives exactly 0.

## 3. Boundary inventory (what a profile switch must cover)
| Site | Legacy behaviour | Note |
|---|---|---|
| `spu_vm.py:508` `QuadrayVector.spread` | defect | python method |
| `spu_vm.py:1952` SPREAD opcode 0x15 | calls method; writes R[d], R[d+1] | `--proof` branch (~1960) prints sum a^2 as "|v|^2", a *third* inconsistent form; must follow the profile |
| `software/common/include/spu_quadray.h:135` | same defect, comment says "matches spu_vm.py" | `cross_validate.py` pins Py==C++ parity |
| `knowledge/isa_reference.md:130` | SPREAD documented as `QRd,Q1,Q2,Q3` (three quadrances) | conflicts with VM/assembler `RQQ` (ISA_CONFORMANCE_2026-10-10 line 57: "freeze canonical intent") — must be resolved in the profile spec, not by this prep |
| `docs/isa/ISA_IMPLEMENTATION_MATRIX.md:29` | SPREAD "implemented" in RTL columns, "partial/unresolved by core" | RTL semantics NOT inspected; no RTL claim made |
| `spu_compiler.py` | emits no SPREAD | compiled programs unaffected by SPREAD (they are affected by QROT, out of scope) |
| `examples/02_quadray_orbit/quadray_orbit.sas:92` | uses SPREAD | working-tree diff already modified by someone else; do not attribute |
Existing `VM_PROFILES=("full","base")` is the *hardware-feature* axis (REGEN). Overloading it would
make `base`/`full` x spread-semantics multiply. Proposal: orthogonal field `metric_semantics`
in `capability_manifest` (`legacy_dot` | `gram_v1`), default `legacy_dot`, so every existing
default run, compiled program and historical evidence is bit-identical.

## 4. Pinned legacy expectations (must survive unchanged under `legacy_dot`)
* `spu_vm_test.py:307-308`: spread(A,A) with A=(1,0,0,0) -> 8/9 (itself the defect, now documented).
* `test_verification.py:test_spread_8_9`: face (1,1,1,0) vs vertex (1,0,0,0) -> 8/9 (agrees in both).
* `cross_validate.py` quadrance_spread R2/R3 and the Py==C++ spread parity.

## 5. Proposed `gram_v1` test set (expected values from the Gram formula, independent of the VM)
Numerator/denominator unreduced; raw pairs computed by hand-checkable integer arithmetic:
| a | b | legacy | gram_v1 | note |
|---|---|---|---|---|
| (1,1,1,0) | (1,0,0,0) | 8/9 | 8/9 | accidental agreement; keep |
| (1,0,0,0) | (0,1,0,0) | 9/9 | 8/9 | |
| (2,0,0,0) | (0,0,1,1) | 48/48 | 32/48 | |
| (3,1,0,0) | (1,2,0,5) | 1319/1344 | 1200/1344 | |
| (1,0,0,0) | (1,0,0,0) | 8/9 | 0/9 | self-spread must be 0 |
| (1,0,0,0) | (2,0,0,0) | 32/36 | 0/36 | collinear |
| (1,1,1,1) | any | den 0 | den 0 | zero-metric vector, see s6 |
Add: symmetry spread(a,b)=spread(b,a); invariance under the 24 cyclic/permutation
transforms (permutations preserve B); translation by (t,t,t,t) leaves B unchanged
(B depends only on differences) — this one is the discriminating property legacy fails;
one surd-valued pair (components with b-lane != 0) with a Q(sqrt3)-checked denominator.
Independent oracle: `fractions.Fraction` over integer inputs plus a second derivation via
`spread_from_quadrances(Q1,Q2,Q3)` with Q3=B(a-b,a-b) (triple-quadrance route, different code path).

## 6. Specification items to freeze (open, need owner sign-off before any code)
1. Zero denominator: B(a,a)=0 or B(b,b)=0 iff all components equal (including (t,t,t,t), a
   nonzero-component but zero-*metric* vector; legacy docstring says "zero vector"). Proposed:
   denominator 0 returned unreduced with numerator 0 (as legacy shape), plus a flag/fault?
   Which one is an ISA/fault-semantics decision (FLAGS.V exists for A31 traps).
2. Overflow: `RationalSurd` is Python-unbounded in the VM but int32 in the C++ VM and bounded
   in RTL registers; product B(a,a)B(b,b) is degree 4 in inputs. Need a stated input bound
   and refusal rule (C++ "unchecked arithmetic limits" per conformance report).
3. Exactness: spread is a rational function; result remains an exact (num,den) pair, never
   reduced or divided. Reduction (gcd) stays a consumer choice, as in legacy.
4. Operand form: resolve `QRd,Q1,Q2,Q3` (ISA doc) vs `Rd,QRa,QRb` (VM/assembler) in the spec.
5. Selection mechanism: constructor/flag on the VM (and C++ equivalent) vs separate opcode.
   Same opcode 0x15 with a profile flag keeps encodings stable; a new opcode needs ISA allocation.
6. Manifest: add `metric_semantics`, feature `spread` support=`implemented` only for gram_v1
   once its tests exist; legacy listed `implemented` with an explicit `qualified: false`
   note. Evidence stays `null` until runs exist.

## 7. Not authorized / not done
Implementation, test files, baseline regeneration, C++ change, RTL inspection of `SPREAD`,
any silicon claim, QROT/`rotate()` decisions, commit. Nothing was staged.
