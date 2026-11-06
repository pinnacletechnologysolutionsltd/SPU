# SOUL-CONTINUITY-0

A deterministic, local, software-only experiment comparing continuation with two
reasoning engines. The agent sees the observations in `scenarios.py`; only the
evaluator uses `TRUTH`. These are fixed registered fixtures, not independently
sampled worlds. Python 3.10 standard library only; no network, model or seed.
See [findings](FINDINGS.md) for results and limits. No production integration or
publication is authorized.

From repository root, run the tests and two independent reproductions, with a
30 second wall limit and 1 GiB virtual-address-space limit per invocation:

```bash
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_continuity_0/test_experiment.py'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_continuity_0/evaluate.py /tmp/soul-continuity-0-repro1'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_continuity_0/evaluate.py /tmp/soul-continuity-0-repro2'
diff -r /tmp/soul-continuity-0-repro1 /tmp/soul-continuity-0-repro2
sha256sum -c research/soul_continuity_0/evidence/source-sha256.txt
```

The evaluator creates/overwrites its named output files in the supplied scratch
directory. Use fresh paths to preserve prior results. `evidence/` contains the
recorded checkpoint, migrated checkpoint, continuation states, forks and scores.
The exact state input is `checkpoint.json`; the JSON round trip is the migration.
The two engines implement `ingest(state, observation)`, `answer(state, key)` and
`transfer(state, subject)` independently over the shared state schema in
`model.py`. Migration uses the same schema: it is not representation translation.

C0 and C1 share the pre-migration history; C1 loads and validates a serialized
checkpoint before continuing under B. C2 is generated from the same checkpoint:
up to 20 current factual beliefs in sequence order plus the standing goal, with
new summary-source records and no earlier observations or revisions. This budget
exceeds the four current facts in the fixture. It includes the transfer rule.
C3 begins empty. All four receive the same continuation observations and queries.

Checkpoints contain canonical JSON SHA-256 digests, schema, lineage, ID, engine,
predecessor digest and state. Validation checks digest, an externally supplied
expected predecessor, evidence existence and proposition match. Hashes are not
signatures: an attacker able to rewrite data and trusted anchors is out of scope.
The caller must validate before use; the engines themselves are not a secure
storage boundary. Forks are separate checkpoints sharing a parent; no merge is
implemented. The evaluator retains raw states for inspection, not just scores.
