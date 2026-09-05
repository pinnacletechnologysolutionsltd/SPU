# INA226 SOM capture set — 2026-09-03

The 30 real captures behind the shelved SOM anomaly-classifier campaign.
10 blocks (`b00`-`b09`) x 3 classes (`normal`, `elevated_load`,
`current_limited_stall`), ~1.4 s each at ~10 ms sampling, integer microamps.
Probe `tamiya_75026_v1`. Verify with `sha256sum -c SHA256SUMS`.

**Provenance.** Rescued 2026-09-05 from `build/ina226_capture/captures/`,
where they were the only copy and were excluded by `.gitignore:23`
(`git ls-files` returned 0). They are **unreproducible**: the load was applied
by hand, and the fixture that would make it repeatable is exactly what the
queued retest has to build first.

**Known contamination.** The `elevated_load` class drifted across sessions —
**b06 at 138.3 mA against b07 at 124.0 mA** — moving the class distribution
across the decision boundary. This is why `elevated_load` scored 60-70% recall
while `normal` and `current_limited_stall` both hit 90%. The campaign result is
ambiguous, not negative.

Full context and the queued fixed-load retest: `docs/SESSION_HANDOVER_2026-09-04.md` §5.
Pipeline: `tools/ina226_capture_pipeline.py`. Features: `software/lib/som_current_monitor.py`.
