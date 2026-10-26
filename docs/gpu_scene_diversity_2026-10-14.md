# GPU scene diversity and observation collisions

This software-only study examines which spatial distinctions are retained by
the GPU-SOM-0A 16×16 tile feature payload. It reuses the existing T1d parser,
packet compiler, finite-width device model, observer, and independent ideal
pixel reference. It does not train a SOM or change GPU-SOM-0A.

## Frozen scenes

The suite contains six valid two-triangle scenes: two disjoint scenes related
by a within-tile translation, two overlapping depth orders, an equal-depth
tie, and a shared-color control. The background remains the profile's fixed
black value. Scene and independent sample-reference hashes are locked in
`examples/gpu/scene_diversity/manifest.json`; evaluator source hashes are locked
in `fixtures/gpu_scene_diversity_source_lock.json`.

The collision pair translates triangle 0 by (+3,+3) pixels wholly within the
same 16×16 tile. Its integer shape and pixel count remain fixed; its three
depths are all 100 and its RGB444 value remains `[15,0,0]`. Triangle 1 is
unchanged and disjoint. The finite-width observer feature payloads are required
to be byte-identical. The task oracle compares per-pixel coverage, covered
primitive identity, winner, and RGB. Exact rational depth differences alone
do not count as different task outputs in this initial study, though exact
depths remain in the hashed ideal reference map.

Fixture preparation found an exact feature collision with 78 task-output pixel
differences. The focused test rechecks the complete feature payloads and both
per-pixel maps. This result shows that tile aggregation loses within-tile
arrangement for this fixture; it does not establish an error rate or general
scene behavior.

The focused test command passed 4/4 tests, including all six frozen sample
sets, both exact feature payloads, the independent full-frame task-map
difference count, hash locks, and atomic failure cleanup.

## Run the focused checks and evaluator

Run from the repository root. The evaluator output destination is fixed and
must not already exist:

```bash
python3 software/tests/test_gpu_scene_diversity.py
python3 -m software.spu_gpu_eval.cli scene-diversity --suite examples/gpu/scene_diversity/manifest.json --out build/gpu_evaluation/scene_diversity_01
```

The evaluator publishes only after all six full-frame maps, frozen sample
expectations, collision conditions, artifact hashes, and report consistency
checks pass. It records device-model versus ideal-reference task disagreements
explicitly. Exact rational depth and finite-width device depth are preserved in
their own representations rather than compared as interchangeable numbers.

## Evidence status and limits

The implementation and fixture checks are authorized. The final evaluator
publication has **not been launched**; its output directory and result
manifest do not yet exist. The expected collision is exercised by the focused
test, but no completed six-scene suite report is claimed.

The suite establishes only the listed cases under the T1d software profile.
It does not evaluate SOM quality, codebook compression, scene generalization,
renderer optimization, physical GPU behavior, or hardware performance. The
optional same-visible-RGB/different-feature diagnostic is not included in the
frozen suite.
