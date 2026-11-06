# SOUL-CONTINUITY-0 findings

**Disposition: BOUNDED PASS.** One hand-constructed deterministic scenario meets
the specified operational acceptance criteria. This is preliminary exploratory
software evidence, not an architectural qualification or independent review.

## Registered results

The pre-migration checkpoint holds eight observations, including one erroneous
reading followed by an explicitly labelled correction, a separately labelled
world change, two unresolved weak contradictory readings, and a supplied rule.
The common continuation introduces two new entities and relationships. The
migrated engine uses the earlier rule to answer the new nested relationship.

| Metric | C0 continuous A | C1 migrated B | C2 summary B | C3 fresh B |
|---|---:|---:|---:|---:|
| Historical observations retained / 8 | 8 | 8 | 0 | 0 |
| Current relationships correct / 3 | 3 | 3 | 3 | 0 |
| Revision chain correct / 1 | 1 | 1 | 0 | 0 |
| World-change history distinguished / 1 | 1 | 1 | 0 | 0 |
| Original provenance records retained / 8 | 8 | 8 | 0 | 0 |
| Appropriate unknown / 1 | 1 | 1 | 1 | 1 |
| Transfer correct / 1 | 1 | 1 | 1 | 0 |
| Checkpoint integrity valid | yes | yes | yes | yes |

Fresh responses for the three historical relationships and transfer were
`unknown`, not wrong guesses; the accuracy score counts abstention as not correct.
All conditions abstained on the conflicting weak readings. C2 matches C1 on all
five task answers, so these tasks do **not** establish a behavioral advantage of
full history over a factual summary. C2 loses the original evidence and revisions;
its synthetic summary sources are not treated as the original provenance.

Migration between the same schema versions preserved the full state exactly:
zero missing/altered state, no intentional or untranslatable omissions, and a
validated input/output checkpoint digest. The engines give identical answers in
this fixture; a difference in engine capabilities has not been demonstrated.

All seven listed controls in `evidence/results.json` passed: relationship removal
changes the answer to unknown; a changed evidence reference fails digest checking
and still fails proposition checking after recomputing the digest; an incorrect
expected predecessor is rejected; unresolved contradiction and unknown cases
abstain; and a valid checkpoint remains usable. Two divergent forks validate
against the same parent digest and have different contents and checkpoint hashes.
Integrity checks only apply when the caller validates the checkpoint and supplies
a trustworthy expected predecessor. They are not an adversarial authentication
mechanism. The rehashed reference test detects this particular mismatch, not all
possible coherent forgeries.

## Interpretation

**Established within this fixture:** a validated A checkpoint survives JSON
serialization and can be interpreted by B; observations, original provenance,
revision links, unknown state, and fork ancestry remain available. B applies the
recorded rule to a new pair of relationships. The registered negative controls
and valid-record control return the expected outcomes.

**Observed:** a compact summary performs as well as full history on the chosen
answer tasks, but cannot answer the original-history and provenance metrics. The
fresh agent abstains when it lacks the earlier facts and rule.

**Assumed:** sensor source labels, explicit correction/world-change labels,
observations, the transfer rule, expected predecessor and evaluator ground truth
are trusted. The two engines implement very similar deterministic update policies;
they are independently coded but not independently designed belief systems.
The distinction between correction and world change is supplied by the fixture,
not inferred by the agent. Historical recall here measures retained source records,
not free-form recollection.

**Unknown:** generalization to other worlds, conflicting reliable sources,
partially corrupt but semantically coherent records, different inference policies,
real agents, alternate representations, or physical computational substrates.
The experiment does not identify a minimal sufficient state; the summary is one
fixed baseline. A digest alone cannot authenticate authorship or prevent a
coherent replacement of the record and its trusted anchors.

**Excluded:** consciousness, subjective or personal identity, generalized
intelligence, hardware acceleration, production integration, publication,
representation translation, network access and external model APIs.

## Reproduction and provenance

Commands and bounds are in [README](README.md). Run on Python 3.10.12; base git
revision `f35d03cb1175de3a2a474936812d12757b7f57be`, with unrelated existing
workspace changes. Source SHA-256 hashes are recorded in `evidence/source-sha256.txt`.
Three focused tests passed. Two subsequent complete registered runs produced
byte-identical artifact directories (`diff -r` exit 0). The first implementation
was corrected before the recorded runs to ensure C1 actually consumes the
serialized-and-reloaded checkpoint rather than its in-memory predecessor; the
registered results shown above use the corrected path. No acceptance criterion
was changed. Outputs were written to `/tmp` scratch and copied as evidence.
