# Soul-0 frozen replay

Run the software-only, sample-by-sample Soul-0 demonstration from the
repository root:

```bash
python3 examples/06_soul0_replay/replay.py
```

The replay checks the frozen fixture and source hashes, then prints each
sensor sample, alert decision for the stateless, rolling-mean, and Soul-0
models, and Soul-0's learned profile centers. It saves Soul-0 after regime C,
continues the same stream through the original and restored instances, and
reports whether their final checkpoints match.

The report also shows the retained regression: a profile seeded at
`(180, count=2)` ends at center 193 after 16 healthy samples from regime B.
Quiet decisions do not establish accurate adaptation. The demonstration covers
only the frozen synthetic sequence and deliberately out-of-range transients;
faults that resemble another normal regime remain untested. It is a research
simulator example, not an integration into the ISA-A reference VM or hardware.

To inspect the integer-mean stall one sample at a time, run:

```bash
python3 examples/06_soul0_replay/trace_stall.py --out build/research/soul0/stall_trace_01
```

This writes a separate diagnostic `trace.json`; it does not change the frozen
experiment result or its source manifest. Each row includes the stored
prototype before the update, selected regime, residual, threshold decision,
integer mean numerator and denominator, resulting center/count, and rolling
mean prediction.
