# Exact Lorentz composition and mission-model counterexample

Read `results.json`, `oracle.json`, `runtime.log`, `negative_control.log`, `compiled_sources.json` and `source_hashes.json` in this directory. This is focused dispatch-port RTL simulation on the existing frozen decoder CPU source, using its ENABLE_SURD_CPU path. It does not add Surd execution to either software VM.

Reproduce in a new evidence directory, preserving this run:

```bash
mkdir build/spu_surd_register/lorentz_model_experiment_20261011/reproduction_01
cp build/spu_surd_register/lorentz_model_experiment_20261011/attempt_01/run.py build/spu_surd_register/lorentz_model_experiment_20261011/reproduction_01/run.py
timeout 55s python3 build/spu_surd_register/lorentz_model_experiment_20261011/reproduction_01/run.py
```

The experiment uses c=1, one spatial dimension and the boost L=[[2,-sqrt(3)],[-sqrt(3),2]]. Its nth composition has coefficients a,b with a²−3b²=1. Independent integer matrix recurrences a'=2a+3b and b'=a+2b are checked against ten literal coefficient rows. The instruction stream then executes multiplication, addition, subtraction, normalization and tuple readback on the actual CPU dispatcher. The existing harness checks atomic tuples, status, destination preservation and exactly one retirement per instruction.

For a final constant-velocity cruise with one unit of proper time, the transformed event has t=a and x=−b sqrt(3). The RTL computes t²−x² exactly. Acceleration/prelude duration is excluded; this is not a full mission trajectory or arrival-date calculation.

| Boosts | a = gamma | b | Exact interval | Mistaken gamma rule 2^n |
|---|---:|---:|---:|---:|
| 1 | 2 | 1 | 1 | 2 |
| 2 | 7 | 4 | 1 | 4 |
| 3 | 26 | 15 | 1 | 8 |
| 10 | 262087 | 151316 | 1 | 1024 |

All ten exact boost/conjugate products and transformed-event intervals equal one. Nine of ten deliberately incorrect arrival-model predictions disagree with the oracle. The ten-boost discrepancy ratio is exactly 262087/1024. These disagreements are expected experimental findings, not arithmetic qualification failures. The wrong rule belongs only to the mission interpretation; it does not alter the valid boost matrix executed by the machine.

The experiment records 853 RTL instruction retirements. Repeated aliased multiplication succeeds through composition 33; composition 34 exceeds signed-64 coefficient representability, reports overflow status 2 and preserves the destination. SSTAT and tuple readback are exercised following the fault. This does not establish unbounded arithmetic parity.

A deliberately malformed boost (2,2) has invariant −8, although its arithmetic operations succeed. Thus the application must check the physical invariant; the arithmetic engine correctly supports values that are not Lorentz boosts. Separately, flipping a bit in an expected multiplication result makes the RTL harness exit nonzero with an atomic-tuple mismatch, demonstrating a falsifiable checker.

No RTL or shared test infrastructure was changed. No full repository qualification, full physical model, integrated timing, silicon, energy or performance result is claimed. The generated clock is a simulation clock. The frozen RTL sources and stream/model inputs are hashed; a setup include-path error was corrected before the successful run by including the snapshot's header-only arch directory. The original FPGA campaigns and their source snapshots are untouched.
