# Wildberger First Pass: Spread Polynomials, Pell Traces, Lorentzian Velocity Addition (2026-10-23)

Status: exploratory, host-only; no ISA/RTL/simulator/hardware change; outside all qualified campaigns.
Verification: `python3 software/experiments/wildberger_spread_inventory.py` (needs SymPy 1.14, installed in a throwaway venv; not a repo dependency). 31 exact checks, all PASS, ~6 s. Check IDs below refer to it.

**Closeout (2026-10-23): exploratory mathematical PASS.** 31 symbolic checks over the stated finite ranges; not a proof of every indexed identity. Mathematical unification demonstrated; hardware simplification hypothesized, not demonstrated. Shared recurrence/identity does not imply shared datapath; domains, branch choices and orientation state still differ (Euclidean vs hyperbolic). No AOR, Pell or rotation mechanism is deleted. Not imported into QCG-0.

## Source status
- **Book text now read** (user-supplied PDF of N. J. Wildberger, *Divine Proportions*, Wild Egg 2005; §8.1–8.6 text, §23.4 on printed p. 242, checked against the rendered page). Verified book claims, each re-checked symbolically in section D of the script:
  - Definition and recurrence of S_n (§8.2); Thm 57 ({S_{n−1}, s, S_n} is a spread triple); Thm 60 S_n∘S_m = S_nm (§8.6, proved geometrically by reflection sequences, not via Chebyshev); the worked S_3, S_5, S_15 and the S_12 spread-cyclotomic factorisation (Ex. 8.5, 8.13) (D1–D3).
  - §23.4 states the velocity relation **in squared speeds** V=v², V1=v1², V2=v2²: (V1+V2−V−VV1V2)² = 4V1V2(1−V)² (23.11), with Newtonian limit (V1+V2−V)²=4V1V2 (23.9) and a symmetric form "quite close to the Triple twist formula (page 93)" (D4–D6). It does **not** use rapidity, ρ, or Möbius maps.
  - §24.2 states the triple-spread quadratic (s3 − (s1+s2−2s1s2))² = 4s1s2(1−s1)(1−s2), the same as my A5.
- **Independent derivations (not in the book as far as read)**: the Chebyshev form of S_n (A1), Pell/Lucas trace correspondence (section B), the ρ/Möbius parameter map (C1–C5), the S_n-of-σ formula for n-fold velocity (C6), and the exact identification D7 below.
- Classical references: Chebyshev T_n/U_n; Lucas sequences V_n(P,Q) and Dickson polynomials D_n(x,a); rapidity/Bondi k-factor.
- Caveat on provenance: an earlier text extraction dropped the square on (1−V) in (23.11); the rendered page shows (1−V)², and only that form is true (my first transcription failed a numeric check).

## A. Spread polynomials
Definition used: S_0=0, S_1=s, S_n = 2(1-2s)S_{n-1} - S_{n-2} + 2s, so S_n(sin²θ)=sin²(nθ).
| Claim | Assumptions | Field/ring | Check |
|---|---|---|---|
| S_n(s) = (1 − T_n(1−2s))/2 | none (polynomial identity), n≤16 | Z[s] | A1 |
| S_n ∈ Z[s], S_n(0)=0, S_n(1)=n mod 2 | n≤12 | Z | A2 |
| S_m∘S_n = S_mn | m,n≤6 (finite check; general proof follows from A1 + T_m∘T_n=T_mn) | Z[s] | A3, A4 |
| Spreads of α±β are the two roots of (x−a−b+2ab)² = 4ab(1−a)(1−b) | a=sin²α, b=sin²β, reduced modulo sin²+cos²=1 | Q(a,b) extended by the quadratic | A5 |
Preserves: sin² of the angle. Loses: sign of the angle and angle mod π; consequently S_{m+n} is **not** a function of S_m, S_n (A5: two roots, one sqrt-level choice). Composition only gives the multiplicative structure (N,×), never additive angle composition, from spread alone.

## B. Trace correspondence for powers of ε = 2+√3
All in Q(√3) (ε has norm 1; ε⁻¹ = 2−√3 is its conjugate).
- ε^n = a_n + b_n√3 with a_n = T_n(2), b_n = U_{n−1}(2), a_n²−3b_n²=1 (B1, B2; n≤16).
- Trace t_n = ε^n+ε^{−n} = 2a_n = V_n(4,1): t_n = 4t_{n−1}−t_{n−2}, and tr M^n = t_n for M=[[2,3],[1,2]] (B3, B4).
- **Correspondence:** S_n(−1/2) = (1−a_n)/2 = (2−t_n)/4 (B5). Reason (derived): 1−2s = cos2θ = 2 ⇒ θ imaginary, s = −sinh²(φ/2)... with cosh(ln ε)=2, s = −1/2. Spread −1/2 is the "spread" of the Pell rotor; it is not a real sin² (hyperbolic angle).
- Doubling a_{2n}=2a_n²−1, b_{2n}=2a_n b_n is S_2=4s(1−s) in trace coordinates; the Pell octave r⁸=(18817,10864) is three doublings of (2,1) (B6, B7). Product-to-sum t_{m+n}=t_m t_n−t_{m−n} (B8).
- Information: trace/spread keeps one integer a_n (b_n recoverable only up to sign, b²=(a²−1)/3, B9); the Pell pair (a,b) keeps orientation and supports ε^m·ε^n directly.
- Q(√5) analogue: φ² has norm 1, trace 3, so L_{2k}=2T_k(3/2) and S_k(−1/4)=(1−L_{2k}/2)/2 (B10). Odd Lucas numbers are not Chebyshev values (φ has norm −1; L_n = D_n(1,−1)); parity of the exponent matters (B11).

