# SOM v1 Bring-Up Plan

Date: 2026-07-16

The authoritative behavior and exit criteria are in
[`SOM_V1_PRODUCT_CONTRACT.md`](SOM_V1_PRODUCT_CONTRACT.md). The superseded
2026-06-30 parallel-array plan is retained at
`docs/archive/legacy/som_bringup_plan_2026-06-30.md` for history only.

## Tranche 1 — truth gate (complete)

- Make the serial BRAM-backed `spu_som_bmu` path canonical.
- Remove archived parallel-array modules and tests from active builds/gates.
- Prove exact `Q(sqrt(3))` ordering with an adversarial RTL vector.
- Pin classification to a data-independent cycle count.
- Repair standalone sidecar result readback and pin it in simulation.
- Run the focused RTL, Python oracle, VM/RTL trace, training, and host-build
  regressions.

Exit: achieved 2026-07-16. `TB_FILTER=som` has no compile errors, exact
ordering passes, seven-node latency is pinned at 434 clocks, and the repaired
sidecar is silicon-proven over RP2350 SPI.

## Tranche 2 — versioned evidence frame

- Define `SOM1` binary framing with an explicit version and payload length.
- Include winner, runner-up, cluster label, `best_q`, `second_q`, confidence
  gap, ambiguity, map generation, and error/status bits.
- Add RTL encoder, host parser, golden byte-stream test, and malformed-frame
  tests while preserving the current compact UART byte for compatibility.

Exit: simulation can hydrate a map, classify a corpus, and compare every result
field against `rational_som.py` through the real SPI/UART boundary.

## Tranche 3 — reproducible map and one-command demo (complete)

- Check in a small training corpus and deterministic offline trainer settings.
- Quantize and range-check four-feature prototypes into 18-bit surd pairs.
- Make `upload_som_weights.py` reject malformed, incomplete, or out-of-range
  maps and verify the expected 28 writes.
- Add a host command that uploads, classifies a golden corpus, and prints a
  concise pass/fail/confusion summary.

Exit: a fresh checkout can regenerate the same map and produce the same result
frames without hand-entered console commands.

Achieved 2026-07-17 with `software/models/iris_som_v1.json` and:

```
python3 tools/iris_som_demo.py --hardware
```

The command regenerated and checksum-validated the seven-node map, issued all
28 writes, and obtained 150/150 exact FPGA/oracle winner matches. The node-label
confusion matrix was `[[50,0,0],[0,48,2],[0,1,49]]`, or 147/150 (98.0%).

## Tranche 4 — silicon and cross-vendor closure (Tang complete)

- Build and run the repaired standalone Tang sidecar.
- Repeat the exact-order adversarial corpus in silicon.
- Run the identical corpus on the Artix-7 SOM probe.
- Record commands, tool versions, utilization, timing, UART/SPI captures, and
  bitstream hashes in `docs/hardware_evidence.md`.

Exit: Tang and Artix-7 results are bit-identical to the software oracle.

Tang status: complete for the 150-sample Iris corpus. The corpus found and
closed a real feature-weight packing mismatch, now pinned by RTL regression.
Artix-7 corpus replay remains open.

## Tranche 5 — observation ABI integration

After SOM v1 closes, define a versioned observation record that robotics and
the proprioceptive layer can populate. Keep feature extraction, normalization,
classification, and actuation as separate components. The first integration is
read-only classification telemetry; closed-loop actuation requires its own
safety and rollback contract.
