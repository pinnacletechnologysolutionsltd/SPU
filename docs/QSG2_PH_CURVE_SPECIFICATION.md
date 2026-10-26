# QSG-2: PH curves and algebraic arc length

Date: 2026-10-19. Status: reviewed mathematical specification; isolated software
implementation and bounded execution now explicitly authorized by the owner.
The [execution contract](../spu_strategy/contract_qsg2_ph_software_2026-10-19.md)
defines certificate authority, immutable validated caches, deterministic
classification and operation-specific comparisons for designated review.
The owner's later “Authorized” activates one 30-second correctness phase and,
only on PASS, one 30-second measurement phase. It supersedes the earlier HOLD;
no independent acceptance or hardware adoption is implied.
The [completed software results](QSG2_SOFTWARE_RESULTS.md) record both phases,
operation-specific costs, certificate controls and the remaining limitations.
No simulator instruction, production arithmetic, RTL, hardware or topology change.
Read the [QSG-1 evidence review](QSG1_EVIDENCE_REVIEW.md) for the preceding
tranche's source-separation, bounded-refusal and comparison limitations.

## 1. Freeze the question and known mathematical foundation

Can a small factored hodograph representation simplify exact curve, tangent
and arc-length queries compared with conventional representations of the same
curve, after charging conversion, certificate validation and cached metadata?
Correctness and comparative utility are separate questions; no novel curve
family or architectural advantage is presumed.

