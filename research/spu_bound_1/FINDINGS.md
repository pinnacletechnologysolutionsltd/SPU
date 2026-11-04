# SPU-BOUND-1 findings

**PASS — BOUNDED DISCOVERY.** In these finite domains, polynomial identities preserve nonlinear relationships that ordinary intervals lose. Expansion alone does not always yield sharp bounds; factoring the norm made F3 sharp. The results support investigating compiler-side symbolic reasoning, not a hardware change or an instruction substitution.

## Bound precision

All independent variables have integer range [-2,2]. Pairs below are coefficient intervals (A,B). Overapproximation is visible as the extra interval beyond the exact column; endpoints are inclusive. Enumeration checks 625 inputs for F1 and F3, 25 correlated inputs for F2 and F4, five inputs for F5, and one for F6. The oracle evaluates every arithmetic stage separately and agrees with both final polynomial evaluations on all registered points. Polynomial bounds contain every enumerated result. Interval propagation also contains every result.

| Fixture | Independent intervals | Expanded polynomial bound | Exact enumeration | Final nonzero polynomial terms A/B |
|---|---|---|---|---:|
| F1 xy | ([-16,16],[-8,8]) | same | same | 2/2 |
| F2 x conjugate(x) | ([-16,16],[-8,8]) | ([-12,4],[0,0]) | same as polynomial | 2/0 |
| F3 (xy) conjugate(y) | ([-80,80],[-48,48]) | ([-32,32],[-32,32]) | ([-24,24],[-24,24]) | 2/2 |
| F4 c=a,d=-b | ([-16,16],[-8,8]) | ([-12,4],[0,0]) | same as polynomial | 2/0 |
| F5 a² | [-4,4] | [0,4] | [0,4] | 1 scalar term |
| F6 xU U⁻¹ | ([M,M],[0,0]) | same | same | 1/1 |

M=2⁶³−1. In F3 the norm-factored expression x(c²−3d²) gives ([-24,24],[-24,24]), matching the oracle. This bound follows from N(y)∈[-12,4] and a,b∈[-2,2]; those maxima are attainable. F4's baseline correctly uses independent interval arithmetic on the projected coefficient intervals, deliberately dropping the relation. Its oracle and polynomial substitution enforce it; the comparison does not claim the original domain was independent.

F1 shows no improvement: each coefficient is multi-affine over the independent rectangle, and its extrema occur at corners. More generally a multi-affine function on a box is affine in each variable separately, so successive endpoint choices attain extrema at corners. That argument does not apply to repeated variables: for a² on [-2,2], corners both give 4 but the interior a=0 gives 0. Treating repeated occurrences as independent yields the sound but loose [-4,4]; claiming the corner-derived lower bound 4 is unsound.

## Work, state and widths

The executable prints per-fixture counters and fresh single-run timings. One sample (nanoseconds; interval, polynomial construction, polynomial bounding, oracle enumeration, checking): F1 40,916 / 51,353 / 56,136 / 2,381,358 / 7,819,000; F2 26,481 / 61,853 / 21,180 / 311,668 / 264,888; F3 38,839 / 92,062 / 45,178 / 3,722,161 / 7,288,726; F4 18,323 / 41,823 / 16,482 / 204,846 / 172,001. F3 norm-bound calculation alone took 30,106 ns. F5 and F6 combined calculation times including printing were 22,800 and 127,123 ns; their components were not separately timed. These single observations include interpreter and instrumentation overhead and are not performance comparisons or claims.

For F1/F2/F4, R1 does five interval multiplications and two interval additions; F3 doubles these. Each interval multiply evaluates four endpoint products; an interval addition evaluates two endpoint sums. R2 construction performs 5 term products and 7 coefficient additions for F1/F2/F4 and 15/21 for F3; bounding costs respectively 8/4, 2/2, 8/4, 2/2 interval multiplications/additions. These counts exclude exponent-vector bookkeeping, zero checks, comparisons, powers, negations and allocation. For F5, R1 uses one interval multiply; its symbolic monomial uses one term and one square-range calculation; the oracle calculates five squares. F6 uses two R1 Surd multiplications, and its two retained polynomial terms are the original variables after cancellation. The F6 symbolic construction and timing are included in the combined sample above, not separately counted. Each oracle Surd multiplication loops over four basis products, doing eight scalar multiplies and four accumulations including multiplication by 1; F3 and F6 use two per input, other Surd fixtures one. Checking is separately timed and verifies polynomial values and interval containment; it is not included in the listed derivation counts. SMT has five positive integer queries, four negative integer controls and one bit-vector query, with process startup times below.

