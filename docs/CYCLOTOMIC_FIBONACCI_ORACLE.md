# Exact Fifth-Cyclotomic Fibonacci Oracle

**Status:** `GO_ORACLE_COMPLETE` — Phase 0 host oracle independently audited
2026-07-30; no RTL authorized

**Implementation:** `software/lib/cyclotomic_fibonacci.py`

**Verification:** `software/tests/test_cyclotomic_fibonacci.py`

## 1. Scope

This oracle asks one bounded question: can the complete multiplicity-free
Fibonacci `F/R` catalog and its three-anyon braid representation be evaluated
exactly in a rank-4 integral fifth-cyclotomic basis, with characteristic-zero
truth kept separate from a fixed-width modular image?

It is not a many-anyon simulator, a quantum controller, or an RTL contract.
Fusion-space growth remains exponential, and no hardware work follows without
a named workload that needs deterministic latency or a modular verification
channel.

## 2. Characteristic-zero coefficient domain

Let `zeta = zeta_5` and

```text
Phi_5(x) = x^4 + x^3 + x^2 + x + 1.
```

Every algebraic integer is stored canonically as four unbounded Python
integers:

```text
c0 + c1*zeta + c2*zeta^2 + c3*zeta^3.
```

Multiplication is integer convolution followed by the exact rule

```text
x^4 = -(x^3 + x^2 + x + 1).
```

No floating point, denominator, or modular reduction occurs in this layer.
The implementation also exposes the four Galois automorphisms, complex
conjugation `zeta -> zeta^4`, trace, and norm.

Multiply-by-`zeta` is a distinct operation:

```text
(a0,a1,a2,a3)*zeta = (-a3, a0-a3, a1-a3, a2-a3).
```

It is a shift plus broadcast-subtract, not a general convolution. In a
redundant five-lane encoding the Galois action can be expressed as a lane
permutation. In the canonical four-lane power basis required here, eliminating
`zeta^4` makes each nontrivial automorphism a fixed integral linear transform,
not a pure permutation.

The real golden-ratio subring embeds as

```text
phi^-1 = zeta + zeta^-1 = (-1, 0, -1, -1)
phi    = 1 + phi^-1      = ( 0, 0, -1, -1).
```

## 3. Integral gauge and metric

The oracle freezes the integral gauge

```text
F = [[phi^-1,  1],
     [phi^-1, -phi^-1]]

R = diag(zeta^3, -zeta^4).
```

`F^2=I` exactly, and every entry lies in `Z[zeta_5]`. This basis is not
orthonormal: `F` does not preserve the ordinary identity metric. It preserves

```text
G = diag(1, phi)
```

instead:

```text
F^dagger G F = G
R^dagger G R = G.
```

This is a basis/gauge change from the standard unitary matrix, not a claim that
the physical representation is non-unitary. Any consumer must carry the
metric contract; treating the coefficient lanes as an ordinary Euclidean
vector is a type error.

## 4. Coherence checks

The test does not substitute a local matrix identity for category coherence.
It constructs all admissible fusion-tree bases for the Fibonacci rule

```text
tau x tau = 1 + tau
```

and compares the two associator paths around the full Pentagon. It separately
constructs both directed Hexagon paths from associators and `R` symbols.

Pinned coverage:

- 27 admissible Pentagon sectors;
- 24 directed Hexagon identities;
- zero residuals;
- exact inverses for both braid generators; and
- `sigma1 sigma2 sigma1 = sigma2 sigma1 sigma2` exactly.

## 5. Declared braid corpus and growth gate

The deterministic corpus contains 100 words covering lengths
`1,2,3,5,8,13,21,34,55,100`: five structured patterns and five independent
fixed-LCG stream words per length. It includes generator powers, alternating
words, inverse alternation, commutators, and mixed signed generators.

Growth is reported **by class**, because three of the five structured patterns
generate finite cyclic subgroups — `sigma1` and `sigma2` have order 10 and
`alternating` has order 15 — so their coefficients cannot grow at any length.
Crediting a corpus-wide maximum to those words would overstate the evidence.
Only `inverse_alternating` and `commutator` grow among the structured
patterns, and the generic bound rests on the 50 stream words.

Current measured maxima at length 100:

```text
structured  55 signed coefficient bits (inverse_alternating_100)
generic     14 signed coefficient bits (50 independent stream words)
```

All corpus results fit signed 64-bit coefficients. This is a measured corpus
bound, not a proof that all length-100 braid words fit 64 bits. The finite
orders are themselves pinned by the test, so the corpus cannot silently become
inert if the patterns are edited later.

The test prints explicit `G1`-`G5` verdicts matching the private audit
contract: coherence, inverses, metric, growth, and modular agreement. A failed
gate terminates the oracle with a nonzero exit status; cases are never dropped
to obtain a pass.

## 6. Modular image and the 521 prohibition

The modular type is deliberately separate from `Zeta5`. For prime `p != 5`,
the factor degree of `Phi_5` is the multiplicative order of `p` modulo 5, so

```text
Phi_5 irreducible over F_p  <=>  p == 2 or 3 (mod 5).
```

