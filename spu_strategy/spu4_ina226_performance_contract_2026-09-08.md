# SPU-4 / RP2350 performance-only replay

Status: ACTIVE; owner authorised deterministic model reconstruction.

Owner subsequently authorised a bench-only 25 MHz divider/UART profile after
the unchanged 50 MHz build failed timing. Preserve that negative result.
Validate both original and new actual consumers, without changing expected
classification responses:

```bash
bash tools/test_spu4_bench25.sh
bash tools/build_spu4_bench25.sh
```

Require final routed pass with explicit 50 MHz source / 25 MHz generated clock
constraints. Treat Pico GPIO-free SRAM timing as preflight only; do not drive
UART/flash GPIO without resolving the documented GP4/GP5 function overlap.

1. Verify archived input hashes:

```bash
(cd docs/bench_captures/2026-09-03-ina226-som && sha256sum -c SHA256SUMS)
```

2. Reconstruct with the unchanged historical pipeline into a NEW output path:

```bash
python3 tools/freeze_spu4_ina226_benchmark.py --output build/spu4_ina226_benchmark/reconstruction_check.json
cmp docs/bench_captures/2026-09-08_spu4_ina226_freeze.json build/spu4_ina226_benchmark/reconstruction_check.json
```

Require original result SHA256
`3a801cd9f54ef36328cb9f07fc0e2ffa676eccd859e8f7012ad3f5fb0ea53bc1`.
Preserve failed promotion gates; label weights reconstructed, not historically
byte-verified. Do not tune trainer, folds, preprocessing, labels or thresholds.

3. Validate optimized Q=0 C baseline:

```bash
UBSAN_OPTIONS=halt_on_error=1 python3 software/tests/test_spu4_ina226_kernel.py
```

Require exact features, scaling, winner, distance and labels on all 120 windows.
Require negative/half-even input controls, unsigned 3.6e9 distance and tie control.
Use four nodes and four features on both paths. Keep session plurality with
lowest class ID tie. Do not substitute the seven-node SOM1 metric.

4. Check the unchanged actual Tang consumer at the documented source frequency:

```bash
bash tools/check_spu4_benchmark_timing.sh
```

Halt on failed timing; do not use timing-allow-fail or redesign the classifier.
Verify physical frequency separately before accepting timing measurements.
Confirm flash J4 and safe UART pin ownership before driving signals. Never
connect two TX drivers to B3. Preserve Pico firmware/files before replacement.

5. Measure only after hardware preflight passes. Preserve raw timing records
for preprocessing, classifier, transport and last-sample-to-label separately.
Use 1/4/16/64 streams, aligned/staggered windows and bounded queues. Count drops,
deadline misses and traffic; retain curves independent of the experimental
10 ms deadline. Report CPU/state/stack and implementation settings. Never use
host C or Python runtimes as RP2350/FPGA performance measurements.

6. Keep the full repository gates in AGENTS.md as implementation-completion
gates. A halted preflight is not a completed benchmark or a green regression.
Do not claim architecture/product advantage from kernel-only measurements.

## Owner-approved measurement amendment — 2026-09-09

This amendment changes measurement variables only. Classifier mathematics,
weights, preprocessing, voting, UART semantics, application-quality evidence
and the comparative premise remain frozen.

Performance requires verified fold-0 flash identity, hydration, 24/24 fold-0
node/distance parity and zero invalid responses. Fold 0 is sufficient for
performance; folds 1–4 remain separate application evidence. Halt on any
performance-run parity failure.

The RP2350 runs the frozen integer classifier locally. Tang uses only the
implemented BL616 USB-CDC/UART path at 115200 8N1; characterize it as this
integration, never as direct-sensor/direct-GPIO transport.

Queue depth is exactly one: issue only after the preceding response completes.
No batching, speculative issue or added queue. Test N = 1, 4, 16, 64 streams
with aligned release at the same nominal boundary and staggered release
`t_i = i*(10 ms/N)`. Use the same schedule on both systems. For each
system/N/schedule/repetition, discard 100 classifications, measure 10,000, and
run exactly three repetitions. Report repetitions and aggregate median; never
shorten a run after observation.

RP2350 classifier latency is existing-cycle-counter kernel entry through
node/distance availability. FPGA classifier latency requires a trustworthy
internal start-to-corresponding-completion measurement; do not use `L=` until
the stale level-held-`done` defect is corrected and reverified. Tang integration
latency is host release of the final complete-query byte through host receipt of
the final corresponding valid-response byte. Report median, p99, maximum and
jitter (`p99 - median`). Interactive spot RTTs are not substitutes.

The deadline is 10 ms (100 Hz). A stream is safe only when each classification
completes before its next boundary. Report completions, drops, invalids, misses
and sustained classifications/s. Capacity is the largest tested N with zero of
all three failures; report `>=64` rather than extrapolating if 64 passes.

RP2350 CPU occupation is classifier cycles consumed per 10 ms divided by
available RP2350 cycles per 10 ms. Tang RP2350 classifier occupation is zero;
report host orchestration separately without claiming general host CPU usage.

Classification gates:

- **A:** exact parity plus either >=2x deadline-safe stream capacity or >=20
  percentage-point lower RP2350 classifier occupation at the same passing
  workload, without material compensating integration failure.
- **B:** exact parity and a meaningful property, but neither A nor fair
  equivalence/inferiority follows.
- **C:** exact parity, the same workload envelope, and principal measurements
  within approximately +/-10%, or no material resource advantage.
- **D:** Tang misses workloads/deadlines RP2350 satisfies, materially
  underperforms, or compensating integration cost defeats offload.
- **E:** a functional gate, trustworthy measurement path or frozen variable
  remains unresolved.

Stop immediately on parity failure, unexplained invalid response, untrustworthy
latency instrumentation, need to change frozen semantics/contract, or discovery
of another outcome-sensitive undefined variable. No second workaround without
owner authorization.
