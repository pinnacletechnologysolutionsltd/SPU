# SOUL-LEARN-0

A small deterministic relational-learning experiment. The world supplies labelled
examples; its target function is held in the evaluator and never passed to the
learner. The learner receives four predeclared Boolean hypothesis templates over
`linked` and `fixed`. This hypothesis space **includes** the target; discovering
a rule outside the language is not tested. The fixed ordering is a simplicity
bias that selects a provisional candidate when multiple candidates remain.
Unresolved is therefore reported even when a provisional prediction is emitted.
An initially wrong candidate is rejected only after labelled counterexample
feedback. Rejected means incompatible with the trusted examples, not proof of a
universal logical negation. Conflicting trusted examples reject all candidates,
leaving unresolved with no prediction.

Training and held-out cases use distinct IDs. The held-out cases reuse feature
combinations from a two-bit domain; they test prediction for new entities and
one previously unobserved combination, not open-ended generalization. A baseline
memorizes exact IDs and abstains for unseen IDs. No model APIs or prior Soul code
are used. Serialization checks retention in the same implementation; this is not
an engine migration experiment. See [findings](FINDINGS.md).

From repository root, each invocation is bounded to 30 seconds and 1 GiB:

```bash
sha256sum -c research/soul_learn_0/evidence/registration.sha256
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_learn_0/test_experiment.py'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_learn_0/evaluate.py /tmp/soul-learn0-run1'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_learn_0/evaluate.py /tmp/soul-learn0-run2'
diff -r /tmp/soul-learn0-run1 /tmp/soul-learn0-run2
```

Evaluator output is written to the supplied scratch path; choose a fresh path to
preserve earlier runs. Source hashes and the registered output are in `evidence/`.