Consequences:

- `521 == 1 (mod 5)`: `Phi_5` splits. The test pins its four primitive roots
  `25,104,396,516` and constructs two nonzero quotient elements whose product
  is zero. The Lucas MAC modulus must not be reused for a field-valued
  cyclotomic backend.
- `M31 == 2 (mod 5)`: `Phi_5` is irreducible and the quotient is
  `F_(M31^4)`. This reuses the project's M31 scalar multiplier semantics
  without conflating the existing split-biquadratic `A31` basis with the new
  cyclotomic basis.

For every corpus word, direct M31 evaluation is checked against reduction of
the independently evaluated characteristic-zero matrix. Agreement proves the
implementation is a homomorphic modular image on the corpus; it does not make
one residue a lossless encoding of an unbounded amplitude.

The runtime types expose and preserve three distinct typestates:

```text
CHARACTERISTIC_ZERO_RING  Z[zeta_5]
MODULAR_FIELD             F_p[x]/Phi_5, Phi_5 irreducible
MODULAR_QUOTIENT_RING     F_p[x]/Phi_5, Phi_5 reducible
```

Mixed characteristic-zero/modular arithmetic and mixed moduli are rejected.

## 7. Run

```bash
python3 software/tests/test_cyclotomic_fibonacci.py
```

The canonical success marker is:

```text
CYCLOTOMIC FIBONACCI ORACLE: ALL CHECKS PASS
```

## 8. Independent audit closure

The independent review completed on 2026-07-30 and cleared all five
predeclared gates against the 48-check audited baseline:

- `F^2 = I` and `F^dagger G F = G`, with `G = diag(1, phi)`, were re-derived
  independently over `Z[phi]`;
- the integral gauge was checked as a diagonal change of basis from the
  standard unitary gauge, so the coherence identities carry across without
  introducing `sqrt(phi)` into the stored coefficients;
- `M31 == 2 (mod 5)`, the four primitive fifth roots modulo 521, and the
  explicit 521 zero-divisor witness were independently reproduced;
- mutation testing confirmed that the Pentagon and Hexagon checks are
  non-vacuous; and
- the characteristic-zero/modular agreement and the declared length-100
  coefficient-growth corpus were reviewed without dropped cases.

The review therefore closes the contracted host-oracle tranche. It does not
authorize a cost model, RTL, synthesis, or board work.

Growth-attribution hardening performed at closure expanded the deterministic
corpus from 60 to 100 words and the focused suite from 48 to 52 checks. It
pins the finite orders of the inert structured families and reports the 50
generic streams separately. This strengthens G4's evidence without changing
the arithmetic, gauge, coherence construction, or modular domain reviewed
above.

### 8.1 Why this does not generalize to one interchangeable CMAC field

For a prime `p` not dividing `n`, every irreducible factor of `Phi_n` over
`F_p` has degree `ord_n(p)`. The complete cyclotomic polynomial can be
irreducible only when `(Z/nZ)^*` contains an element of order `phi(n)`.

| `n` | `deg Phi_n` | maximum unit order | best factor degree |
|---:|---:|---:|---:|
| 5 | 4 | 4 | 4 |
| 8 | 4 | 2 | 2 |
| 12 | 4 | 2 | 2 |
| 16 | 8 | 4 | 4 |
| 24 | 8 | 2 | 2 |

Thus the fifth-cyclotomic modular image can be a degree-4 field, while the
`Phi_8`, `Phi_12`, `Phi_16`, and `Phi_24` power-basis quotients cannot be
fields of their full characteristic-zero ranks for any prime. A modular
implementation of those quotients must expose their factor/CRT structure and
zero divisors as part of its type contract. Changing only a reduction mask
would not make inversion, norm, or fault semantics interchangeable.

The existing SU3 sidecar is not a rank-4 `Q(zeta_12)` engine. Its source
declares a degree-8 modular `A31[i]` element over M31 at
`hardware/rtl/core/spu13/spu13_su3_mult.v`; that is the authoritative domain
pointer. The earlier project decision also remains in force:
`docs/SESSION_HANDOVER_2026-07-28.md` records photonic/CV outreach as the
wrong immediate target because `phi` has no privileged role there.

## 9. Stop gate and future work

Phase 0 ends with this independently audited oracle. Before any cost model or
RTL:

1. identify a real braid-word consumer and its latency or determinism need;
2. define whether modular results are used only as verification residues or
   reconstructed via a proven coefficient bound; and
3. declare overflow, typestate, and fault behavior.

Without such a consumer, the correct disposition is to retain the oracle as a
published-gap closure and stop.

## References

- Field and Simula, *Introduction to topological quantum computation with
  non-Abelian anyons*: <https://arxiv.org/abs/1802.06176>
- Kawagoe and Levin, *Microscopic definitions of anyon data*:
  <https://arxiv.org/abs/1910.11353>
- Experimental Fibonacci braid matrices in *Nature Physics*:
  <https://www.nature.com/articles/s41567-024-02529-6>
- Audit decision: `docs/FEASIBILITY_AUDIT_VERDICT_2026-07-29.md`
