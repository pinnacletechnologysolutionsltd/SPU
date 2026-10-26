# ISA v0.2 — domain-and-semantics matrix (DRAFT, not normative)
Status: draft for review. Software/mathematical evidence only; no RTL or silicon claim. Changes no frozen ISA definition.
Sources (all in integration candidate cfb5c70 / branch e3ce5e6+): knowledge/isa_reference.md, research/field0, field1, gc_field0 FINDINGS,
research/sim_cap1_spread/GRAM_V1_CONTRACT_FROZEN.md, docs/BQ0_BIQUADRATIC_FINDINGS.md, docs/ICOS0_FINDINGS.md (master 1d010a6), docs/isa/ISA_IMPLEMENTATION_MATRIX.md.
"?" = not established by the evidence above; to be decided, not assumed.

## 1. Arithmetic domains (contract 1)
| Domain | Value / encoding | Equality & canonical form | Bound / width evidence | Zero divisors | Status |
|---|---|---|---|---|---|
| Q(√3) scalar surd (R regs) | (a,b) integers, a+b√3 | exact; `SNORM` canonicalizes (surd bank) | Python unbounded; C++ checks final int32 coefficients; surd bank (ENABLE_SURD_CPU) signed 64-bit a,b, unsigned positive 64-bit d | none (field) | implemented, profile-specific widths |
| Quadray over Q(√3) | 4 surd components, 1 gauge redundancy (common offset) | gauge-equivalence vs component equality: ? | as above | none | implemented |
| Z[φ] pairs | (a,b) = a+bφ; product (ac+bd, ad+bc+bd); conjugation (a+b,−b); no division | exact integer pairs | ICOS-0: unit icosians ½·Z[φ] entries; norm-2 roots fit 3 bits; unrestricted products grow ≈0.45 bit/step | none | IROTC/tensegrity implemented; icosian oracle software-only |
| A₃₁ = F_p[x,y]/(x²−3,y²−5), p=M₃₁ | 4 coefficients | mod p | fixed p | YES (split algebra); trapped by FLAGS.V | implemented; invertibility contract must NOT be reused for char-0 domains |
| Q(√3,√5) (BQ-0) | rational basis [1,√3,√5,√15]; integral golden basis [1,√3,φ,√3φ] | exact Fractions | 64-bit-input product coefficient ≈131 bits (scratch measurement, not a fixture) | none (field; N≠0) | software oracle only; NO fixed-width semantics |
| Integer lattices (A4, E8 8-lane) | integer vectors | exact | roots 2 bits; reflections 2; root products 3 | n/a | oracle only |
Rule: exactness in an unbounded oracle does not imply representability in a profile; every instruction must state its domain AND its profile bound.

## 2. Intrinsic metrics (contract 2)
| Form | Domain | Definition | Evidence / caveat |
|---|---|---|---|
| Quadray Gram | Quadray (integer or Q(√3) comps) | B(v,w)=4Σvᵢwᵢ−(Σvᵢ)(Σwᵢ); B(v,v)=quadrance | equals VM quadrance exactly (GRAM_V1 §1) |
| `legacy_dot` | Quadray | Σvᵢwᵢ | NOT a metric: spread(A,A)=8/9 for (1,0,0,0); `qualified:false` |
| gram_v1 spread | Quadray | N=B(v,v)B(w,w)−B(v,w)², D=B(v,v)B(w,w), unreduced | software conformance only; degenerate iff all four components equal |
| icosian/E8 form | 8-lane Z[φ]⊗ | B(x,y)=2(a+b)=2·Tr(λ·dot), λ=(5+√5)/10 | positive definite; roots B=2; software-only |
| Pell ROT/QROT (×(2+√3)) | Q(√3), Quadray | preserves x²−3y² (indefinite), NOT Euclidean quadrance | FIELD-0: Q 24 → 24(7+4√3); a similarity. Semantics UNRESOLVED. Implemented `QROT QRn` is in-place, one step, followed by `normalize()`; its preserved quantity is UNVERIFIED (source comment claims quadrance preserved, contradicting FIELD-0 for plain component scaling). Spec row `QROT Rd,Rs,n` is a different, scalar form |
| none defined | A₃₁, Q(√3,√5) | – | do not infer a metric from register width or shared basis |

