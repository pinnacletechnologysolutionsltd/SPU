# QSG-2 PH software contract: authorized isolated tranche

## Prospective execution transition — 2026-10-19

The owner adopted the [research execution policy](RESEARCH_EXECUTION_POLICY.md)
with QSG-2 as its Class A pilot. Implementation, small software tests, ordinary
debugging, reruns and comparison are authorized under that policy. It supersedes
the historical execution-HOLD/per-run approval and campaign-record requirements
below, including the requirement for a reviewer disposition before implementing.
The mathematical specification, ordered arithmetic, certificates, negative
controls, comparative semantics and exclusions remain binding. Research results
do not advance QSG-0/QSG-1 independent acceptance or architectural qualification.
The original draft follows unchanged as the historical baseline. No experiment
was executed by this policy amendment.

Date: 2026-10-19. Status: COMPLETE for the authorized software tranche; both
phases PASS. See [results](../docs/QSG2_SOFTWARE_RESULTS.md). Owner replied “Authorized” to
isolated implementation, one correctness run capped at 30 seconds and, only
after PASS, one separate 30-second measurement phase with three 100-query
samples per workload. This supersedes the earlier HOLD for this tranche only.
Earlier QSG-0/QSG-1 independent acceptance remains pending; no gate advances.

## Review and scope

```bash
python3 research/qsg2/run.py freeze --output build/qsg2/freeze_01
timeout 30s python3 research/qsg2/run.py correctness --freeze build/qsg2/freeze_01 --output build/qsg2/correctness_01
timeout 30s python3 research/qsg2/run.py measurement --freeze build/qsg2/freeze_01 --correctness build/qsg2/correctness_01 --output build/qsg2/measurement_01
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_qsg2_ph_software_2026-10-19.md docs/QSG2_PH_CURVE_SPECIFICATION.md docs/QSG_RESEARCH_ROADMAP.md
```

Use only the [planar cubic specification](../docs/QSG2_PH_CURVE_SPECIFICATION.md).
Implementation files belong under `research/qsg2/`. Preserve production
arithmetic, simulator/ISA, RTL and all earlier evidence. Source snapshots and
hashes must be frozen before execution; the measurement gate checks those same
hashes and a durable correctness PASS before importing measurement code.
The implementer's analytical review found no further mathematical contradiction;
this disposition authorizes research execution, not independent acceptance.

## 1. Certificate authority and immutable state

Factor import accepts exactly six canonical rationals in order
(u0,u1,v0,v1,x0,y0), interval [0,1] and a schema version. Only those factors
and origin are authoritative. Derive curve, sigma and S coefficients; supplied
cached values never override derivation. Reject any supplied cache mismatch.

Conventional import accepts either eight power coefficients (x0..x3,y0..y3)
or four ordered Bézier control points, plus declared sigma and S coefficients.
It need not recover rational PH factors. Independently derive its derivative
polynomials, check every coefficient of x'²+y'²=sigma², and require S(0)=0
and S'=sigma. Validate sigma>0 on [0,1]. A negative sigma satisfying the squared
identity is still an INVALID_SPEED_CERTIFICATE, not a usable speed function.
Zero speed is NONREGULAR. No approximate certificate or trusted caller flag.

Accept caches only after exact validation against the authoritative representation
and object version. Copy external arrays into immutable internal tuples; later
caller mutation must not change accepted state. Validated immutable objects may
retain their caches without per-query revalidation. Replacements are staged,
validated and atomically published; failures preserve old state and caches.
This privilege applies equally to all representations. No disk cache or
caller-supplied hash is a substitute for mathematical certificate validation.

## 2. Freeze arithmetic and construction order

Use independent arbitrary-precision Fraction mathematics and QSG-R32 with the
unchanged checked signed-64-bit primitive contract. Classify the first bounded
primitive refusal at its labeled stage; do not infer its location from a final
status. No silent reassociation, wider fallback or coefficient repair.

For factor import compute, in order, u0²,v0²,u0*u1,v0*v1,u1²,v1²,
u0*v0,u0*v1,u1*v0,u1*v1. Derive A0,A1,A2, then B0,B1,B2, then s0,s1,s2
using the specification's formulas and left-to-right binary primitives.
Build x and y coefficient arrays (origin,D0,D1/2,D2/3), x before y.
Build S=(0,s0,s1/2,s2/3). Retain each intermediate's normalized exact value
and bounds before proceeding. Constants use canonical encodings too.

For conventional input convert Bézier to power form coordinate-by-coordinate:
c0=P0, c1=3*(P1-P0), c2=3*((P2-2*P1)+P0),
c3=((P3-3*P2)+3*P1)-P0. Derivative coefficients are (c1,2*c2,3*c3).
Power input bypasses that conversion, not certificate checking.
Polynomial multiplication initializes zero coefficients, then visits ascending
i and ascending j, multiplying and adding one pair at a time without zero
skipping. Compare complete coefficient arrays with canonical trailing zeros.
Derivative/speed identity has degree at most four. Do not replace it with
three sampled point checks.

