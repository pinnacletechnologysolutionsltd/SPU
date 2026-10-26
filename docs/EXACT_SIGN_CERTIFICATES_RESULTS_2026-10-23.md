# Exact Sign Certificates for PH Curves — Exploratory Results (2026-10-23)

Status: exploratory, host-only, simulation-free. Not in the regression gate. Not independently qualified.
Script: `software/experiments/exact_sign_certificates.py` (`python3 software/experiments/exact_sign_certificates.py`).
Seed: 20261023 (single `random.Random`, deterministic). Exact `Fraction` arithmetic throughout.
Cost unit: counted operations (one de Casteljau lerp ≈ one multiply; Sturm counts multiplies). A proxy, not hardware cost.

## 1. Bernstein discovery vs verification (degree 4–8, positive, initial coefficients include negatives; 20 per degree)
- Midpoint bisection: R = C_discovery / C_verification = 1.00 at every degree. Checking a submitted tree replays the same splits.
- Degree elevation: R = 1.00 at every degree; discovery cost varied widely (mean elevation steps 3.4–19.6; up to ~480 lerps at degree 5).
- Negative finding: replaying a search is not a cheap certificate.

## 2. PH curvature (300 random quadratic U, V)
- Identity r'×r'' = 2W(U²+V²) held exactly in all 300.
- 158 trivial (initial Bernstein coefficients single-signed); 126 sign-changing (no sign certificate exists, refused); 16 nontrivial certified.
- On the 16: W certificate 6 counted operations vs 672 for the generic degree-6 numerator (~112x). Small sample.

## 3. Affine transformations (200 steps)
- 184 nonsingular, 16 singular (det A = 0, skipped); 85 orientation flips among nonsingular.
- Determinant rule cross~ = det(A)·cross held exactly in all 184; it needs no rediscovery (I_det = 0).
- PH representation lost (general A is not a similarity) in 177 of 200 steps (I_PH = 0.89): a PH-specific certificate would need rediscovery, the determinant-based sign rule does not.

## 4. Near-zero and exact zero, P = (t−1/3)² + ε (bisection)
- Depth 3, 6, 13, 26, 53 for ε = 1e-2, 1e-4, 1e-8, 1e-16, 1e-32 (roughly linear in log 1/ε); max bit length ~262 at 1e-32.
- ε = 0 (nonnegative, double zero): refused at depth cap 40; strict positivity admits a finite certificate, nonnegativity with a zero does not.

## 5. Sturm comparison (degree 4–8, 20 per degree; multiplies disc/ver)
| deg | bisection | Sturm | Sturm bits vs bisection |
|---|---|---|---|
| 4 | 16/16 | 53/47 | 31 vs 25 |
| 5 | 32/32 | 76/69 | 138 vs 30 |
| 6 | 21/21 | 98/89 | 66 vs 42 |
| 7 | 35/35 | 134/123 | 341 vs 44 |
| 8 | 36/36 | 154/142 | 180 vs 58 |
- Sturm costs ~3–4x bisection on these cases and has much larger coefficient growth; verification is ~90% of discovery.
- Sturm cost is flat in ε (18 mults at degree 2); bisection grows 9 → 159 mults for ε 1e-2 → 1e-32.
- Sturm decides ε = 0 in finite steps (not strictly positive); bisection cannot.

## Conclusion
Structural certificates (low-degree PH form, determinant rule) are cheap and outlive transformations; subdivision-tree and Sturm-chain certificates are not cheaper to check than to find.

## Limitations
Operation-count proxies only; no hardware cost; no generalized-PH h(t) sign test; midpoint bisection only; small samples; no independently qualified outcome. No certificate framework or sum-of-squares campaign opened.
