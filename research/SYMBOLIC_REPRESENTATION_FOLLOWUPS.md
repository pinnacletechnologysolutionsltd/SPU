# Symbolic representation: two research questions

**Status: ideas for future work; no experiment or architectural change is
authorized by this note.** The central question is what mathematical information
a processor or compiler could retain so that later computation can be expressed
more simply. Expressiveness and computational cost are separate questions.

## Algebraic generators

For u = 2 + √3, N(u) = 1. Multiplication by u maps coefficients (a,b) to
(2a + 3b, a + 2b), corresponding to the matrix [[2,3],[1,2]]. A transformation
family can be described by an integer exponent n: T_n(v) = u^n v, with
T_m ∘ T_n = T_(m+n). Negative exponents use u⁻¹ = 2 − √3.

Could a generator and exponent express useful transformation families more
compactly than expanded matrices, while preserving independently checkable
relationships? This is established algebra, not a claim of novel mathematics
or a measured SPU advantage. Exponent addition can avoid expanding matrices
when the application only needs the symbolic composition; producing actual
coefficients still requires computation and their size grows with |n|.
Compare against direct matrix composition and exponentiation, including
representation size, checking costs and the operations the application needs.
The representation covers this generated family; it does not by itself
represent every norm-preserving transformation.

## Certified coefficient bounds

Given explicit input coefficient bounds and an operation sequence, can a
reusable proof bound every relevant intermediate coefficient and thereby
justify a narrower representation or removal of a particular runtime check?
Compare proposed proofs against ordinary static range analysis, interval
arithmetic and direct solver analysis on the same workloads. Record proof
construction, checking and metadata costs as well as any eliminated checks.

An ideal mathematical bound is insufficient on its own: any proposed
application must match the actual fixed-width instruction semantics, intermediate
widths, overflow, truncation, normalization and refusal behavior, including
whether a failed operation changes state. Solver assumptions and counterexamples
must be explicit. No hardware simplification has been established here.

## Evidence and boundaries

[GEOM-1 findings](symreg_geom_1/FINDINGS.md) demonstrate bounded independent
checking of quadratic-form-preserving matrices, not an implementation of either
follow-up above. [SYMREG-5 findings](qaf_symreg_5/FINDINGS.md) retain the
unresolved authority-restart replay counterexample. Eager coherency metadata and
externally derived mathematical facts have different trust and maintenance
requirements; a current-state property bit is not automatically a theorem.

Certificate caching and general domain descriptors are parked. Neither this
note nor its examples change the Gen-1 CPU, ISA or v0.2 qualification.
