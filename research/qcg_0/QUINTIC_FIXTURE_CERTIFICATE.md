# QCG-0 independent fixture certificate

2026-10-22. Reviewer: fresh-context `/root/qcg0_fixture_reviewer`, independent of the author and HEX-SOM acceptance reviewer. Author calculator output seen: **no**. Scope: mathematical fixtures only. **Disposition: REVISE / CERTIFIED WITH CORRECTIONS.** The selected regular PH5 is mathematically certified. The packet as written cannot be certified: its curvature requirement contradicts its definition of N. No pilot, candidate, cost measurement, implementation acceptance or hardware claim is authorized by this review. No pinned document was edited.

## Source identity and calculation record

Read `REVIEW_CALCULATION_AUTHORIZATION.md` first; verified all four SHA-256 pins before mathematical calculations. Pins matched exactly. Read the entire packet and pre-registration, and the two pinned QSG-2 documents. Artifact hashes and complete argv are in `QUINTIC_FIXTURE_REVIEW_MANIFEST.json`; the manifest is outside the certificate to avoid a self-hash. Values SHA-256: `8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34`.

Two bounded invocations used of three allowed, both exit 0, no failures or timeouts. Each used `/usr/bin/timeout --signal=KILL 30 /usr/bin/prlimit --as=1073741824:1073741824 -- /usr/bin/python3 -B -I <script>`. Cumulative external ceilings consumed: 60 of 90 seconds; no third invocation used. First invocation reported 0.072382 seconds elapsed and 18,908 KiB maximum RSS. Second was readback only. Both stdout/stderr and exit records are preserved. `/usr/bin/timeout` 9.12, `prlimit` 2.42.4 and Python 3.14.8 were executable and invoked for their version before calculation; scripts were read and inspected before execution. No child processes, network, project helper imports or installations. Enumeration domain: 4096 tuples; only two resultants tested. Final JSON is 69,201 bytes; complete review outputs are far below 10 MiB. Exact polynomial products check the authorized coefficient-bit ceilings; the tiny fixed degrees and rational inputs do not approach them. Resource use is evidence of this fixture computation, not a candidate benchmark.

## F-A: selection and exact quintic

Frozen R-SEL applied literally, before any cost evaluation. First tuple `(-1,-1,-1,-1,-1,-1)` fails K2, K3, K4. Second tuple `(-1,-1,-1,-1,-1,1)` passes all four. Both have maximum magnitude 1 and absolute sum 6, so no earlier tuple in any other magnitude/sum stratum is possible. The complete rejection log is in the JSON. No widening or replacement selection rule.

U = −1−t−t²; V = −1−t+t². The independently evaluated 4×4 Sylvester determinant is Res(U,V)=4. Thus gcd(U,V)=1 over Q[t] and there are no simultaneous real roots. Therefore sigma=U²+V²>0 on all real t. Nonconstant U/V follows also from the nonzero Wronskian.

Ascending power coefficients and exact degree-5/degree-4 Bernstein controls are in the JSON. In readable form:

- x′=4t²+4t³; y′=2+4t+2t²−2t⁴.
- x=4t³/3+t⁴; y=2t+2t²+2t³/3−2t⁵/5.
- sigma=2+4t+2t²+2t⁴; S=2t+2t²+2t³/3+2t⁵/5.
- N_raw=UV′−U′V=−4t−2t²; D_raw=sigma².
- r(1)=(7/3,64/15); S(1)=76/15.

Coefficient identities x′²+y′²=sigma² and S′=sigma pass. Differentiating the coordinate coefficients gives cross(r′,r″)/sigma³=**2N_raw/D_raw**, verified exactly at 0, 1/7, 1/3, 1/2 and 1. True endpoint curvature pairs are (0,4) and (−12,100); hence kappa(0)=0 and kappa(1)=−3/25. N vanishes at 0 and −2. There is no interior inflection on [0,1]; the endpoint 0 is a simple zero and would be an inflection on an extended interval. Nonconstant curvature is certified by its different endpoint values.

K1 makes the generators dense but does **not** ensure dense derived coordinates: x has degree 4, y degree 5, and x′ has degree 3. This follows from the frozen rule and is not grounds for replacing the fixture after selection. Any claim that K1 prevents all sparsity advantages must be narrowed to generator coefficients.

## F-B: literal reference outputs and independent checks

`QUINTIC_FIXTURE_VALUES.json` contains all 16 ordered Cell A queries, including both repeats. `values` order is x,y,x′,y′,sigma²,sigma,S,N_raw,D_raw; `D_nonzero` is true for every row. The last pair deliberately retains the packet's literal definitions. It must **not** be called a true curvature numerator/denominator without doubling N. Each row additionally labels the corrected quotient explicitly. No frozen meaning was silently changed.

