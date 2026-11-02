# H0-RTL-1F-R2: reset and retirement barrier

**Disposition: REVISE.** Source inspection establishes the conditional reset
invariant below, but R1 does not expose controlled initialization during an
owned execution, and its current test suite does not establish the complete
requested wrapper-to-core barrier. No R1 or frozen RTL was changed. Baseline
`e90bef1`.

## Enabled retirement path and sampled reset

For R1's selected core parameters (`ENABLE_SURD_CPU=1`, sequencer, math,
lattice, RPLU, SOM, REGEN, IROTC and torus disabled), the frontend reads
`surd_retire_valid` directly from `spu13_surd_exec`, not generic `inst_done`.
`cpu_program_probe.v` drives core `.rst_n(cpu_rst_n)` and suppresses `valid`
outside ISSUE. Its IDLE and INIT assert core reset; INIT advances only after two
sampled rising `clk` edges, then RELEASE and WAIT_BOOT precede issue. Physical
reset asynchronously clears wrapper state and also asserts `cpu_rst_n`.

On a rising core clock with `rst_n=0`, the following connected sequential
retirement-producing state is reset synchronously (`rst=!rst_n`):

* `spu13_surd_exec`: busy, retire/read/write valid, status, held destination and
  read data. Its retire pulse arises only from an accepted operation or from
  `arith_done && busy`.
* `spu13_surd_arith`: state IDLE, `done=0`, held operation, operands and raw
  values reset. `normalization_start` is combinational from the reset state.
* `surd_normalize_unit`: IDLE, busy/done/valid/fault and its registered
  `gcd_start`/`quotient_start` reset, along with held operands and outputs.
* `surd_binary_gcd3` and all three `surd_exact_quotient` instances: IDLE,
  busy/done/fault, counters, operands and result registers reset. The product
  datapath is combinational and has no pending state.
* `spu13_surd_load` staging/received state and `spu13_surd_bank` initialized
  flags/tuples reset; `bank_we` is disabled during reset. These affect the
  next instruction's state even though they do not emit retirement themselves.

Core `boot_state` and `inst_seen` also reset asynchronously with `rst_n`. The
core's generic `inst_done_r` separately mirrors surd retirement but is not the
frontend's retirement input. Tied configuration and timing inputs and disabled
feature parameters are assumptions of this specific profile, not a general
claim about other profiles or autonomous paths.

## Conditional source invariant

Assume a known asserted core reset is sampled on a rising edge by every listed
producer, all share this clock, the frozen RTL behaves as written, no external
force or alternate source drives the retirement net, and no new issue is
accepted. After the reset edge's nonblocking updates, executor and downstream
state are idle, `retire_valid`, arithmetic/normalizer/GCD/quotient `done` and
their registered start pulses are zero. With reset released and no new issue,
the executor cannot generate a retirement: its acceptance is false and its
`arith_done && busy` path is false. Downstream IDLE machines have no start and
cannot spontaneously generate done. By induction over later clock edges, no
pre-reset operation can generate a retirement in this closed hierarchy before
a new accepted issue. The two INIT samples in R1 supply more than the one
sample needed by these synchronous reset branches under the stated ideal
clock/reset assumptions; simulation does not prove physical reset distribution,
CDC, clock integrity or post-synthesis behavior.

After a new issue, that induction depends on causal ownership of every later
`done`/retirement and on no other source injecting an event. An untagged event
with valid metadata in WAIT_RETIRE is observationally indistinguishable at the
frontend. The R1 wrapper does not provide an initialization request during
owned execution: controlled INIT starts only with an accepted START in IDLE;
raw reset can interrupt but invalidates the bank. The separate H0-RTL-1E probe
does have an interrupting internal init request but is not the R1 wrapper.
The source invariant therefore does not by itself verify the requested R1
controlled-interruption integration.

## Focused evidence

`build/h0-rtl-1f-r2/focused-01/bank_ab.log`: R1 bank-fed A/B run passed all six
result checks. `stale_wait.log`: during PC 7 WAIT_RETIRE with the real core
still busy, forcing retire/status/read/write metadata to a valid-looking
successful SMUL makes the frontend enter REARM without fault at 776000 ps.
The event is deliberately injected; it is **not evidence the frozen core can
produce that event**. Under the closed, correctly reset hierarchy and no-force
assumptions above, an old event should not arise, but the frontend cannot
distinguish one if the assumption is violated.

`build/h0-rtl-1f-r2/reset-1e-01/` reruns the earlier separate controlled-reset
probe: interruption of product, GCD and quotient activity, reset-edge coverage,
bank-retention probe, two subsequent six-slice runs and named reset/stale
completion mutants passed. Normalization was reached via the GCD/quotient
path. This is bounded simulation of a different wrapper, not proof that R1's
controlled-init path was exercised or that all arithmetic phases were covered.

Reproduction from the worktree root:

```bash
iverilog -g2012 -s cpu_check -o build/h0-rtl-1f-r2/focused-01/test.vvp -f research/h0_rtl_1f_r2/sources.f
vvp build/h0-rtl-1f-r2/focused-01/test.vvp
vvp build/h0-rtl-1f-r2/focused-01/test.vvp +stale_wait
python3 research/h0_rtl_1e/run.py --output build/h0-rtl-1f-r2/<new-run>
```

## Exact remaining guarantee

Before PASS, define whether an owned run may be internally interrupted and
implement/review that control in the actual wrapper, or explicitly constrain
initialization to idle and use independently verified physical-reset recovery.
Demonstrate that the actual wrapper supplies the reset samples and issue gate to
the complete frozen producer hierarchy for that policy; test reset/start/
retire coincidences and relevant arithmetic phases, and independently review
the no-alternate-producer/closed-hierarchy assumptions and the conditional
invariant. The experiment does not prove reset distribution or arbitrary
events. If those assumptions cannot be guaranteed, a reviewed interface that
distinguishes retirement ownership is required; no transaction tag or frozen
core modification is introduced here.

Source SHA-256: R1 wrapper
`d9760167bfb783f1b2fbef20ef08f08f34a3ff7ce8a16d04543804a35dc567f7`;
R2 testbench `3e9f3214455bab929fbb9b5717c980ffb6d794e1e3b34ca0412d4389e1ccf179`;
R2 filelist `f44e081368bca823bed6bb458cfac3a2ee7880639a00029bcf90dac13cc8be41`.
