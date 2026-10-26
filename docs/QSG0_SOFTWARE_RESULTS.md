# QSG-0 rectangle fan: isolated software results

Date: 2026-10-19. Status: software fixture PASS; research acceptance **0/5**,
pending independent result review. QSG-0 is frozen after this experiment.

The [reviewed specification](QSG0_MATHEMATICAL_SPECIFICATION.md) was exercised
under the [software execution contract](../spu_strategy/contract_qsg0_software_experiment_2026-10-19.md).
The owner authorized the isolated experiment; no production software, shared
regression runner, RTL, ISA, timing constraints or hardware campaign was changed
or launched by this work. These are software results, not hardware evidence.

## Evidence and reproduction

Executed from the repository root:

```bash
timeout 30s python3 research/qsg0/run.py --output build/qsg0/rectangle_fan_03
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- research/qsg0 docs/QSG0_MATHEMATICAL_SPECIFICATION.md docs/QSG0_GENERATIVE_GEOMETRY_RESEARCH.md docs/QSG0_SOFTWARE_RESULTS.md spu_strategy/contract_qsg0_software_experiment_2026-10-19.md
```

Evidence: [results JSON](../build/qsg0/rectangle_fan_03/results.json),
[provenance](../build/qsg0/rectangle_fan_03/provenance.json),
[terminal marker](../build/qsg0/rectangle_fan_03/COMPLETE) and copied inputs
under `build/qsg0/rectangle_fan_03/inputs/`. The marker records exit 0.
Provenance includes exact argv, Python/platform, git HEAD, pre-existing dirty
status, tracked-diff hash and hashes of all experiment sources. The copied
specification predates the results annotation; the numerical contract is
unchanged. Build evidence is local and is not assumed to be distributed with
a source checkout. The runner recreates results from the source files.

Output must be a new child of `build/`; the runner refuses overwrite. For a
separately authorized reproduction choose a new evidence directory. Run 01
passed initial checks; run 02 added the bounded timing comparison and full input
snapshots. Run 03 strengthened endpoint value/refusal parity checks. Only run 03
supplies the reported measurements. No run timed out.

## Exact geometry and refusal checks

| t | u | B=(c,s) | Central spread | Doubled face area |
|---|---|---|---|---|
| 1/2 | 4/5 | (3/5,4/5) | 16/25 | 4/5 |
| 1 | 2 | (0,1) | 1 | 1 |
| 2 | 16/5 | (-3/5,4/5) | 16/25 | 4/5 |

The independent Fraction oracle constructs coordinates directly from t. The
bounded model constructs u, then reconstructs using a checked rational square
root. They agree exactly on all primary targets and repeated reconstructions.
All nine ordered target transitions, repeated targets and coordinate-to-metric
round trips pass. All four spoke quadrances stay 1; both diagonal quadrances
stay 4. Boundary quadrances change, and adjacent boundary edges stay
perpendicular. Positive face orientations, triangle discriminants, opposite
boundary separation, convexity and an interior center establish a valid
nonoverlapping fan for these tested coordinates. Topology is fixed in code.

Nine rigid controls preserve all pairwise quadrances and invert exactly.
Reflection and bent-corner negative controls are detected. This checks target
reconstruction, not a local constraint solver, continuous evolution or a
composable deformation group. Equal central spreads at t=1/2 and 2 do not
identify the labeled state.

Fourteen refusal checks pass, including invalid metric/parameter/encoding,
inconsistent expanded edges, domain escape, primitive division by zero and
bounded result overflow. Failed state updates preserve the previous descriptor
and cached coordinates. Valid real metrics u=1 and u=1/2 are DOMAIN_ESCAPE
over Q, not invalid geometry. t=32768 refuses at 4*t² before division under
the frozen evaluation order. Its reduced final u is 4294967296/1073741825;
the numerator also exceeds R32's signed 32-bit limit. This fixture therefore
does not demonstrate an intermediate-only refusal. The earlier interpretation
that the reduced final value would fit was incorrect; the observed refusal,
source snapshots and measurements are retained without rerunning the experiment.
See the [evidence review](QSG0_EVIDENCE_REVIEW.md) for the correction and limits.