R1 retains four endpoints per Surd value. R2 retains original variable identities and domains, plus coefficient/exponent records for each term; F4 additionally needs the input relation or its substitution. R3 retains input and intermediate values during enumeration; Z3 retains encoded variables, constraints and expressions, with internal storage unmeasured. Host object overhead is not measured. These costs are representation descriptions, not hardware register estimates.

Maximum signed widths for exact intermediate coefficients / explicit oracle products and sums are F1 6/6, F2 5/5, F3 6/7 and F4 5/5 bits. For F5 the square and its product need 4 bits; for F6 final coefficients need 64 bits, first-step coefficients 65, and explicit products and sums across both stages 66. The latter are mathematical unbounded intermediates, not measured internal RTL datapath widths. Polynomial construction, bound endpoint arithmetic, solver internals and Python object widths are not included in those peaks.

## Solver evidence and negative controls

Z3 4.15.5, integer QF_NIA, all a,b,c,d constrained to [-2,2]. Five checks for counterexamples were UNSAT: F1 coefficient bounds, F2 imaginary cancellation, F3 norm identity, F3 final bounds, and F4 cancellation assuming c=a,d=-b. Four deliberately wrong controls were SAT: wrong multiplication coefficient (a=0,b=-1,c=1,d=-1); assuming cancellation without the correlation (same witness, B=-1); corner-only a²≥4 (a=0); and wrong norm sign (c=1,d=-1). Thus each control is falsifiable and exercised. The SMT files specify the precise formulas. These checks do not prove the Python implementation, general nonlinear bounds, or machine behavior.

A separate 64-bit QF_BV formula proves by UNSAT that fixed-width 2M wraps to -2. It does not encode signed overflow detection, Gen-1 normalization, status or refusal. The integer solver process took 0.082 s wall time and bit-vector process 0.096 s in one sample, including startup. The internal Z3 limit was 25 s and external limit 30 s, with 1 GiB virtual memory per process.

## Finite-width interpretation

F6 uses the exact MATHSTATE-0 F3 operation sequence: x=(M,0), U=(2,1), then U⁻¹=(2,-1). The final mathematical tuple fits, but the first exact coefficient 2M needs 65 signed bits. Existing [MATHSTATE-0 evidence](../mathstate_0/FINDINGS.md) reports first-instruction status 2 and unchanged valid destination in that trace. Our unbounded oracle continues mathematically and is not an instruction simulator. A mathematical final bound does not establish correct intermediate widths, normalization/rescue, status, validity or destination behavior; it does not authorize substitution. Algebraic field norm here is unrelated to the Gen-1 SNORM tuple-normalization instruction.

## Interpretation

Conjugate cancellation and the norm factor survived symbolic multiplication when variable identity was preserved. Independent intervals lost both this cancellation and F4's cross-input relationship. F2/F4 and F3 gained tighter bounds; F1 did not. Norm factoring avoids evaluating a two-stage Surd product when an exact algebraic result is sufficient, but preserving variable identity, domains and correlations is essential. Expansion and term-wise bounding still lose dependence among terms, and term counts and solver effort may grow for larger compositions; no general scalability result is established. A compiler-side exact norm/rewrite primitive could be worth studying under separately verified finite-width, status and observability conditions. This experiment demonstrates no reason to introduce hardware.

## Reproduction

HEAD `71adca8`, unrelated pre-existing work in checkout; Python 3.10.12. No floating-point is used in the mathematical calculations; timings are integer nanoseconds. No Vivado or production code used. Commands:

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.spu_bound_1.test_model -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.spu_bound_1.measure)
(ulimit -v 1048576; time timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/spu_bound_1/verification.smt2)
(ulimit -v 1048576; time timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/spu_bound_1/bitvector.smt2)
```

Five tests passed. Integer results: UNSAT ×5, SAT ×4; bit-vector result: UNSAT. No random seed or sampling. Solver results and finite observations do not constitute independent architectural qualification.
