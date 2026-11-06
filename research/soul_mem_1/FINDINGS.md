# SOUL-MEM-1 findings

**Disposition: PARTIAL.** The registered trial compares the three retention
policies and meets most of the measurement and control objectives. The S5
fixture provides a rule explicitly and its two example records merely assert
`valid`; it does not demonstrate learning a rule from meaningful examples.
The attribution check tests relevance of a returned source ID, not whether that
source independently supports the answer. Consequently the intended learned-rule
and source-attribution evaluations are incomplete. These limitations were not
corrected after viewing the registered results.

## Registered results

| Scenario | M0 summary | M1 full scan | M2 selective | Archive records read M0 / M1 / M2 |
|---|---|---|---|---|
| S1 stable | box ✓ | box ✓ | box ✓ | 0 / 3 / 0 |
| S2 correction | unknown | red ✓ | red ✓ | 0 / 5 / 3 |
| S3 current; historical | open ✓; unknown | open ✓; closed ✓ | open ✓; closed ✓ | 0 / 8 / 2 |
| S4 conflicting sources | red ✓ | red ✓ | red ✓ | 0 / 4 / 0 |
| S5 supplied-rule application | chest ✓ | chest ✓ | chest ✓ | 0 / 18 / 0 |
| S6 reactivation | unknown | depot ✓ | depot ✓ | 0 / 5 / 3 |

The two unknown current answers and one unknown historical answer from M0 were
appropriate abstentions under its retained information, rather than false
assertions. None of the policies produced an unjustified certainty in these
registered cases. S3 demonstrates the difference between knowing the current
state and reconstructing its earlier value.

| Aggregate across six separate scenarios | M0 | M1 | M2 |
|---|---:|---:|---:|
| Correct answers / 7 | 4 | 7 | 7 |
| Archive record visits | 0 | 43 | 8 |
| Canonical archive bytes visited | 0 | 4,062 | 676 |
| Index bytes visited | 0 | 0 | 99 |
| Defined query operations | 9 | 52 | 20 |
| Sum of separate scenario state bytes | 2,115 | 4,705 | 5,024 |
| Defined ingestion operations | 27 | 27 | 54 |
| Relevant / archive visits | undefined | 22 / 43 | 7 / 8 |

These are sums over separate states, not peak storage or timing measurements.
Index bytes and archive bytes are counted separately; Python object access and
actual I/O, CPU cost, memory allocation and index construction costs beyond the
simple counters are not measured. M1's policy scans all records for every
lookup, so M2's lower access count is relative to that intentionally simple
baseline, not proof that selective retrieval beats an optimized history system.
M2 retains the entire archive and a measured index, and costs more stored bytes
than M1 in all six scenarios. The evaluator-only relevance list may classify a
related but unnecessary record as relevant; precision is relative to that oracle.

All eight recorded control outcomes passed: irrelevant records were excluded
from the selected S6 retrieval; withholding its critical fact led to unknown;
a strong source beat two weaker contradictory sources; the stable task needed
no M2 retrieval; a changed revocation reference failed the digest and structural
checks; valid provenance was accepted; and disabling retrieval made the S6
answer unknown. The archive validator is exercised as a separate control, not
as a mandatory gate on every answer.

## Interpretation

**Established within these fixtures:** M1 and M2 can use archived observations
that the selected one-candidate summary discards after a revocation. M2 read
fewer archived records than the specified full-scan policy while giving the same
answers. A summary sufficed for the stable, conflicting-source and supplied-rule
answer tasks. Results are deterministic in two runs.

**Observed:** historical access changed decisions in S2 and S6 from abstention
to the evaluator's correct value. This advantage depends on deliberately unequal
storage and the summary's fixed one-candidate policy. A richer compact summary
could retain backup evidence; no equal-storage or alternative-summary comparison
was performed. Source strength and revocation notices are explicitly supplied.

**Assumed:** the evaluator's world facts, source reliabilities, revocation notices,
epoch labels, evidence relevance and trusted digest anchor are correct. The
case-specific answer keys and relevance are only used by the evaluator after
agent answers. Expected source IDs are not independently validated against a
support relation.

**Unknown:** whether history improves decisions against equally sized or more
capable summaries, how an agent would infer reliable sources or learn rules from
examples, and whether fewer logical record visits translate into faster runtime.
The selected fixtures do not establish generalized memory sufficiency.

**Excluded:** real-world autonomous operation, model APIs, neural training,
production use, publication, physical substrates and subjective identity.

## Reproduction and provenance

Python 3.10.12, git base `f35d03cb1175de3a2a474936812d12757b7f57be`, with
unrelated workspace changes. Five focused tests passed. Two registered runs
were byte-identical (`diff -r` exit 0); no policy or acceptance criteria were
changed between them. Registration hashes, detailed per-query answers, IDs,
resource counts and all controls are in `evidence/`. Commands and resource
limits are in [README](README.md). Scratch output was copied into the research
directory as evidence.