All 64 endpoint arithmetic cases pass the expected outcome checks. For valid
R32 operands, the largest possible absolute unreduced add/sub numerator is
at most 2*2³¹*(2³¹-1)<2⁶³; multiplication and division products are smaller.
Thus no artificial single-primitive 64-bit overflow case is claimed. This
analytic bound does not promise that every reduced result fits R32.

## Costs and conventional baselines

Variable packed state is 8 bytes for u, 64 for eight rational edge values,
and 80 for five 2D rational Cartesian vertices; five binary64 vertices also
take 80 bytes. Topology, scale and frame are fixed shared constants. Cached
rational coordinates add another 80 bytes to either metric form. These are
logical formats, not measured Python heap sizes. A conventional rational t
parameter is also 8 bytes in the same format: this family demonstrates no new
compression advantage over ordinary parametric geometry.

Per target, the instrumented bounded target-plus-metric path records 391
checks, 58 gcd calls, 116 integer exact divisions, 19 rational multiplications,
9 additions, 18 subtractions, 2 divisions, 3 negations and 1 rational sqrt
(2 integer square roots). Target generation alone uses 103 checks and 18 gcd
calls. Peak observed bounded integer magnitude is 11 bits for the non-square
targets and 3 bits for the square. These tiny fixtures do not characterize
general expression growth or worst-case R32 workloads.

The workload below generates all three targets, canonical coordinates and all
eight measured edge quadrances. Each timing is the median of three samples,
100 workloads per sample, one warm-up, with GC disabled during sampling.

| Software path | Median microseconds per three-target workload | Traced Python peak bytes |
|---|---:|---:|
| Rational descriptor and reconstruction | 331.83 | 6,888 |
| Expanded rational metric and reconstruction | 379.72 | 7,304 |
| Direct rational Cartesian construction | 338.55 | 6,744 |
| Direct binary64 Cartesian construction | 54.72 | 4,144 |
| Checked, instrumented R32 descriptor and reconstruction | 857.25 | 9,432 |

Separate rational coordinate-to-metric conversion costs 255.53 microseconds
per three-target workload; rational metric-to-coordinate conversion costs
47.77 microseconds. Binary64 metric-to-coordinate conversion costs 2.85
microseconds. Raw samples, Fraction operation profiles, integer-local sizes,
retained memory and transient estimates are in the JSON. Tracemalloc runs
outside timing and excludes untraced C/system allocation; peak minus retained
is only a transient-allocation estimate. R32 timing includes instrumentation
and checking overhead. This single-host tiny run establishes no speedup,
hardware resource benefit, energy result or statistically stable ranking
between the closely timed rational paths.

## Binary64 and robust geometric decisions

The square is represented exactly. For both non-square targets, the maximum
coordinate error is 1/22517998136852480. The maximum exact edge residual of
the stored binary64 coordinates is approximately 8.88e-17, and the maximum
corner dot-product residual is approximately 4.44e-17. Residuals are evaluated
as exact fractions of the finite stored values, not rounded away.

The local robust orientation baseline is `interval-filter-v1`: outward-rounded
interval arithmetic, with exact rational fallback on the original finite
binary64 inputs. It is not Shewchuk's implementation or an adaptive-expansion
performance comparison. Its declared input range is [-4,4]. Across 33 tests
(all primary-target triples plus collinear, near-collinear and underflow
controls), 24 signs resolve in the filter and 9 use exact fallback; all agree
with independent exact determinants. Robust decisions do not repair inexact
coordinates or establish exact construction invariants.

## Disposition

This restricted rectangle family is exactly reconstructible for the three
rational targets and rejects the specified domain and bounded-format failures.
The invariant-preserving target changes are nonrigid, but ordinary rational
parameterization already provides equally compact state. No advantage over
established geometry representations has been demonstrated.

Keep acceptance at **0/5 pending independent result review**. Freeze QSG-0;
do not enlarge the family, add arithmetic domains, create native operations or
launch follow-up runs without renewed authorization. Gen 1 qualification and
integration retain priority.
