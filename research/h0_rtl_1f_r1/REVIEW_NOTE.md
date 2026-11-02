# H0-RTL-1F-R1 — retirement ownership repair

**Disposition: REVISE for integrated safety.** This is an isolated experimental
repair of one acceptance-edge defect; it does not establish universal exclusion
of stale untagged retirements. Original H0-RTL-1F sources and
`COUNTEREXAMPLE.md` remain unchanged.

The frozen generic frontend `cpu_fetch_1b` accepts a retirement in ISSUE on the
same edge as ready/acceptance. The specific connected `spu13_surd_exec` instead
registers `retire_valid` with a nonblocking assignment on or after the edge on
which it accepts `start`. Its new transaction's retirement cannot be present
before that same acceptance edge. This conclusion applies to the selected
single-clock surd endpoint, not the generic frontend interface or other cores.

R1 rejects a high retirement in ISSUE, faults without consuming it, and gates
core `inst_valid` while that retirement is high. A newly accepted instruction
enters WAIT_RETIRE; only a later matching-status retirement is consumed. A
duplicate in REARM and an event in WAIT_BOOT/FETCH/FETCH_WAIT fault. The tests
check first-PC stability, no result, and no core accept for the injected
acceptance-edge or preaccept events. WAIT_RETIRE still has an untagged input:
an old event there is indistinguishable from a legitimate retirement. Merely
waiting a cycle does not prove the event is fresh. Before integrated safety can
be claimed, prove that controlled reset flushes every prior retirement producer
before new issue and that only the owned instruction can retire thereafter, or
review an interface that can distinguish the events. A quiet window is not that
proof.

## Reproduction and results

Baseline reproduction, saved under `build/h0-rtl-1f-r1/baseline-01/`:

```bash
iverilog -g2012 -s cpu_check -o build/h0-rtl-1f-r1/baseline-01/original.vvp -f research/h0_rtl_1f/sources.f
vvp build/h0-rtl-1f-r1/baseline-01/original.vvp +stale_issue
```

The baseline exited 1 at the original PC 0 assertion. R1 focused run:

```bash
iverilog -g2012 -s cpu_check -o build/h0-rtl-1f-r1/focused-01/test.vvp -f research/h0_rtl_1f_r1/sources.f
vvp build/h0-rtl-1f-r1/focused-01/test.vvp
vvp build/h0-rtl-1f-r1/focused-01/test.vvp +stale_issue
vvp build/h0-rtl-1f-r1/focused-01/test.vvp +before_accept
vvp build/h0-rtl-1f-r1/focused-01/test.vvp +duplicate
```

All four R1 invocations exited 0. The normal case executes both bank-fed
programs and checks all six slices (A: `13,0,4,0,9,0`; B: `7,0,4,0,4,0`),
and injects an old retirement during WAIT_BOOT after a physical reset. The
other invocations check acceptance-edge stale retirement, retirement with
ready forced low, and duplicate retirement in REARM. Logs are preserved as
`case-0.log` through `case-3.log`. No valid same-edge retirement is supported
by the particular registered surd interface; ordinary registered completions
are exercised by both programs. No hardware, full regression or synthesis ran.

## Source SHA-256

```text
d9760167bfb783f1b2fbef20ef08f08f34a3ff7ce8a16d04543804a35dc567f7  research/h0_rtl_1f_r1/cpu_program_probe.v
c587541680f6dbecea129684b06c0a2fbcb24699a6d68e67d46b8364478640d0  research/h0_rtl_1f_r1/cpu_check.v
1796522822d92fd442ff9d02a2351313fbb4e221c191075d810a4caa93af7f46  research/h0_rtl_1f_r1/sources.f
e211220cd99fd8849cc46ca4560cd8ed84c721f35c6a83de7e1b5e82b59e7c5f  research/h0_rtl_1f/program_banks_v2.v
d1f1cb408ba59f02b3faf8256d491b54b4661faeb5c536cdf658be34fe9b7780  hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_fetch_1b.v
2ff5c0ec8b8eefe8fab96ac5ac2a899ee90398b969b7c5c803e01d59581166fe  hardware/rtl/core/spu13/spu13_surd_exec.v
```
