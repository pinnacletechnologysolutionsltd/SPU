# SOUL-EVIDENCE-0

A deterministic, bounded evidence-checking experiment under the proposal and
amendments in [CONTRACT](CONTRACT.md). `producer.py` constructs hypotheses and
claims; `checker.py` independently evaluates candidate truth tables, validates
trusted inputs and reconstructs the survivor set without calling the producer.
The checker does not see evaluator expected results. The evidence registry and
manifest contain exactly the declared records and bind their contents, candidate
definitions, language version, predicates, inference rules and versions. The
SHA-256 manifest digest is supplied through a trusted external channel. Hashing
checks consistency with that anchor; it cannot establish authorship or source
truth, and does not defend against replacing both data and anchor.

All five A2 verdicts are used, with INVALID_EVIDENCE before UNKNOWN before
UNVERIFIED before semantic outcomes. A missing anchor or missing declared
record is UNKNOWN; a present mismatched anchor, modified record, substituted
language or rules, or extra record is INVALID_EVIDENCE. A missing cited ID is
UNKNOWN. This deliberately does not conflate missing with malformed records.
`CONSISTENT`, `CONTRADICTED` and bounded uniqueness are typed findings, not
verdicts. Exactly one candidate consistent with every complete validated
observation yields `UNIQUE_WITHIN_DECLARED_HYPOTHESIS_AND_EVIDENCE_BOUNDARY`.
It does not establish empirical truth or uniqueness outside the declared space.

The checker covers direct facts, a two-premise `subset` transitive deduction,
finite Boolean hypotheses, survivor claims, counterexamples and predictions.
It reconstructs from all complete observations, not the learner's proposed
survivors. A prediction can follow from a hypothesis while being empirically
wrong; the later outcome is evaluated separately. The Boolean language and
trusted semantics are fixed and very small. The producer and checker are
separately coded but not formally proved independent or correct. They share
registered definitions and independently coded predicate meanings; evidence,
labels, anchoring channel and semantics are assumptions. Unsupported kinds and
rules return UNVERIFIED; this is not a general theorem prover.

The code does not reuse prior experiment implementation. The scenario
specifications and independently written expected outcomes are fixed in
`scenarios.py`; each output includes full checker inputs, expected and actual
verdict, typed finding and per-case result. See [findings](FINDINGS.md).

Run from the repository root with Python 3.10+ standard library. Each invocation
is limited to 30 seconds and 1 GiB virtual address space. Use fresh scratch
paths; output files in those paths are overwritten.

```bash
sha256sum -c research/soul_evidence_0/evidence/registration.sha256
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_evidence_0/test_experiment.py'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_evidence_0/evaluate.py /tmp/soul-evidence0-repro1'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_evidence_0/evaluate.py /tmp/soul-evidence0-repro2'
diff -r /tmp/soul-evidence0-repro1 /tmp/soul-evidence0-repro2
```
