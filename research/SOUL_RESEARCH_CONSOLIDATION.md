# Soul research: continuity and memory consolidation

2026-11-06. These are bounded software-research results, not architectural
qualification. The completed experiments and their evidence remain unchanged.
Production integration and publication remain on hold.

| Experiment | Disposition | Bounded finding |
|---|---|---|
| [SOUL-CONTINUITY-0](soul_continuity_0/FINDINGS.md) | BOUNDED PASS | A serialized checkpoint retained observations, revisions and provenance across two closely related deterministic engines using the same schema. The destination applied a previously supplied rule. A factual summary matched its answers on all five tasks, but omitted original history and provenance. |
| [SOUL-MEM-1](soul_mem_1/FINDINGS.md) | PARTIAL; registered campaign closed | Archived evidence resolved two cases where a one-candidate summary abstained. Selective retrieval and a full-scan baseline each answered 7/7; the summary answered 4/7. Rule learning and independent evidence-support verification were not established. |

In SOUL-MEM-1 the selective policy visited 8 archive records versus 43 for the
specified full-scan policy, approximately 81% fewer. It retained the full archive
and an index: the sums of stored bytes across separate scenarios were 5,024 for
selective retrieval, 4,705 for full scan and 2,115 for the summary. These are
logical access counts and serialized-state sizes, not measured runtime, CPU
cost or peak memory. The result compares unequal storage budgets and a simple
one-candidate summary against an intentionally full-scan history policy. It does
not establish an advantage over competitive summaries or optimized retrieval.
The SOUL-MEM-1 summary's unknown responses were appropriate abstentions, not
fabricated answers.

## Assumptions and open questions

Both experiments use small constructed scenarios and deterministic, closely
specified policies. They assume the relevant source labels, reliability,
correction or revocation notices and evaluator ground truth. The migration
fixture shares a representation and does not establish portability to a
fundamentally different architecture or substrate. A source reference or digest
is not independent verification that evidence supports a belief. Neither
experiment demonstrates learning a rule from examples, inferring source
reliability, or preserving subjective identity; subjective experience is
outside their scope.

A working research direction is to investigate current knowledge, retained
developmental history and selective retrieval as distinct roles. The results do
not qualify that arrangement as a production architecture. The conceptual
connection to QAF is a question about what information a reduced representation
must preserve for future use; belief revision is not algebraic normalization,
and neither research result establishes equivalence between the systems.

## Candidate work, not authorized here

- **SOUL-MEM-2:** compare a stronger compact summary, full history and indexed
  retrieval under declared storage budgets, including index construction and
  maintenance costs. An equal-budget design and its trade-offs remain to be
  specified and authorized.
- **Rule learning:** separately investigate forming and revising a relational
  hypothesis from meaningful examples and counterexamples, with preservation
  across an engine change.
- **Evidence support:** separately investigate whether cited records actually
  support a conclusion, including relevant but misleading or insufficient
  evidence.

No new experiment is opened by this note. Primary engineering attention returns
to SPU v0.2 qualification within its existing contracts and authorization.
