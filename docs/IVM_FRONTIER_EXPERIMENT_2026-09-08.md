# IVM frontier — software transaction-to-display experiment

Status: completed software research; no production RTL or hardware claim.
Baseline HEAD: `0891e56`. Owner's provisional fixed orthographic profile,
exact rational visibility, measured-loss adapter and bounded-domain decisions
apply. Earlier [frontier derivation](IVM_GPU_FRONTIER_2026-09-08.md) is retained.

## Result

The complete byte-packet -> validation -> prepared scene -> epoch activation ->
native samples -> square adapter path agrees with its exact references in the
tested cases. Premature activation and stale adapter data are detected by
negative controls. No approximate depth was needed.

Nearest-site reconstruction differs from direct exact square sampling at
101/1,375 output pixels (7.345%). This is retained sampling loss, not an oracle
failure. No application-quality acceptance threshold was supplied, so this
number is not labelled commercially acceptable or unacceptable.

The native lattice provides an integer coefficient/stepping representation for
this lattice-aligned view and, by construction, native triangular sample sites.
It does NOT provide an exclusive exact-visibility or arithmetic-light sample
capability: an exact square row-threshold implementation also removes irrational
arithmetic from sample execution. No IVM-specific throughput, storage, energy
or image-quality advantage is established by this experiment.

## Reproduce and evidence

```bash
python3 software/tools/run_ivm_frontier_experiment.py
python3 software/tools/ivm_raster_feasibility_probe.py
```

The first prints deterministic JSON and exits nonzero on any failed assertion
or exception. It does not use the known-imperfect aggregate PASS classifier.
[Frozen full output](bench_captures/2026-09-08_ivm_frontier_software.json) includes
per-scene error, source hashes, operation counts and widths. The earlier
feasibility probe still passes unchanged. No broad regression, synthesis or
hardware operation was needed; the software protocol is not UART/CDC proof.

Files added:

- `software/lib/ivm_frontier_model.py`: exact preparation, native/square scans,
  adapter, independent reference, and square row-threshold counter-baseline.
- `software/lib/ivm_frontier_protocol.py`: incremental framed-byte receiver and
  explicit prepare/queue/activate state machine.
- `software/tools/run_ivm_frontier_experiment.py`: fixed-seed corpus, hostile
  transactions, negative controls, counters and JSON report.

## Declared profile and fair-comparison limits

Two opaque RGB444 triangles; fixed tetrahedral-axis orthographic view; exact
signed zero-sum integer Quadray components in [-9,9]. This bound is required by
the retained extent-8 witness: one vertex is `(3,7,-1,-9)`.
This is an intentional canonical wire-format restriction, not acceptance of
every gauge-equivalent Quadray tuple. No receiver normalization is promised.
Adversarial check: `(1,-1,0,0)` and `(2,0,1,1)` both project to `(-2,1,4)`;
the model/protocol accept the former and reject the latter's nonzero sum.
No arbitrary camera, perspective, geometric clipping or texture claims. Samples
outside the viewport are simply not emitted; zero-area triangles are rejected.

Projection is `U=2b-c-d, V=-b+2c-d, h=3a-b-c-d`, with native sites `(3i,3j)`.
Projected vertices are not snapped. Coverage has half-open edge ownership;
nearer means smaller exact N/D; equal depth chooses primitive ID 0. Receiver
orders records by ID, not arrival order.

Both renderers allocate 49 unit-pitch sites (indices -3..3 in each direction).
Both produce the same physical square output window: x,y in -2..2, 25 points.
The native adapter selects Euclidean-nearest sites, with row/index tie-break.
Its mapping is checked against all sites in a larger -8..8 search using
independent rational interval distance comparisons. More distant sites cannot
win: outside that patch their minimum distance from the origin exceeds
`9*sqrt(3)/2`, well beyond the output-window radius plus the measured nearest
distance. Some selected sites require |i|=3, so radius 2 is insufficient.

The initial 81-site allocation was reduced to this smallest symmetric native
patch without changing any reconstruction result. Equal allocated counts and
common output window do NOT mean equal exterior patch shape or optimal density.
Only 25 native sites are actually referenced by this fixed adapter; the square
renderer could likewise omit its guard sites. No sample-count saving is claimed.

Square sampling retains the SAME physical geometry: a field at square (x,y)
has exact value `(3*A*x+C)+(-A+2*B)*y*sqrt(3)`. Algebraic sign uses integer
squares, not rounded vertices. Independent Fraction barycentric references
re-project raw Quadrays through the Cartesian tetrahedral embedding and certify
signs using a proven rational enclosure of sqrt(3); an ambiguous enclosure
would fail, not guess. The references do not use prepared edge/depth fields.

