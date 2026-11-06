# SOUL-EVIDENCE-0 findings

**Disposition: PARTIAL.** The second registered attempt passed all 26 cases,
including the added malformed-record case, but the prediction result reports a
candidate as `consistent` together with the surviving set rather than
explicitly classifying it as provisional versus uniquely established. A reader
can infer that distinction from the survivors, but the registered prediction
interface does not itself report the required epistemic state. The result is
preserved rather than promoting an incomplete semantic check to a bounded pass.

## Results

A separately coded checker reconstructs all candidate survivors from anchored
observations; it does not call the producer's hypothesis function. Its manifest
binds record IDs and content, hypothesis definitions and version, and
interpretation rules and version. With that conditional trusted anchor, attempt 2
returned the registered expected verdict and expected typed finding in 26/26
cases: seven SUPPORTED, eight UNSUPPORTED, five UNKNOWN, five INVALID_EVIDENCE
and one UNVERIFIED. The complete case inputs, anchors, outputs and expected
results are in `evidence/attempt2_results.json`.

The cases cover direct and transitive support, reversed chains, incomplete
premises, unrelated evidence, survivor reconstruction, valid and false rejection,
wrong elimination and retention, multiple and zero survivors, forged uniqueness,
unique consistency within the declared boundary, missing evidence and anchors,
substituted language and rules, and an anchored malformed relation. An incomplete
subset that would leave a unique survivor is not accepted as complete. A derived
prediction was correctly checked as following the chosen candidate even though
the later evaluator outcome was false; prediction derivation is not prediction
accuracy. Semantic controls include well-formed records with invalid claims,
not merely checksum failure.

Five focused tests passed and two complete attempt-2 outputs were byte-identical.
Identical runs are reproducibility, not independent formal verification.

## Attempts and limitations

Attempt 1's 25 registered cases passed twice, but subsequent review with a
malformed yet anchored relation missing its endpoint caused a `KeyError` instead
of INVALID_EVIDENCE. Original source and results are preserved in
`evidence/attempt1_source/` and `evidence/attempt1_results.json`; the original
registration hash file is retained. Attempt 2 validates required record fields
before reasoning and adds the malformed-record case. The two attempts are distinct;
no acceptance criterion was changed. Attempt 1's source snapshot corresponds to
the original recorded source hashes, whose paths refer to their original location.

**Established within the registered language:** conditional checking of the
listed direct and two-premise transitive deductions, reconstruction of finite
hypothesis survivors and selected counterexample claims, and the listed anchor
and evidence completeness controls. The checker does not call the producer's
hypothesis evaluator, but shared specification and independent code do not
constitute a formal proof of correctness.

**Observed:** five top-level verdicts and bounded-uniqueness findings behaved as
expected on the 26 fixed cases; a structurally sound but semantically false
claim was rejected. The prediction interface's consistency label remains weaker
than explicit provisional/unique reporting, so S6 is incomplete.

**Assumed:** the trusted anchor and manifest are supplied through a trustworthy
channel, the bounded language and interpretation are correct, and observation
labels reflect the trusted fixture. A digest cannot establish authorship or
external truth and does not resist replacing both data and anchor. The current
validator is bounded to its registered schemas; it is not a hardened parser for
arbitrary hostile input. No claim of universal malformed-input coverage is made.

**Unknown:** general proof checking, noisy and contradictory real-world evidence,
unrepresented hypotheses, arbitrary rule languages, and cross-engine migration
of learned knowledge. Prediction consistency is not universal truth or certainty.

**Excluded:** network access, production integration, public release, physical
hardware, QAF/SPU changes, subjective identity and the SOUL-CONTINUE-1 successor.

## Reproduction

Python 3.10.12, base git revision recorded in the handover. Attempt-2 inputs,
source and instructions were hashed before the two registered runs; hash checking
and five focused tests passed. The [README](README.md) contains commands and
resource bounds. Outputs were written to disposable `/tmp` directories and the
first of each attempt was copied into the research evidence directory.
