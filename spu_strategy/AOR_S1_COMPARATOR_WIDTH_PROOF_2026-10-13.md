# AOR-S1 comparator and adjustment width proof

**Status:** PROPOSED proof artifact; independent review pending, not executable qualification.

```bash
sed -n '1,240p' spu_strategy/AOR_S1_COMPARATOR_WIDTH_PROOF_2026-10-13.md
python3 tools/doc_audit.py --actual-pass 238
```

Applies to the [finite-profile amendment](contract_aor_s1_finite_profile_amendment_2026-10-13.md).
No floating-point ratio, division or logarithm is required by this comparator.

## Exact sign kernel

For p+q sqrt(3), test p=0, then q=0, then whether their signs agree.
If they disagree, calculate p*p, q*q, 3*(q*q), then compare p*p with
3*(q*q). The larger term supplies the sign. A nonzero integer pair cannot
tie, since 3 is not a rational square. Zero returns sign0.
This kernel uses no multiplication of two surd expressions.

## Exact balance comparator

Let alpha=sign(a+b sqrt(3)), beta=sign(a-b sqrt(3)). For nonzero m both
are +/-1. Compute them with the exact sign kernel, not trusted annotations.
Set A=alpha*a, B=alpha*b, C=beta*a, D=-beta*b. These are the coefficients
of |x| and |x'|, respectively, and remain in signed280 comparison workspace.
Negating signed136 minimum must not be performed in signed136 first.

Lower comparator: sign(U|x|-|x'|). Calculate, in order:
`2A`, `3B`, their sum, subtract C to obtain p;
`2B`, add A, subtract D to obtain q; then sign(p+q sqrt(3)).
Negative means ratio below U^-1. Zero belongs to the interval.

Upper comparator: sign(|x|-U|x'|). Calculate, in order:
`2C`, `3D`, their sum, subtract from A to obtain p;
`2D`, add C, subtract from B to obtain q; then sign(p+q sqrt(3)).
Nonnegative means ratio at or above U and requires adjustment.

These comparisons are between positive embedding magnitudes. They correctly
handle both signs of N. They never divide by x', nor square a norm expression.

## Expression-by-expression bounds

Let M=2^135, so signed136 a,b satisfy |a|,|b|<=M. All expressions below
are evaluated in signed280, including the preliminary signed absolute values.

| Expression, in evaluation order | Magnitude bound | Sufficient signed width |
|---|---|---|
| A,B,C,D | M | 137 |
| 2A or 2C | 2M | 138 |
| 3B or 3D | 3M | 138 |
| First coefficient sum | 5M | 139 |
| p after subtraction | 6M | 139 |
| 2B or 2D | 2M | 138 |
| Second coefficient sum | 3M | 138 |
| q after subtraction | 4M | 139 |
| p*p | 36M^2 | 277 |
| q*q | 16M^2 | 276 |
| 3*(q*q) | 48M^2 | 277 |
| Compare p*p with 3*(q*q) | No additional product | 277 |

For norm/sign of the original a,b: squares <=M^2, three times the second
square <=3M^2, and their difference has magnitude <=3M^2; signed273 suffices.
Every expression in this table fits signed280. The kernel must not accept
arbitrary signed280 p,q for squaring: its precondition is the bounds above.
A wider input profile requires a new proof, not reuse of this conclusion.

## Both unit-adjustment directions and intermediate order

Stored operands satisfy |a|,|b|,|c|,|d|<=S=2^63. In multiplication:

| Expression | Magnitude bound |
|---|---|
| ac, bd, ad, bc | S^2 |
| 3bd | 3S^2 |
| A=ac+3bd | 4S^2=2^128 |
| B=ad+bc | 2S^2=2^127 |

For U adjustment, evaluate `2A`, `3B`, sum; then `2B`, add A.
For U^-1 adjustment, evaluate `2A`, `3B`, subtract; then `2B`, subtract A.
Both paths have intermediate bounds 8S^2, 6S^2, 14S^2 for the first
coefficient, and 4S^2, 8S^2 for the second. Signed131 suffices; signed136
therefore covers products and both local adjustments. Comparisons before and
after adjustment satisfy the separate signed136-input/signed280 proof above.

Conjugation of stored signed64 coefficients first promotes b, then negates:
|b|<=S fits signed136, including b=-2^63. A subsequent adjustment has bounds
5S and 3S. Equal-exponent sums have coefficients <=2S, so their first
adjustment has bounds 10S and 6S; unlike products, later adjustments are not
covered by the one-step theorem.

For a general signed136 current mantissa, adjustment intermediates can reach
5M and 3M, which exceed signed136. Check after each scalar action, preserving
temporary state and returning TEMPORARY_LIMIT on the first failure. This is
an admissible bounded refusal, not proof that normalization is impossible.
The comparison workspace's larger width does not widen coefficient storage.

## Local rebalance proof and preconditions

Balanced operand ratios are in [U^-1,U). Their product ratio is in
[U^-2,U^2). If below U^-1, multiplying the mantissa by U gives ratio in
[1,U). If at least U, multiplying by U^-1 gives ratio in [U^-1,1).
Otherwise it is already balanced. Thus at most one adjustment suffices.

Require actual validated balance on both operands. The proof does not license
one adjustment for arbitrary intermediates or unequal-exponent alignment.
Conjugation gives ratio in (U^-1,U]; only the upper endpoint needs adjustment.
Exponent-range failure remains possible even when this mathematical proof holds.