## C. Lorentzian velocity addition (c=1)
u⊕v = (u+v)/(1+uv), field Q(u,v) (rational, no square roots needed).
- ρ(v)=(1+v)/(1−v) satisfies ρ(u⊕v)=ρ(u)ρ(v) (C1); equivalently the Möbius matrices [[1,u],[u,1]] close under multiplication up to scale (C2); inverse v=(ρ−1)/(ρ+1) (C3). ρ = e^{2φ} (rapidity φ); √ρ is the Bondi factor.
- ρ=2+√3 ⇔ v=1/√3, v²=1/3 (C4); n-fold v⊕…⊕v = (εⁿ−1)/(εⁿ+1) exactly (C5). Note v itself needs Q(√3); only v² is rational.
- **Link to spread composition (derived):** with σ(v)=−v²/(1−v²)=−sinh²φ, the squared n-fold velocity is −S_n(σ)/(1−S_n(σ)) for generic v (C6, n≤6). The u,w case: σ((u⊕w)²) and σ((u⊖w)²) are the two roots of the same quadratic as A5 (C7).
- **Exact bridge to the book (D7):** with σ=−V/(1−V), the numerator of the spread-combination quadratic (A5) in σ(V), σ(V1), σ(V2) is *identical as a polynomial* to the book's (23.11), over the denominator ((V−1)(V1−1)(V2−1))². So (23.11) is the triple-spread formula (§24.2) after the Möbius change of coordinate V→σ; the book's \"quite close to the Triple twist formula\" is made exact by this substitution (my derivation). Hyperbolic-angle reading: σ=−sinh²φ.
- Information: v² drops direction; (u⊕w)² ≠ (u⊖w)² generically, so squared state needs a root choice (C8), exactly as spread addition does.

## Classification
- **Identical algebraic mechanism:** (1) S_n, Chebyshev T_n and the trace of the n-th power of a norm-1 unit (B5); (2) n-fold velocity addition and the Pell power ε^n (C5), same power map on the rank-1 torus; (3) S_n in σ-coordinates and squared n-fold velocity (C6); the spread-combination quadratic and the velocity-squared one (A5/C7).
- **Related, different state:** velocity v / ρ (keeps sign, supports u⊕w) vs v²/σ (loses direction, supports only n-fold); Pell pair (a,b) vs trace a; norm +1 units (Chebyshev) vs norm −1 units (Lucas odd terms, Dickson Q=−1).
- **Superficial / unestablished:** The book does not use ρ or σ (D7 is my bridge); no claim about the repo's A₃₁ or Z[φ]/L_p arithmetic beyond B10; "octave = fractal" in PELL_OCTAVE.md is just the doubling map S_2 iterated (B6, B7), not additional structure.

## Architectural deletion / unification table (observations; no new opcode)
| Existing thing | Unification observed | Consequence (hypothesis, unmeasured) |
|---|---|---|
| Pell doubling (a,b)→(2a²−1, 2ab) | = S_2 in trace coordinate | one doubling datapath serves Pell octave and spread doubling |
| Trace-only ladder t_n = 4t_{n−1}−t_{n−2} | = V_n(4,1) = 2T_n(2) | a 1-integer state suffices for n-th power *traces*; cannot form products ε^m·ε^n without b (B8 needs both traces and t_{m−n}) |
| Velocity addition via Möbius; book (23.11) | = ρ multiplication; (23.11) = triple spread under σ=−V/(1−V) (D7) | ρ-coordinate makes n-fold sum a power; rational for rational v |
| Separate "spread polynomial", "Chebyshev", "Lucas" tables | one family: S_n=(1−T_n(1−2s))/2; V_n=D_n(P,Q) | duplicate coefficient tables could be generated from one recurrence; not measured |
| Spread composition S_m∘S_n=S_mn | no additive composition | cannot delete ROTC-style full rotors in favour of spreads |
No unavoidable new primitive found.

## Limitations
Finite-n symbolic checks (n≤16 / ≤8 / ≤6), not general proofs (general proofs follow from T_m∘T_n=T_mn and ρ-multiplicativity). Book read only for §8.1–8.6, §23.4 and §24.2 (not the rest). No hardware, resource or performance claim. No independent qualification.