## 3. Representation & canonicalization (contract 3)
Decide per domain: (a) canonical encoding, (b) equality (representation vs value), (c) when normalization is mandatory vs on request,
(d) bounded coefficient growth. Known: surd bank commits raw-fitting results unreduced, SNORM always canonicalizes (valid zero mapped);
overflow invokes exact normalization (isa_reference). Open: Quadray gauge canonicalization ?; Z[φ] canonical sign/denominator for ½-entries ?; BQ/icosian bases ?.

## 4. Refusal and machine-state effects (contract 4)
| Operation | Outcome classes | Destination state on refusal | Evidence |
|---|---|---|---|
| gram_v1 SPREAD (0x15) | OK / DEGENERATE_METRIC / OVERFLOW(final int32 only, C++) | pre-instruction state preserved except halt/fault status | frozen contract; C++ 4022 cases: OK 1253, OVERFLOW 2761, DEGENERATE 8 |
| Surd bank ops | SSTAT: OK, OVERFLOW=2, ENGINE_FAULT=3, BAD_ENCODING=4; SSTAT preserves last status | per surd-bank spec | isa_reference |
| A₃₁ inverse | FLAGS.V on zero divisor | RTL unit raises `flags_v`+`done` on zero norm and does not write `inv0..3`; consumer gating and architectural FLAGS readout: ? (no ISA-A encoding, no FLAGS word in either VM) | MATHEMATICAL_FOUNDATIONS §8.3; `spu13_fp4_inverter.v`; O6 findings |
| Python vs C++ vs RTL | differ today (Python unbounded) | must be profile-labelled, not unified silently | ISA_CONFORMANCE reports |
Principle: a profile states either "atomic: success or no architectural destination change" or lists permitted status/diagnostic writes. Existing profiles are not retro-fitted.

## 5. Instruction composition — native-status rule (contract 5)
An operation is native only if it offers a distinct semantic contract (atomicity, boundedness, certified metric behaviour, or a refusal class) that composition of existing primitives cannot express as conveniently.
| Candidate | Provisional | Reason |
|---|---|---|
| Gram spread (0x15, gram_v1) | already native; keep | atomic degeneracy refusal and certified metric identity; lowering would need explicit check ops |
| E8/icosian reflection s_r(x)=x−B(x,r)r | lower first | expressible via exact bilinear + vector ops; no distinct refusal contract yet |
| BQ-0 norm/inverse | defer | no fixed-width semantics exist |
| Pell ROT/QROT | decide metric semantics first | FIELD-0 similarity vs isometry unresolved |
SFL-0 (separate draft) is the test of rows marked "lower first".

## 6. Open decisions for the owner
1 Profile naming: legacy_dot vs gram_v1 default for ISA 0.2? 2 Quadray equality: gauge or component? 3 Is QROT a similarity (rename) or to be replaced? 4 Fixed-width semantics for Q(√3,√5) and icosian — in scope for 0.2? 5 Which profiles (Python/C++/RTL) must satisfy atomic refusal?

## 7. D1-A amendment cross-reference (documentation only)
Common-core vocabulary, extension profiles (`0x2A` SOM vs RPLU2, JSCR/NSA, Lucas/Neuro/SU3), the `POLY_STEP = 0xE0` encoding candidate and its VM/RTL semantic blocker, `QROT` operand form and `SNAP` vs FLAGS are recorded in `ISA_V0_2_REVIEW_DRAFT.md` §6.2–§6.5 and §9 (O9–O13). Reachability evidence with source locations: `ISA_V02_O6_FINDINGS.md` §D1. Nothing here changes an encoding or a frozen definition.
