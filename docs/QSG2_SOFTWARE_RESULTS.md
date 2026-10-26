# QSG-2 PH curves: bounded software results

Date: 2026-10-19. Status: EXPERIMENTAL software fixture PASS; correctness and
measurement phases complete. Independent scientific acceptance remains pending.
QSG-0 stays 0/5; no QSG-1 acceptance decision or hardware adoption is implied.

## Scope, authorization and evidence

The owner explicitly authorized isolated implementation, one 30-second
correctness invocation and, only on PASS, one separate 30-second measurement
phase. Both completed with exit 0; no retry, timeout, installation or hardware
run occurred. Only research sources, documentation and local build evidence
were added/updated. Production RTL, ISA, simulator and shared arithmetic/tests
were untouched. QSG-0's rational primitives were reused read-only.

The [execution contract](../spu_strategy/contract_qsg2_ph_software_2026-10-19.md)
and [mathematical specification](QSG2_PH_CURVE_SPECIFICATION.md) define the
representation, cache trust, arithmetic order, failures and exact outputs.
Executed from the repository root:

```bash
python3 research/qsg2/run.py freeze --output build/qsg2/freeze_01
timeout 30s python3 research/qsg2/run.py correctness --freeze build/qsg2/freeze_01 --output build/qsg2/correctness_01
timeout 30s python3 research/qsg2/run.py measurement --freeze build/qsg2/freeze_01 --correctness build/qsg2/correctness_01 --output build/qsg2/measurement_01
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- research/qsg2 spu_strategy/contract_qsg2_ph_software_2026-10-19.md docs/QSG2_PH_CURVE_SPECIFICATION.md docs/QSG2_SOFTWARE_RESULTS.md docs/QSG_RESEARCH_ROADMAP.md
```

Preserved artifacts:

- [Frozen manifest](../build/qsg2/freeze_01/manifest.json) and its `inputs/` tree:
  thirteen research modules, unchanged rational primitive module, specification
  and contract, all SHA-256 pinned before execution.
- [Correctness results](../build/qsg2/correctness_01/results.json), provenance
  and COMPLETE marker.
- [Measurement results](../build/qsg2/measurement_01/results.json), provenance
  and COMPLETE marker; measurement provenance pins the correctness result hash.

The runner verifies current and copied sources against the freeze before
execution. Measurement additionally requires exactly one correctness terminal
marker, COMPLETE, the recorded PASS, and the same freeze identity. Closeout
annotations in current documents do not replace their frozen execution-time
copies. Build artifacts are local evidence, not presumed shipped with a source
checkout. New output paths and renewed authorization are required for replay.

## Correctness and certificate trust

All four regular curves passed. Across seven representation/arithmetic paths,
588 named query comparisons agreed exactly with the independent Fraction oracle;
24 position/derivative comparisons also agreed with de Casteljau evaluation.
The oracle uses polynomial convolution and power-to-Bézier conversion, while
the candidate uses the frozen explicit products and checked primitives.
The oracle and ordinary factored baseline import no candidate implementation.
The same implementer wrote both: this is source/formula separation, not
independent authorship or exhaustive verification.

Queries cover position, derivative, scalar speed, unit tangent, arc length,
interval length and bundled position/derivative Q1. Exact unit-tangent norms,
interval additivity, endpoints and independently stated total lengths passed.
All measured correctness residuals are zero on the tested rational inputs.

| U,V | Endpoint | Total length |
|---|---|---|
| 1,t | (2/3,1) | 4/3 |
| 1,2t | (-1/3,2) | 7/3 |
| 1+t,t | (2,5/3) | 8/3 |
| 1,0 | (1,0) | 1 |

For the primary curve at t=1/2, position (11/24,1/4), arc length 13/24,
speed 5/4 and tangent (3/5,4/5) match the hand-derived specification.

Thirty counted refusal controls exercise zero/cusp regularity, schema/encoding,
interval errors and the required certificate precedence in both candidate modes.
In particular, negative sigma=-(2+t²) with matching integral first fails
the polynomial identity: INVALID_CERTIFICATE. Negative sigma=-(1+t²) with its
matching negative integral passes the identities but fails positivity:
INVALID_SPEED_CERTIFICATE. These paired controls use conventional power import.

Supplied stale factor caches are rejected. Accepted coefficient caches are
immutable tuples of canonical pairs; changing caller arrays does not change
accepted factor or conventional power objects. Bare unadmitted records cannot
query. Twenty-one failed replacement checks preserve the previous accepted
object and its populated coefficient cache, including bounded arithmetic failure.
The cache guarantee concerns the validated public API, not hostile in-process
Python reflection or an authenticated external certificate scheme.