For regularity evaluate sigma(0), sigma(1), then the interior stationary point
tv=-s1/(2*s2) if s2>0 and 0<tv<1. If s2<=0, the minimum is at an endpoint;
do not divide by zero for s2=0. The factor-derived s2=0 case necessarily has
s1=0; imported conventional certificates may be affine. Compute the minimum
before classifying its sign. Coefficient schema is degree<=2.

## 3. Freeze error precedence and query order

First validate schema/arity/version, then every external rational encoding in
record order, then the declared interval/schema. INVALID_SCHEMA and
INVALID_ENCODING precede arithmetic or geometry. Construct/convert coefficients
in section 2 order; first bounded refusal takes precedence over later exact
certificate/regularity diagnoses. Record the unbounded diagnosis separately.

Next check imported curve/cache agreement where factors are authoritative,
then the squared-speed identity, S(0)=0 and S'=sigma: INVALID_CERTIFICATE on
the first mismatch. Then check speed sign: negative minimum gives
INVALID_SPEED_CERTIFICATE, zero gives NONREGULAR. Publish only after success.
Malformed certificates are not silently replaced with freshly computed ones.

Queries require an accepted immutable object and valid operation/schema before
decoding parameters. Require rational t in [0,1]; interval queries decode a,b,
then require 0<=a<=b<=1, otherwise INVALID_INTERVAL. Unknown operation or
malformed query is INVALID_SCHEMA. No partial query result is observable.

Horner evaluation starts at the highest coefficient, repeatedly multiplying
by t then adding the next coefficient, retaining zero coefficients. Position
evaluates x then y. Factor derivatives evaluate U then V, U² then V², followed
by dx=U²-V², dy=(2*U)*V. Speed is U²+V². Tangent evaluates these derivatives
and speed, then dx/sigma and dy/sigma. Conventional forms may use their cached
derivative/speed polynomials with the same output requirements.
Arc length evaluates S(t); interval length evaluates S(a), S(b), then subtracts.
Each public query stages all outputs; bounded refusal leaves object/cache intact.
An accepted positive-speed object makes a mathematical zero query denominator
unreachable; report a violated invariant rather than quietly substituting data.

## 4. Freeze fixtures and comparative semantics

Use the four specified curves, t in {0,1/2,1}, and subintervals [0,1/2],
[1/2,1], [0,1]. Check exact points, derivatives, speeds, lengths, additivity
and unit tangents with an independent oracle and de Casteljau construction.
Include zero/cusp states, malformed data and the non-PH (t,t²) certificate
control. Test mutations of curve, sigma sign/coefficient, S constant/coefficient,
stale caches and post-import caller arrays. Exercise refusal with populated
caches, including arithmetic refusal, before claiming that dynamic coverage.
Do not invent near-limit refusal stages: independently calculate expected exact
intermediates, trace first refusal, and preserve any corrected interpretation.

Pin certificate precedence on the primary curve r=(t-t³/3,t²). Import
sigma=-(2+t²), S=-(2t+t³/3): S'=sigma, but the squared-speed identity fails.
Require INVALID_CERTIFICATE before considering negative speed. As its paired
control, sigma=-(1+t²), S=-(t+t³/3) passes both polynomial identities but must
return INVALID_SPEED_CERTIFICATE. These inputs distinguish identity precedence
from sign validation without changing the curve or arithmetic domain. They
are required checks in the authorized correctness invocation.

Compare identical curves as factors, power coefficients and Bézier controls.
Include a conventional factored implementation and cached exact sigma/S on all
forms. Measure admission/certificate validation once, representation conversion,
position, derivative, speed, tangent and arc queries separately, then matched
combined workloads. Position and derivative timings must identify returned
outputs exactly; a bundled query is not a position-only benchmark.
Report operation-specific outcomes: an arc-length improvement says nothing
about position speed. Equal algorithms or parameterization are not novel SPU
advantages. Approximate quadrature is optional and never the sole exact baseline.

## 5. Activated budget and completion

One correctness invocation capped at 30 seconds, then one measurement invocation
capped at 30 seconds only after correctness PASS: 60 seconds total maximum.
No corrective rerun is authorized. On failure or timeout, preserve evidence
and stop for disposition rather than consuming another attempt. Source freezing
and static syntax checks do not execute the geometry fixture.
Closeout: both authorized invocations were consumed and completed PASS.
There is no remaining execution allowance under this contract.
Use three 100-call samples per named workload, one warm-up, GC disabled during
samples; round-robin the same four curves and three parameters. Query workloads
name exact returned outputs, including bundled Q1. Admission/conversion calls
are separate named workloads with the same sample count. Time admission once
per call, never recertify on each query. Integer counters and labeled traces
are implementation diagnostics, not complete host-work or hardware cost models.
Preserve source snapshots, raw samples, exact residuals and terminal outcome in
a new build child. Stop after the separately authorized tranche. No inverse
arc-length solver, offsets/trimming, fitting, surfaces, dynamics, symbolic ISA
or hardware experiment. Negative or representation-dependent results are valid
outcomes; no earlier gate is accepted automatically.
