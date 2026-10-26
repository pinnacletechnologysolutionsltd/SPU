# QSG-0 evidence review and interpretation correction

Date: 2026-10-19. Status: read-only technical audit completed; designated
independent gate decision remains pending. Research acceptance: **0/5**.

The implementer performed this audit at the owner's request. It is not an
independent reimplementation, rerun or substitute for designated result review.
The owner agreed to the overflow interpretation correction and QSG-1 closure
proposal. That agreement did not mark any acceptance gate verified.

## Evidence identity

Audited [run 03 provenance](../build/qsg0/rectangle_fan_03/provenance.json),
[results](../build/qsg0/rectangle_fan_03/results.json), terminal marker and
the copied files under `build/qsg0/rectangle_fan_03/inputs/`.
Exactly one terminal marker is present: COMPLETE, containing exit 0.
All eleven copied inputs match their recorded SHA-256 digests: nine Python
modules, the mathematical specification and software execution contract.
At this audit, all eleven matched their current working copies. Subsequent
report annotations do not alter the copied inputs or recorded measurements.
The recorded git revision is `963a685004b96e275e7e58ebefac98c6e1321597`;
the manifest also records the dirty checkout, platform and Python version.
HEAD alone is not the complete experimental source identity.

This audit hashed/parses saved files and checked report arithmetic; it did not
import or execute QSG-0 modules, repeat timings, run a new geometry fixture,
or alter any build evidence. Result JSON is a preserved runner record, not
independent proof that its checks were adequate or a fresh reproduction.

## Oracle and check separation

Static import inspection confirms that `oracle.py` depends only on standard
Fraction/integer mathematics. It imports neither `model.py` nor `rational.py`.
It generates expected target coordinates directly from rational t; the bounded
model computes u and reconstructs via a checked rational square root.
The harness compares these paths using the independent exact coordinates.
Both paths still share the reviewed mathematics and were written by the same
implementer; separation is useful but not independent authorship or exhaustive
proof. Conventional Fraction paths share the oracle's geometric helpers.

| Recorded check | Source inspection and record agreement |
|---|---|
| Nine ordered target transitions | Three-by-three target loop, repeated targets and reconstruction comparisons |
| Fourteen refusal cases | Twelve state-update fixtures with unchanged-state checks, plus two standalone primitive refusals |
| Nine rigid controls | Three modes on each of three target states; exact distances and inverse-coordinate checks |
| Sixty-four endpoint cases | Both accepted values and bounded refusals compared against Fraction expectations |
| Thirty-three robust-predicate cases | Thirty target triples plus three numerical controls; 24 filter decisions and 9 exact fallbacks |

Convex boundary, separated opposite edges, positive face orientation and an
interior fan center justify the nonintersection conclusion for the named
rectangle family. Fixed topology is a construction assumption, not a tested
dynamic-topology capability. The reflected-state mutation reaches the geometry
validator; the bent-corner control checks a nonzero dot product directly and
does not exercise a generic public input rejection interface.

## Interpretation correction

For t=32768, t²=1073741824 and 4*t²=4294967296. The bounded model correctly
refuses that multiplication before division. Reduction of
4294967296/1073741825 leaves numerator 4294967296, also outside signed R32.
The [results report](QSG0_SOFTWARE_RESULTS.md) previously asserted that the
final reduced value would fit. That assertion was wrong and is corrected.
The fixture supports early refusal under the specified order; it supplies no
evidence of an intermediate-only failure. No source, result JSON, timing sample
or input snapshot has been changed, and no replacement fixture is authorized.

## Measurement qualifications

Reported timing medians match the stored three-sample medians. The report's
rounded table agrees with run 03. Timing samples cover three targets per
workload, 100 repetitions per sample, with one warm-up and GC disabled.
They measure local Python implementations and include checking/counter costs
in the bounded path. Expanded metrics perform additional redundancy checks;
these are implementation comparisons, not isolated arithmetic kernel speedups.
Packed bytes exclude common constant topology/frame/schema, while traced
Python allocations include objects and outputs. Neither describes FPGA cost.
The 8-byte t parameter baseline prevents a novel-compression inference.

The local interval filter is explicitly not Shewchuk's implementation. Its
finite tests and exact fallback establish the recorded outcomes, not an
established-library performance comparison. Future comparative utility work
must include an established robust-predicate baseline. Domain-limited geometry,
small coefficient growth and this single-host timing sample do not establish
general closure, a useful native primitive, energy benefits or system utility.

## Designated reviewer decision record

| Acceptance criterion | Audit material available | Gate decision |
|---|---|---|
| Intrinsic metric, topology and embedding distinguished | Reviewed specification and explicit planar convention | Pending |
| Exact oracle and bounded behavior specified | Import separation, operation order and refusal inspection | Pending |
| Four-triangle validity | Recorded fixture outcomes with fixed-family limitations | Pending |
| Conventional baseline included | Fraction/binary64 measurements; robust-library comparison not performed | Pending |
| Gen 1 RTL, ISA and timing unchanged by experiment | Isolated source/contract scope; unrelated dirty checkout preserved | Pending |

The designated reviewer must determine whether each criterion's stated scope
is satisfied, or request further evidence under separate authorization.
No criterion advances automatically from this audit. QSG-0 remains frozen;
This audit itself grants no QSG-1 execution authority. The owner's later
instruction independently authorized a reviewed bounded QSG-1 software tranche;
its separate contract and results do not advance these QSG-0 acceptance gates.