Use the classical planar polynomial Pythagorean-hodograph (PH) construction
described in [Kosinka and Lávička's survey](https://www.cs.rug.nl/~jiri/papers/14KoLa.pdf),
especially its planar construction and regularity discussion. Polynomial
speed/arc length and rational offsets are established PH properties. This
specification specializes that construction; it does not introduce new theory.
The formulas below follow directly by squaring, multiplying and integrating
linear rational polynomials. Defer offsets, trimming, fitting and surfaces.

## 2. Fix domain, state and regularity

Let U(t)=u0+u1*t and V(t)=v0+v1*t with rational coefficients, 0<=t<=1.
Store (u0,u1,v0,v1,x0,y0) in a declared gauge; no claim of unique/minimal
encoding. Simultaneously negating U,V leaves the curve unchanged. Require
regularity: sigma(t)=U(t)²+V(t)²>0 everywhere on the closed interval.

```text
dx/dt = U²-V²              dy/dt = 2UV
sigma = U²+V²              (dx/dt)²+(dy/dt)² = sigma²
sigma = s0+s1*t+s2*t²
s0=u0²+v0²   s1=2(u0*u1+v0*v1)   s2=u1²+v1²
```

Prove positivity without approximate roots: inspect sigma at both endpoints
and, when s2>0 and tv=-s1/(2*s2) lies strictly inside (0,1), at tv.
When s2=0 use the constant sigma; the source construction forces s1=0.
A zero is NONREGULAR, not a false PH identity or invalid Euclidean curve.
Stationary/cusped curves remain outside this first regular-query contract.

Write dx/dt=A0+A1*t+A2*t² and dy/dt=B0+B1*t+B2*t², with
A0=u0²-v0², A1=2(u0*u1-v0*v1), A2=u1²-v1²,
B0=2*u0*v0, B1=2(u0*v1+u1*v0), B2=2*u1*v1.
Then r(t)=(x0,y0)+(A0,B0)*t+(A1,B1)*t²/2+(A2,B2)*t³/3.

## 3. Define exact queries and closure boundaries

Q0 validates input encoding and regularity; Q1 returns r(t) and r'(t).
Q2 returns S(t)=s0*t+s1*t²/2+s2*t³/3 with S(0)=0.
For 0<=a<=b<=1, arc length is S(b)-S(a). Reject reversed/outside intervals.
Q3 returns the oriented unit tangent T(t)=r'(t)/sigma(t); verify T·T=1
exactly. Return sigma as scalar speed, distinguishing it from squared speed.
For rational inputs and rational query t, all these outputs lie in Q before
bounded-format checks. No runtime square-root extraction is needed in these
queries once the PH construction and positive-speed certificate are established.

Do not infer rational inverse arc-length parameters. In the primary example
below, requested length 1 requires t³+3t-3=0. Its unique root in (0,1) is
not rational by the rational-root test. Inverse arc length, uniform arc-length
sampling, root solvers and arbitrary symbolic extensions are outside execution
scope; this hand-derived example falsifies a blanket rational-closure claim.

## 4. Freeze a tiny proposed fixture set

Use origin (0,0) and linear forms below; these are mathematical expectations,
not generated golden data or executed observations. Query t in {0,1/2,1}.

| U,V | Expected endpoint r(1) | Total length S(1) | Role |
|---|---|---|---|
| 1,t | (2/3,1) | 4/3 | Primary regular cubic |
| 1,2t | (-1/3,2) | 7/3 | Different tangent and coefficient sizes |
| 1+t,t | (2,5/3) | 8/3 | Both linear coefficients contribute |
| 1,0 | (1,0) | 1 | Straight-line control |

For U=1,V=t: r(t)=(t-t³/3,t²), S(t)=t+t³/3. At t=1/2,
r=(11/24,1/4), S=13/24, sigma=5/4 and T=(3/5,4/5).
The same cubic's Bézier controls are (0,0),(1/3,0),(2/3,1/3),(2/3,1).

Include zero U,V and U=t-1/2,V=0 as NONREGULAR controls. Include a
perturbed derivative coefficient with an unchanged speed certificate: exact
coefficient identity must fail. The generic curve (t,t²) is a valid non-PH
control: 1+4t² is not a polynomial square. Do not label the curve invalid or
use comparisons of different shapes to claim a PH speed advantage.
Malformed fractions, out-of-interval queries, bounded refusals and certificate
mutations must be distinguished. Test identities as polynomial coefficients,
not only at the three selected sample parameters.

## 5. Require independent oracles and fair conventional baselines

The independent arbitrary-precision Fraction oracle must derive and compare
the polynomial identities, verify dS/dt=sigma, and validate exact regularity.
Use de Casteljau evaluation of independently derived rational Bézier controls
to cross-check points, plus independent derivative control points for r'.
Verify arc-length additivity across subintervals and exact unit tangents.
No candidate helper may generate expected outputs for its own assertions.

Compare the same curves as factored PH state, ordinary rational power basis
and cubic Bézier controls. A one-span unit-weight NURBS representation is the
same Bézier curve; no full NURBS engine is needed or authorized for this probe.
The conventional exact baseline may retain sigma/S coefficients and verify
their PH certificate once, then use the same exact arc-length opportunities.
Also include a conventional factored-hodograph implementation: equal compact
representations must not be relabeled as an SPU-specific storage advantage.
Numerical quadrature may provide an explicitly approximate reference with an
error target, but cannot be the sole arc-length baseline for a known PH curve.

Report one-time conversion/certificate costs, repeated query costs, packed
state, cached coefficients, peak intermediate sizes and refusals separately.
Include matched combined workloads, not only isolated formula counts.
Holding sigma metadata on one side and forcing the other to rediscover it
per query is not a fair architectural comparison.

## 6. Preserve the execution boundary

Start the proposed bounded model with QSG-R32, unchanged checked signed-64-bit
primitive intermediates and canonical fractions; no silent widening or fallback.
Unbounded validity and bounded operational refusal remain separate outputs.
Integration divides by small integer constants in software; it grants no RTL
divider or new arithmetic-kernel authority. Preserve state/cache on failure.

Before implementation, freeze coefficient-construction order, Horner query DAGs,
certificate/regularity error precedence, traceable refusal stages and matched
metadata policies in a separate reviewed execution contract. Do not invent a
refusal-stage interpretation from a final status code, as the QSG-0/QSG-1
reviews showed. Any asserted intermediate-only case needs exact final and
intermediate representability checks, not an assumed cancellation argument.

Proposed scale: one tiny correctness fixture, then at most three 100-query
timing samples if meaningful, with a 30-second software invocation limit.
This original proposed scale was superseded by the owner's explicit 30-second
correctness plus 30-second measurement authorization in the execution contract.
That tranche is complete; no new invocation is authorized by this specification.
Record negative findings and stop. No inverse
solver, arbitrary curve matching, surface dynamics, symbolic ISA or FPGA work
is within scope. Mathematical specification approval alone does not authorize
implementation, execution or advancement of earlier research acceptance gates.
