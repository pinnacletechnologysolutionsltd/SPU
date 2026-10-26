# QSG-1 saved-evidence review

Date: 2026-10-19. Status: technical evidence audit complete; designated
independent acceptance/disposition remains pending. QSG-0 remains 0/5.

This audit was performed by the implementer from saved artifacts. It does not
claim independent authorship, a fresh reproduction or authority to accept
research gates. The owner requested evidence review while preparing QSG-2;
neither activity authorizes a new geometry fixture or changes the production ISA.

## Integrity and mathematical separation

Audited `build/qsg1/experiment_02/` without importing or executing its modules.
Exactly one terminal marker is present, COMPLETE. All twelve source/dependency
snapshots match their provenance SHA-256 digests: seven QSG-1 modules, QSG-0's
unchanged rational primitives, specification, contract and predicate source/
binary. All Python snapshots also match the current source files. Report
closeout annotations differ from the execution-time documents and are not
substituted for preserved inputs.

The audit record is `build/qsg1/evidence_review_01/audit.json`; it pins result
and provenance hashes, records import edges and checks timing medians against
raw samples. No experiment, compiler, numerical baseline or timing was rerun.

Static inspection confirms `gram.py` imports only Fraction and integer math,
not the metric-first implementation. It evaluates a conventional Gram determinant
or reduced Schur form. The candidate evaluates W²=4HK with W>0. Both originate
from the same reviewed planar geometry, so formula/source separation does not
remove correlated-specification risk. Three independently stated rational point
sets and the wrong-branch/closure controls provide additional falsifiers.

## Recorded checks and their scope

| Evidence | What the saved harness establishes |
|---|---|
| Four accepted metric records | Candidate Fraction/R32 and Gram accept the same named real planar metrics |
| Nine negative records | Named schema, encoding, edge, anchor, local and closure classifications agree |
| Eight atomic edit checks | Four rejected edit types in both candidate arithmetic modes preserve metric/cache state |
| Nonsquare metric | Candidate state commits valid relationships; both exact formulations refuse rational reconstruction |
| Shared-edge controls | Inconsistent or noncanonical duplicate AB rejected before geometric validation |
| Bounded stage controls | Exact validity and operational R32 refusal kept separate; W and x stage assertions pass |
| Eighteen predicate cross-checks | Original Shewchuk signs agree with Fraction on the same stored binary64 inputs |

The atomic edit fixtures cover invalid face, closure, encoding and arity.
Arithmetic-overflow refusals are checked directly through V, not through a
state edit with a populated cache. The commit-after-validation source structure
supports the intended atomicity, but do not describe that missing dynamic case
as independently observed. Generic meshes, topology changes and a constraint
solver remain outside the tested scope.

## Classification and interpretation

The executed contract fixes operational precedence. A bounded refusal can occur
before an exact oracle's later geometric diagnosis. It is neither invalid
geometry nor DOMAIN_ESCAPE. DOMAIN_ESCAPE belongs to the exact coordinate
query, not metric admission. Positive W is checked before squared closure,
so WRONG_ORIENTATION_BRANCH is an operational classification, not a claim
that another valid planar embedding must exist.

Run 01's incorrectly named W² refusal stage was corrected in run 02 with an
explicit stage assertion. The large valid metric first exceeds R32 while
forming W, as shown algebraically in the results note. Both runs remain
preserved. QSG-0's separate corrected scalar-transform interpretation is not
overridden or reclassified by this result.

## Measurement qualifications

Reported medians match raw timing samples. Admission comparisons include the
nonsquare metric for candidate and Gram; exact coordinate timing uses only
the three Q-reconstructible records. The guarded numerical path includes an
exact Gram admission test and produces approximate coordinates, so it is not
an equal-output competitor for exact reconstruction. Original predicate source,
binary and compiler flags are pinned; robust orientation alone proves no closure.

The metric formula is locally faster than the particular full/reduced Gram
implementations. Algebraically equivalent conventional optimization remains
possible. This tiny single-host comparison establishes no native architectural,
energy or system-complexity advantage. Metric payload is larger than the four
free Cartesian scalars before coordinate caches are added.

Instrumentation counts describe Arithmetic's counters, not all host work.
In particular, each valid decode also calls Python gcd in `Field.decode`
outside the primitive counter: the reported 27 gcd counter events are not
the validator's total gcd calls. Integer-magnitude tracking excludes temporary
Python/schema work, and no peak heap result was measured for QSG-1.

## Disposition for the designated reviewer

The preserved evidence supports the limited reported fixture behavior and the
separation between real metric validity and rational reconstruction. Independent
review should explicitly assess the source/formula dependence, atomic-refusal
coverage and comparison limits above. This audit neither accepts QSG-0 gates
nor invents QSG-1 gate decisions. QSG-2 may proceed as an independently bounded
mathematical specification; implementation and execution require their own
reviewed contract and authorization.