## Verification results

| Check | Observed |
| --- | --- |
| Scenes: 7 named adversarial + 48 deterministic random | 55 accepted and activated |
| Native and direct-square samples versus independent exact reference | 5,390 comparisons, zero mismatch |
| Compiled square row thresholds versus direct exact square samples | 2,695 comparisons, zero mismatch |
| Transaction/epoch tests | 50 pass |
| Minimum nonzero projected area denominator | D=3 accepted |
| Fractional projected sites | Exercised without snapping |
| Rational-depth witness | 12/7 vs 3/2; correct second-triangle winner |
| Shared interior tessellation sites | Exactly one owner at all 9 tested sites |

Transaction population: commits at four preparation phases and on either side
of a boundary; truncation at every one of 24 packet cut points; CRC, version,
length, exact sum, range, ID, colour, profile, missing primitive, duplicate,
degenerate, stale epoch, wrong epoch, busy and unknown opcode refusals; reset;
old immutable frames draining after new activation; stale adapter samples.

Preparation's three ticks are ABSTRACT software events, not estimated RTL
cycles. COMMIT is rejected until READY; receipt is distinct from ACTIVATED.
At a boundary, a queued complete scene replaces the active immutable snapshot.
Incomplete preparation retains the old scene. CRC/timeout abort pending work;
reset returns to blank. Buffer consumers validate the frame epoch.

Negative controls were observed to discriminate:

- Unsafe commit publishes one newly prepared triangle with old triangle/depth
  state: renderer rejects the mixed prepared epoch.
- Injecting an old-epoch sample into the adapter cache: adapter rejects it.
- All-inclusive edges double-own three diagonal sites.
- Negating the depth comparison field changes the rational witness winner.
- A deliberately undersized signed-16-bit H limit rejects an in-domain scene.

Retained test-design correction: the first range-extreme negative-control
fixture produced H=0 because its triangles had identical depth planes. The
assertion correctly failed to observe overflow. Replacing one vertex with
`(9,-9,-9,9)` produced H=(7,558,272,15,116,544,0), making the width control
nonvacuous. No oracle or quality threshold was changed to obtain a pass.

## Arithmetic bounds and widths

Widths are conservative domain proofs, not minimum circuit widths or maxima
inferred solely from random tests. Let R=4*9=36 and Z=36; then:

```
|A|,|B| <= 2R; |C| <= 2R^2; 0 < D <= 8R^2
|N_A|,|N_B| <= 6RZ; |N_C| <= 6R^2 Z
|H_A|,|H_B| <= 2*Dmax*N_AB; |H_C| <= 2*Dmax*N_C
native scan |H| <= 18*H_AB + H_C  (scaled sites -9..9)
```

Bounds include evaluation outside triangle coverage, setup products and signs.
The model checks declared magnitude bounds at measured arithmetic stages;
per-column widths follow the analytic formulas.

| Quantity | Safe width for profile | Observed signed width |
| --- | --- | --- |
| Quadray component | 5 signed (wire uses 8) | 5 by fixture endpoints |
| Projected coordinate/depth | 7 signed | 7, including intermediates |
| Edge A/B; C | 8; 13 signed | 8; 11 |
| D | 14 unsigned | 12 signed |
| N A/B; C | 14; 20 signed | 13; 11 |
| H A/B; C | 29; 34 signed | 25; 18 |
| Native H accumulator | 35 signed | 29 maximum across scan/seed stages |
| Direct-square H real/surd components | 34; 32 signed | combined stage maxima <=29 |
| Direct-square sign intermediates | 67 signed | 55 |

The square row-threshold compiler moves those algebraic sign decisions into
preparation, emitting 3-bit cuts (0..7) plus direction bits. Sample execution
then uses only integer index comparisons. The same optimization could also be
applied to native rendering; its existence prevents an exclusive add-only
IVM claim. No width implies a tested FPGA frequency or resource count.
Adversarial width adjudication: 8,707,129,344 is the conservative domain bound,
not the measured peak of the named range-extrema fixture. That fixture's H
evaluates from -204,073,344 to +204,073,344 over this scan, within signed 32 bits.
This does not prove 32 bits sufficient over the full domain. Reusing the legacy
edge stepper unchanged is unsupported: its 32-bit accumulator and 16-bit slope
ports are not the proposed H interface. No such RTL integration was performed.

## Operation counts