Both PH3 and PH5 have all 17 dyadic S1–S3 rows. S2_add order: x′,y′,sigma,T_x,T_y. S3 supplies true signed curvature and the next-interval arc increment for the 16 intervals. At k=16 the next increment is null because [17/16] lies outside the specified interval; the author must freeze a different endpoint convention if desired. All rational values use reduced numerator/positive-denominator pairs. Integers serving as discrete metadata are JSON integers.

Fresh Fraction convolution/integration is the primary route. A second route expands Bernstein basis polynomials coefficientwise back to power form, derives derivative controls from adjacent position controls, and evaluates by de Casteljau at each dyadic parameter. Exact finite-difference tables reconstruct every dyadic sample. Repeated synthetic division produces Taylor-shift coefficients and reverse composition recovers the source polynomial. These are review-only identity checks, without operation counting or candidate engines. Serialized JSON was reopened and compared to the in-memory canonical value tree; a second isolated invocation read it independently and printed endpoint/control/residual summaries. These checks provide method separation within this independent review, not a claim of a second human author.

## F-C: retiming

For PH3 the independently integrated coefficients give r=(t−t³/3,t²), sigma=1+t², S=t+t³/3. At 1/2 they give r=(11/24,1/4), sigma=5/4, T=(3/5,4/5), S=13/24, consistent with QSG-2.

phi=(4t+18t²+27t³)/49; phi′=(2+9t)²/49>0 on [0,1]; endpoints 0 and 1. Let q=−(2+9t)/7. H-form: (U_tilde,V_tilde,h_tilde)=(1,phi,phi′). Primitive form: (q,phi q,1). Both produce phi′(1−phi²,2phi) coefficientwise. Composite x,y,S degrees are 9,6,9 respectively; overall position degree is 9. Expanded polynomials and all 16 seven-value Cell B rows are recorded in the JSON. Composition, differentiated expanded coordinates and independently evaluated Bernstein forms agree exactly.

For phi_bad=4t−4t² the sign changes at 1/2, with stationary speed there. Put B(t)=phi_bad(t)+phi_bad(t)³/3. Oriented length is B(t). True accumulated traversal length is B(t) on [0,1/2] and 8/3−B(t) on [1/2,1]; total is exactly 8/3. Oriented total is zero. Both piece polynomials and all query values are recorded. `OUT_OF_DOMAIN` is the declared single-polynomial traversal-length class refusal; it does not mean that this piecewise-polynomial length or total rational length is mathematically uncomputable.

For phi_ns=t²: h-form (1,t²,2t) is valid; primitive form over Q is refused because 2t is not ±a rational-polynomial square. At t=0 the continued generator direction is (1,0), while the actual velocity divided by nonnegative speed is 0/0 and must refuse. For phi_rev=1−t, primitive generators (t−1,1) give the correct negative composed hodograph. Applying reversal twice negates the original generator and restores its squared hodograph. For PH3h, h=1+t is positive on [0,1] and its sigma and arc length are obtained by multiplying PH3's sigma by 1+t and integrating; no new physical qualification follows.

## F-D: independent proofs and corrections

R1: the chain rule gives psi′=phi′(h composed with phi)(w composed with phi)². Its squared Euclidean norm is the square of the real polynomial phi′(sigma composed with phi), regardless of its sign. Thus polynomial PH-class and h-form closure hold. The identically stationary case remains algebraically PH but fails regular-query admission.

R2: write g=U²+V². Actual speed is |h|g, not hg for negative h. After retiming it is |phi′(h composed with phi)|(g composed with phi). Signed speed phi′(h composed with phi)(g composed with phi) equals actual speed wherever its prefactor is nonnegative (including a zero). A stationary point is not regular. For a sign-changing prefactor the absolute value generally yields piecewise polynomials; the registered phi_bad indeed does. Retimed parameters must remain in the original certified interval for its regularity certificate to apply.

**Negative-h correction:** the pre-registration's claim that the unit tangent is independent of h requires h>0. Actual unit tangent is sign(h)·w²/g at regular points; w²/g alone is a continued generator direction. Likewise the Euclidean signed curvature cross(r′,r″)/|r′|³ is 2(UV′−U′V)/(|h|g²). The printed 2N/(h g²) uses signed speed in the denominator and only agrees for h>0. Reversal/nonmonotone controls must distinguish these conventions.

R3: for a nonzero original primitive generator W in Q(i)[t], the composed generator is nonzero for nonconstant phi. If phi′W(phi)² is a polynomial square, each irreducible's exponent in phi′ is even by unique factorization; the constant unit is also a square because the quotient of the two squares lies in the fraction field. A rational function whose square is a polynomial has no denominator primes, so phi′=A² for A in Q(i)[t]. Write A=a+ib with a,b in Q[t]; real A² forces ab=0. Thus phi′=q² or −q². Conversely multiply W(phi) by q or iq respectively. Constant phi has phi′=0 and q=0 and satisfies the algebraic statement but is nonregular. An identically zero original W must be excluded from a necessity claim; regularity already excludes it in this experiment. A nonsquare positive rational constant such as 2 is not a square in Q(i), confirming the registered counterexample.

