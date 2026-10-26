# Wildberger §19 Taylor Translation vs Exact Sign Certificates (2026-10-23)

Status: exploratory, host-only, software-only; no ISA/RTL/FPGA/simulator/QCG-0 change; not an architectural acceptance campaign. One bounded comparison, then stopped.
Script: `python3 software/experiments/taylor_sign_certificates.py` (imports baselines from `exact_sign_certificates.py`; SymPy optional for the identity section; ~1 s). Fixtures fixed before running, depth cap 40 for every method, nothing tuned afterwards.

**Closeout: exploratory negative result for Taylor-based interval sign certification.** Registered fixture outcomes, counts and limitations below are unchanged. Taylor algebra itself (jets, tangents, multiplicity at a known root) is not rejected; see `docs/SPU_MATHEMATICAL_DELETION_LEDGER.md`.

## Book vs mine
- **Wildberger §19.1–19.3** (printed pp. 197–203, read from the supplied PDF): translate of a conic by B (Thm 118, coefficient formulas a1=a−2du−ev, …); Taylor conic = translate to put the point at the origin (standard conic, c=0); tangent line = the linear part (a0,b0) of the Taylor conic (Thm 119: ⟨a+2dx0+ey0 : b+ex0+2fy0 : ax0+by0+2c⟩); non-singular = a1 or b1 ≠ 0; "second order non-singular" = a quadratic part exists; same construction for cubics and higher. All valid over any field (char ≠ 2); **no calculus, no inequalities, no sign or positivity criterion anywhere in §19.** Re-verified symbolically: S1 (Thm 118 identity), S2 (Thm 119 = partial derivatives).
- **Mine**: everything about interval sign certificates, the M3/M4 methods, the Descartes↔Bernstein identity (S4), the contact-order check, the comparison itself. Wildberger does not discuss sign certificates.
- S3: Taylor shift coefficients = P^(k)(c)/k!, and shifts compose (n=4,6,8). S4: coefficients of (1+x)ⁿ p(1/(1+x)) are binomial × Bernstein coefficients (n=4,6,8).

## Methods (positivity of P on [0,1], exact rationals)
- **M1** Bernstein midpoint bisection (baseline; verify = tree replay, as before).
- **M2** Sturm chain (baseline).
- **M3** Taylor-centre: P(c+t)=Σaₖtᵏ; leaf criterion a₀ > Σ_{k≥1}|aₖ|hᵏ on |t|≤h (checkable by the triangle inequality; coefficient inspection alone is not used); refutation if a₀ ≤ 0. Independent verify: recompute each leaf's shift from the original P and check coverage of [0,1].
- **M4** Descartes/VCA: integer coefficients, Taylor shift by 1 (additions only), test "all coefficients of (1+x)ⁿp(1/(1+x)) positive"; independent verify recomputes each leaf from the original integers.
Counters: mul (true), add, shift (×2^k). Bits = bit length of the coefficient vector with common denominator cleared (same metric for all four).

## Results (23 fixtures, 20 strictly positive: 12 random positive deg 4/6/8 with negative Bernstein coefficients, near-zero (t−1/3)²+ε at 1e-2/1e-8/1e-32, a degree-6 triple-near-zero at 1e-2/1e-8, double zero, three double zeros, sign change, zero outside, trivial, min at 1/2)
Certified-fixture totals (build / verify):
| Method | certs / 20 positives | false certs | mul | add | shift | verify ops |
|---|---|---|---|---|---|---|
| M1 bisection | 19 | 0 | 0 | 1308 | 654 | 654 (replay) |
| M2 Sturm | 20 | 0 | 1561 | (not instrumented, ≈mul) | 0 | 1418 |
| M3 Taylor-centre | 19 | 0 | 7869 | 6375 | 0 | 7588 |
| M4 Descartes | 19 | 0 | 0 | 2900 | 250 | 2010 |
- Same single refusal for M1/M3/M4 ((t−1/3)²+1e-32, needs depth ≈53 > cap 40); Sturm certifies it at 18 mults (flat in ε), and decides both repeated-zero fixtures and the sign change finitely.
- M3 needs 2.5–3.4× more leaves than M4 (e.g. 36 vs 14, 48 vs 14) and ~7× the arithmetic of M1 (14,244 vs 1,962 counted ops); bits are larger than M1 (44 vs 29 on deg 8). The |aₖ| bound discards cancellation, so it is a coarser criterion than the sign structure in the Bernstein/Descartes form.
- M4 makes the **same decisions** as M1 (S4: identical sign test), with ~2× the additions (it shifts once to test and once to descend) and larger integer coefficients (35 vs 29 bits on deg 8) since it does not normalise. Zero true multiplications — but M1's midpoint split has none either (halving is a shift).
- Independent leaf verification is cheaper than construction for M3 (≈0.5×) and M4 (≈0.7×) because failed internal nodes are not re-visited; M1's replay verify equals its build (R=1, as in the earlier note). The comparison is *kind*-mismatched (independent vs replay), and the table says so.

## Order of contact (the one genuinely Wildberger-shaped result)
One exact Taylor shift at a known rational root exposes the multiplicity: first non-zero index 2 for (t−1/3)² at 1/3 and for the three-double-zero fixture at 1/3, 2/3, 1/2; index 0 (nonzero value) when there is no root. This is the §19.3 "order of non-singularity" idea in one variable. It is a *classification* (P = (t−c)²·Q locally), not a positivity certificate, and it needs the root supplied (Sturm/gcd gives it); then Q>0 can be certified by M4. This is the only capability here that bisection alone lacks.

## Verdict (stop point)
- **No Taylor-based method gives a structural advantage for interval sign certification.** M3 is valid but dominated; M4 is Bernstein in another coordinate system (S4) and costs more, not less. Sturm remains the stronger reference (decides zero cases; flat in ε; but larger coefficient growth at high degree, per the earlier note).
- The Taylor/translate machinery is useful as exact *local* structure (tangent, order of contact), not as an interval certificate.
- This does **not** overturn the earlier finding: the cheap certificates remain the structural ones (low-degree PH form; det rule).

## Caveats (not tuned away)
1. Baseline M1 has no endpoint-value refutation; M3/M4 refute when P(c)≤0 or p(0)/p(1)≤0 at a dyadic point. The three-double-zeros fixture has a root at the dyadic 1/2, so M3/M4 refute it instantly (21 and 56 ops) while M1 spends 840 lerps. This is a fixture/implementation asymmetry, not a method result.
2. Sturm add-counts are not instrumented (≈ mul assumed).
3. Operation counts are proxies; no hardware, timing or bit-width-datapath claim. Coefficient-bit metric is vector-level, not per-coefficient.
4. 23 fixtures, one seed (20261023); positivity only (no negativity, no multi-interval, no univariate-only caveat for the bivariate §19 content).
5. Depth cap 40 forced the 1e-32 refusal for three methods.
