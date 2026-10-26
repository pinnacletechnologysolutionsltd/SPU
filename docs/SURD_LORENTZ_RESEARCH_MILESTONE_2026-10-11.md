# Surd CPU Lorentz research milestone

Date: 2026-10-11. Result: **focused instruction-executing RTL simulation PASS**.
Scope: exact one-dimensional boost composition, application invariants and a
deliberately incorrect arrival-time interpretation. No RTL or shared test
infrastructure was changed.

## Recorded result

The Surd-enabled canonical CPU dispatcher retired **853 instructions**. All
ten tested exact compositions preserve both the boost invariant and the
transformed-event interval. Composition 34 exceeds the signed-64 coefficient
bound, reports overflow status 2 and preserves the destination. A deliberately
poisoned expected multiplication result causes an atomic-tuple mismatch and
nonzero simulator exit.

Evidence: [machine-readable results](research/surd_lorentz_20261011/evidence/results.json),
[runtime trace](research/surd_lorentz_20261011/evidence/runtime.log), and
[negative-control trace](research/surd_lorentz_20261011/evidence/negative_control.log).
The historical harness prints its generic kernel-stream PASS label; the
experiment did not execute the separate retained robotics kernel corpus.

For the boost

\[
L=\begin{pmatrix}2&-\sqrt3\\-\sqrt3&2\end{pmatrix},
\qquad L^n=\begin{pmatrix}a_n&-b_n\sqrt3\\-b_n\sqrt3&a_n\end{pmatrix},
\]

the independent integer recurrence is
\(a_{n+1}=2a_n+3b_n\), \(b_{n+1}=a_n+2b_n\), beginning with \((1,0)\).
Ten literal coefficient rows additionally check that recurrence. Actual Surd
instructions compute both conjugate products and transformed coordinates,
with tuple readback, write and retirement checks in the existing harness.

| Compositions | Gamma | Radical coefficient | Interval | Incorrect gamma rule |
|---|---:|---:|---:|---:|
| 1 | 2 | 1 | 1 | 2 |
| 2 | 7 | 4 | 1 | 4 |
| 3 | 26 | 15 | 1 | 8 |
| 10 | 262087 | 151316 | 1 | 1024 |

Here c=1, and the transformed event represents a final constant-velocity
cruise with one unit of proper time. Acceleration and prelude duration are
excluded. The experiment is not a complete mission trajectory or arrival-date
prediction. Nine of ten predictions from the deliberately incorrect rule
\(\gamma_n=2^n\) disagree with the correct result; these disagreements are
experimental findings, not arithmetic failures. The ten-composition ratio is
exactly 262087/1024.

## Three verification responsibilities

| Layer | Responsibility | Experiment evidence |
|---|---|---|
| Arithmetic engine | Correct bounded Surd operations and failure preservation | Exact readbacks, overflow rejection and falsifiable expected-result checker |
| Mathematical application | Valid Lorentz transformation and interval | Valid compositions give invariant 1; coefficients (2,2) give invariant −8 |
| Mission software | Correct interpretation of boosts, frames and elapsed time | A valid computed transformation coexists with the incorrect gamma interpretation |

Arithmetic succeeds for the malformed coefficients (2,2), correctly producing
\(2^2-3(2^2)=-8\). The application must reject that value as a Lorentz boost.
Exact arithmetic does not enforce physical validity or validate a mission's
assumptions. This example transfers to transformation checks in graphics,
robotics and simulation without claiming qualification of those applications.

These are negative controls, not a claimed formal Davis Gate. The poisoned
expectation demonstrates checker falsifiability; malformed coefficients and
the wrong gamma rule demonstrate application/model discrimination. Overflow is
a separate bounded-failure check. Detection of these specific faults does not
prove detection of every possible implementation defect. Their expected
failures are successes of the verification method, not CPU failures.

## Preserved evidence and future demonstration

The [archive manifest](research/surd_lorentz_20261011/evidence/archive_manifest.json)
records hashes for the retained script, instruction stream, independent
expectations, results, source provenance and traces. The archived
[review](research/surd_lorentz_20261011/evidence/REVIEW.md) describes the focused
experiment. The full compiled binary remains in the original workspace
evidence directory:

`build/spu_surd_register/lorentz_model_experiment_20261011/attempt_01/`.

Check the preserved artifacts from the repository root:

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib, json
base = Path('docs/research/surd_lorentz_20261011/evidence')
manifest = json.loads((base/'archive_manifest.json').read_text())
for name, expected in manifest['files'].items():
    assert hashlib.sha256((base/name).read_bytes()).hexdigest() == expected, name
print('PASS preserved Lorentz evidence:', len(manifest['files']))
PY
```

The archived script retains its original workspace and frozen-source paths;
the reproduction commands require that snapshot and its tools. A portable
public demonstration remains future work, with an explicit source-selection
and dependency contract. Preservation here does not authorize a new build.

This milestone establishes focused simulation evidence only. It does not
establish full repository qualification, unbounded arithmetic, a complete
physical model, integrated CPU fit, legal routing, 25 MHz timing, silicon,
speedup or energy efficiency. Both software VMs continue to reject Surd
instructions. Integrated CPU routing remains a separate campaign.