Reversal: phi′=−1=i²; iW(1−t) has real/imaginary parts (−V(1−t),U(1−t)). Its square is −W(1−t)². A second reversal gives −W, hence the same hodograph. This proves R5 without a numerical example.

**Completeness over Q is independently proved here; no external citation relied on.** Given X²+Y²=Z² in Q[t], first handle Y=0 separately using X=±Z and a constant generator (swap axes/sign if needed). Otherwise let d be the monic gcd of X,Y. Since d² divides Z², unique factorization implies d divides Z. Set A=X/d, B=Y/d, C=Z/d. Then gcd(A,B)=1 and gcd(A,C)=gcd(B,C)=1. Thus C+A and C−A are coprime polynomials up to nonzero rational units: a common prime would divide 2C and 2A. Their product B² implies C+A=alpha f² and C−A=beta g², with f,g in Q[t] and nonzero rational alpha,beta. Because B²=alpha beta f²g², its leading coefficient implies alpha beta=delta² for a rational delta (choose its sign so B=delta fg). Define h=d alpha/2, U=f, V=(delta/alpha)g. Then h(U²−V²)=dA=X, 2hUV=dB=Y, and h(U²+V²)=dC=Z. Zero triples and C+A=0 are covered by the elementary constant-generator cases. This establishes polynomial h,U,V over Q, with no rational-function denominator left. To obtain nonnegative Euclidean speed on a regular interval choose the sign of the polynomial Z positive there; h then is positive there. Completeness does not imply every curve has h=1 over Q.

## F-E: controls, ambiguities and required revisions

The join JSON supplies exact generator cross/dot, velocity, G1, cusp and C1 tests for the six stated next generators, relative to w_a(1)=(1,1), h=1. C1 holds for (1,1) and (−1,−1); (2,2) has G1 with a speed jump; (1,0) is a corner; (1,−1) is a cusp. The near-miss determinant is 1, so G1 is false. These are direction/velocity facts conditional on placing the next start at the preceding endpoint. G0 needs the placement. C2 and G2 require the next generator's derivative (and h derivative if nonconstant), which the packet does not supply. In a planar curve G0 uses two rational equalities, not four. A loop residual 1/10^6 is nonzero exactly.

The promised float64 misclassification is **not established by the fixed controls**. With absolute tolerance 10^−9, a closure residual 10^−6 is rejected even in ordinary floating arithmetic. The raw near-miss generator cross is 1; normalized tangent angular discrepancy is of order 10^−6, still above tolerance. The predicate and normalization must be fixed before any numerical control can have a literal expected classification. Do not change the fixture after observing a candidate.

For harmonic P′=V,V′=−P with an order-4 Taylor step, M(h)=[[a,b],[−b,a]], a=1−h²/2+h⁴/24, b=h−h³/6. M(−h)M(h)=(a²+b²)I. At h=1/4, a=5953/6144, b=95/384 and residual operator is **−127/37748736 times I**, nonzero. The JSON gives both basis-state residuals. An initial state was not fixed by the packet, so an operator, rather than an invented unique trajectory residual, is the complete reference. Only zero initial state has zero residual. Formal Taylor coefficients are exact; finite-step harmonic motion is E2 approximate.

For C4 use R=[[0,−1],[1,0]], R⁴=I. Bounded entries refer to rotation state, not arbitrary accumulated position. For the 3-4-5 rotation use (3+4i)/5. For k≥1 both reduced entries have denominator 5^k: modulo 5 the integer numerators of (3+4i)^k have nonzero real and imaginary residues, with ratio imaginary/real=3 and each further multiplication multiplying the real residue by 1 modulo 5. Thus no factor of 5 cancels. The JSON gives k=0..16 as exact references. A precise ARITH_LIMIT step still depends on the registered width and operation ordering; this certificate does not invent a missing ledger or partial-state rule.

S5 requires explicit translations, segment order/interval and chain-parameter convention before nine literal chain samples exist. S6 C2/G2 needs derivative data as above. Atomic refusal state, malformed inputs, width-stage mutants, perturbed caches and operation-ledger invariants are implementation-test obligations, not certified merely by this fixture file. No blanket S1–S6 execution-readiness claim is made.

Cell A contains the same nine scalars for every arm and no quotient if its final pair is defined consistently. Equal precomputation/caching rights are mathematically implementable in all listed representations; their real cost is unmeasured. FD remains a negative control, not an advantage-screen cell. No E2 trajectory is labelled exact and no A31 residue is used as geometry.

Required author/owner actions before fixture freeze: resolve the factor-two definition explicitly; amend negative-h direction/curvature conventions; narrow the K1 sparsity claim; define S3 endpoint increments and missing chain/join inputs; correct the unsupported float-control prediction; record hashes after accepting corrections. No source amendment is performed here. Candidate implementation and P0 remain HOLD.