Counts are scalar integer field operations in THIS model. Constant multipliers
are included, so a 'multiply' is not a DSP requirement. Boolean muxes, loop/index
control, CRC and packet parsing are excluded. Reference/oracle work is excluded.
These counts are not Python-runtime or FPGA-throughput measurements.

| Work | Add/subtract | Multiply | Sign/comparison |
| --- | ---: | ---: | ---: |
| Common geometry preparation, 55 scenes | 4,939 | 3,294 | Not separately metered |
| Native scan including seed/step setup, 55 frames | 19,250 | 1,540 | 18,865 |
| Direct exact square scan, 55 frames | 26,369 | 22,897 | 44,849 |
| Square row-threshold compilation, 55 scenes, additional to common preparation | 15,292 | 22,006 | 20,297 |
| Compiled square sample execution, each frame | 0 field arithmetic | 0 | 343 threshold comparisons |
| Native adapter-map construction, once per fixed profile | 10,012 | 11,811 | 2,662 |

Native per frame: 350 adds/subtracts, 28 constant-scale/seed multiplications,
343 signs. Of these, 336 additions are scan/row advances; there are no
sample-time depth multiplications. Compiled square execution reads 49 row cuts
per frame. Both adapters perform 25 sample reads and zero per-frame arithmetic.
Compile/setup work can be reused across unchanged frames; native map lookup is
fixed-profile, while square row cuts must be recompiled when geometry changes.
The direct-square sign implementation is not an optimized conventional GPU.

## Storage estimates (logical packing, not synthesis)

| State | Bits / bytes |
| --- | --- |
| Prepared scene: six edges/ownership, H, colours, IDs, epoch/profile | 322 bits |
| Two prepared banks | 81 bytes packed together |
| Maximum packet / staging geometry records | 24 / 30 bytes |
| N/D preparation scratch | 124 bits |
| Native scan registers, including increments | 394 bits |
| One 49-sample colour/coverage/winner buffer plus epoch | 702 bits |
| Two sample buffers | 176 bytes packed together |
| Native fixed map | 150 bits, 19 bytes rounded |
| Square compiled row-cut table | 154 bits, 20 bytes rounded |

Epoch is per immutable buffer, not 16 bits copied into each stored pixel; the
Python model retains per-token tags to expose mixing. Counts exclude control,
FIFO sizing and intermediate pipeline registers. Components may share storage;
do not sum these into a claimed device footprint. The experiment chose complete
sample buffers for adapter simplicity; it does not prove they are necessary
or that a framebuffer-less adapter is possible for every output mapping.

## Reconstruction loss

Declared adapter: Euclidean-nearest native point, no filtering. Reference:
direct exact point sampling at the same square output positions.

| Measure | Observed |
| --- | --- |
| Coverage changes | 92 / 1,375 pixels |
| Winner changes where both outputs covered | 9 / 1,375 pixels |
| Total differing output pixels | 101 / 1,375 = 7.345% |
| Worst scene | 5 / 25 = 20% differing pixels |
| RGB absolute error / channel count | 1,650 / 4,125 = 0.4 levels, on 0..15 scale |
| Maximum sample displacement | approximately 0.517638 unit pitch |
| Direct-square and compiled-square discrepancy from exact square reference | Zero |

The distance bound is certified for all 25 mapped destinations. It does not
bound arbitrary image mismatch rates: discontinuous edges can change colour
fully over an arbitrarily small displacement. The percentages describe only
this frozen corpus, not perceptual quality, antialiasing performance or a
universal 7.345% error guarantee. No filtering-quality improvement was tested.

## Answer to the owner question and stop boundary

What did the triangular lattice itself provide that the exact square version
did not? A natural integer-indexed, integer-coefficient sample representation
for this particular IVM-aligned view, and samples at genuinely triangular sites.
Those are representation properties. It supplied no demonstrated unique
visibility capability, sample-time arithmetic advantage after the square
counter-baseline, sample/storage saving or conventional-display quality benefit.

Exact edge predicates, division-free rational visibility and epoch-safe prepared
scenes worked in both formulations and must not be marketed as IVM-specific.
The square output objective favours direct square sampling in this experiment;
native-first incurs the explicitly measured reconstruction loss. This does not
falsify a native representation for a native consumer, but no such application
advantage was demonstrated here.

Next boundary is OWNER REVIEW, not production RTL or Rung 5. A subsequent
decision can accept this bounded contract, change adapter quality requirements,
or shelve the proposed implementation. No infrastructure cleanup, larger FPGA
or PCB decision follows from these results.
