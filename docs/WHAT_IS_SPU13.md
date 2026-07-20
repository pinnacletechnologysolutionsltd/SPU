# What is SPU-13?

SPU-13 is a small experimental chip design for calculations where repeatable
results and inspectable decisions matter. It carries selected calculations
with integers and exact fractions rather than rounded decimal approximations.
The design runs on reprogrammable chips called FPGAs.

For a supported job with the same input, stored reference data, and design
version, two runs produce the same result, down to every stored zero and one.
When it classifies an input by assigning it to a category, the decision can be
replayed and reduced to one exact comparison: the winning reference was closer
than the runner-up by the recorded gap.

## What it is not

- It is **not a rival to a general computer processor or a graphics processor
  such as a GPU**.
- It is **not a replacement for ordinary rounded computer arithmetic, often
  called floating point**.
- It is **not certified, qualified, or approved as a safety controller**.
- Its demonstration results are **not a claim that every classifier will be
  accurate**.
- Its current-monitoring path has **not yet been validated with the planned
  physical current sensor**.

“Exact” has a narrow meaning here. Within a supported operation and its tested
input range, the arithmetic does not introduce rounding drift. Stored numbers
still have fixed limits, unsupported inputs can be rejected, and exact
arithmetic does not make a sensor accurate, a model correct, or a system safe.

## What exactness buys

SPU-13 compares exact squared distances to a stored set of reference patterns.
Its evidence record preserves the closest and second-closest patterns, both
distances, their gap, an ambiguity warning, version details, and an integrity
check that detects damaged records. That does not prove the label is right; it
makes the machine's reason concrete enough to inspect and replay.

The same design approach also supports exact rotation and specialist integer
arithmetic demonstrations. In each case, repeatability is an engineering
property with a stated boundary, not a synonym for reliability or safety.

## What exists today

- **Iris classification:** the frozen seven-reference model labels 147 of a
  standard set of 150 flower measurements called Iris correctly. On two FPGA
  families, all 150 complete hardware records match the exact software
  calculation. That is hardware agreement, not 150 out of 150 model accuracy.
- **Exact decision explanation:** the hardware-free demonstration expands one
  Iris decision and checks the exact dividing line between its two nearest
  choices. It explains one decision, not overall model quality.
- **Robotics arithmetic:** an FPGA board returned a supported six-step rotation
  cycle exactly to its starting value. This proves the tested calculation, not
  physical robot accuracy or a complete controller.
- **Lucas arithmetic:** a Tang FPGA completed 100 cycles of repeated scaling
  and returned to its seed exactly at every cycle boundary. This is a
  specialist demonstration, not a universal number format.

The next monitoring milestone is deliberately more modest: capture real
current measurements from the planned sensor, freeze the test before scoring,
and see whether coarse load or stall changes are distinguishable. No physical
accuracy or power claim is made before that run.

## Door 1: maintenance and reliability

The useful question is not merely “did the classifier raise an alert?” but
“what made this sample closer to the alert pattern than to the normal pattern?”
SPU-13 records both candidates, both distances, and the gap. A small gap marks
the decision as ambiguous instead of making it look strong.

This could help investigate a bounded equipment-monitoring decision. It does
not identify bearing wear, predict remaining life, or replace inspection. The
current test measurements are generated, not read from a physical sensor; that
study remains pending.

[See one decision expanded into its exact comparison.](DEMO_TOUR.md#4-exact-voronoi-decision-evidence)

## Door 2: robotics

Repeated coordinate changes can accumulate rounding error. On SPU-13's tested
path, a supported rotation followed by the operation that undoes it returns to
the starting value without numerical drift. The calculation replays exactly in
software and hardware.

The boundary matters: a real robot also has sensor error, flex, backlash,
timing, calibration, and control hazards. The demonstration proves selected
coordinate calculations only; it is not a robotics safety case.

[See the hardware-free rotation demonstration and its boundary.](DEMO_TOUR.md#1-rational-robotics-closure)

## Door 3: evaluation and commercial pilots

A sensible evaluation today is a bounded replay study, not a deployment
promise. Start with a labelled table of measurements, freeze a small set of
reference patterns in software, then compare every hardware record with the
exact software calculation before discussing a field trial.

The project already has tools that turn such a table into stored reference
patterns and load them into a writable chip classifier. Physical sensing,
packaging, certification, pricing, and commercial terms are unfinished. Any
pilot should name its data, decision scope, acceptance test, and prohibited
claims in advance.

[Discuss a bounded evaluation.](mailto:johncurley@pinnacletechglobal.com)

## Evidence behind this page

The public [current-status summary](CURRENT_STATUS.md) separates software-only
tests from physical-board results. The [hardware evidence record](hardware_evidence.md)
lists the commands, outputs, and limits behind the board claims.