## Refusal stages and arithmetic costs

With U=46341,V=0, unbounded construction is valid, but the first square is
2147488281, larger than R32's maximum numerator. The bounded replacement refuses
at `products.u0_squared`; old state/cache remain unchanged. A primary position
query at t=1/(2³¹-1) refuses at `position.x.2.mul`, whose exact intermediate is
-1/6442450941. That denominator exceeds R32's limit; no partial result publishes
and the accepted cache remains intact. Both stages are explicitly asserted,
not inferred from a generic status. Neither fixture is claimed to demonstrate
a representable final answer with intermediate-only failure.

Peak observed admission integer magnitudes for the four primary curves are
3,5,4,2 bits; primary query traces reach at most 6 bits. These small samples
do not characterize arbitrary coefficient growth. Raw primitive counters are
in the JSON and exclude Python schema logic, extra decode gcd work, Fraction
internals and complete host memory/compute costs. No worst-case heap result
or general QSG-R32 closure claim was measured.

## Operation-specific comparisons

Each number is the median microseconds per call from three samples of 100
calls, one warm-up, GC disabled. Samples cycle the same twelve curve/parameter
pairs; because 100 is not divisible by twelve, each sample has the same small
fixed weighting toward the first fixtures. Results are not a randomized,
cross-machine or statistically qualified performance study.

| Query output | Ordinary factored Fraction | Candidate factor Fraction | Cached power Fraction | Checked factor R32 | Checked power R32 |
|---|---:|---:|---:|---:|---:|
| Position only | 16.82 | 53.00 | 53.68 | 110.76 | 107.25 |
| Derivative only | 14.88 | 34.08 | 44.61 | 78.91 | 82.26 |
| Scalar speed | 9.61 | 28.05 | 25.31 | 60.96 | 46.09 |
| Unit tangent | 19.86 | 40.02 | 63.69 | 98.01 | 125.07 |
| Arc length | 9.66 | 30.29 | 31.17 | 59.80 | 59.19 |
| Interval length | 18.88 | 50.16 | 50.85 | 113.69 | 113.54 |
| Position plus derivative | 29.76 | 82.18 | 95.05 | 172.70 | 175.27 |

All accepted forms retain validated speed/arc metadata. Arc queries use the
same polynomial opportunity; no conventional path rediscovers the PH identity
or integrates numerically per query. Cached quadratic speed uses two rational
multiplications and two additions; factor speed uses four multiplications and
three additions. Factor tangent reuses factor squares rather than evaluating
three separate derivative/speed polynomials. These explain operation-specific
work differences, not a universal ordering or a new mathematical capability.

The ordinary factored implementation already exploits the same PH structure and
was faster than the instrumented candidate. Candidate Fraction and R32 paths
include diagnostic stage/trace overhead and cache decoding; this comparison
provides no SPU-specific speed advantage. Bézier imports use retained power
coefficients for timed queries; this is not a benchmark against direct native
de Casteljau position evaluation or a general NURBS engine. Their full samples
are in the JSON, and their arc-query costs are comparable to cached power.

Admission medians are 330.63 microseconds for the ordinary factored reference,
303.70/287.77/343.00 for candidate factor/power/Bézier Fraction, and
798.84/702.31/866.44 for their R32 counterparts. Admission includes validation,
cache construction and baseline-specific bookkeeping; the reference also
constructs oracle Bézier controls. These are measured implementation costs,
not normalized import-library speed rankings. Separate Bézier-to-power
conversion medians are 63.22 microseconds Fraction and 164.58 R32.

The selected representation stores six authoritative factor rationals (48
logical R32 bytes) or eight conventional scalars (64 bytes), plus a deliberately
full 21-rational derived cache (168 bytes). Power coefficients can alias their
authoritative data, making a deduplicated power layout 168 total bytes instead
of naively adding 64. Smaller cache choices are possible; ordinary factored
PH has the same compact source as the candidate. No minimal-storage or FPGA
resource advantage is established by these logical payload counts.

## Disposition

The tested PH construction supports exact rational queries, explicit cache
admission and bounded refusal with retained state. Polynomial arc length is an
established PH benefit that conventional implementations can retain equally.
The results distinguish position, speed, tangent and arc-length costs rather
than claiming an aggregate speedup. Inverse arc length, fitting, offsets,
surfaces, dynamics, native instructions and hardware remain outside scope.
The authorized tranche is complete; independent result acceptance and any
follow-up execution are separate decisions. No additional run is needed here.
