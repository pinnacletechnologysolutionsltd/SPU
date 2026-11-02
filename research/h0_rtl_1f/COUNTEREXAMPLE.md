# H0-RTL-1F: stopped at retirement boundary

**REVISE.** The experimental integration is not safe to use as an owned-run
frontend. The prior H0-RTL-1 and H0-RTL-1E files and evidence remain unchanged.
No frozen or production RTL was edited.

## Counterexample

`cpu_program_probe.v` ISSUE state calls `accept_retirement()` when `ready` and
`retire` are high on the same edge. This matches a same-edge path in the old
frontend, but the experimental integration has not proved that an untagged
retirement at that edge belongs to the newly issued instruction. A forced
retirement with successful SLI metadata at PC 0 is accepted rather than
faulted. This is a **fault-injection counterexample in the new wrapper**, not
an observation that the frozen core actually generated a late retirement.

Reproduce from the worktree root:

```bash
iverilog -g2012 -s cpu_check -o /tmp/h0-rtl-1f-stale.vvp -f research/h0_rtl_1f/sources.f
vvp /tmp/h0-rtl-1f-stale.vvp +stale_issue
```

Observed exit 1 at simulation time 416000 ps:

```text
FAIL tirement at first issue rejected pc=0
FATAL: research/h0_rtl_1f/cpu_check.v:11:
```

The displayed assertion text is truncated by the testbench's fixed-width
message argument. Its full intended name is `stale retirement at first issue
rejected`. The test waits for the first issue with ready asserted, forces the
untagged retirement and success metadata high, and expects fault with no
completion. The current wrapper instead follows the same-edge retirement path.

## Scope and earlier observation

Before the counterexample was added, an exploratory normal run printed
`H0_RTL_1F EXPERIMENTAL PASS`: it loaded A and B, checked their six results,
rejected a bad replacement CRC, and exercised selected physical resets. That
run does not close the task or establish stale-event exclusion. The newly added
fault injection was not present in that earlier version of the testbench.
Required comprehensive negative controls, stopped-clock/reset coincidences,
and independent review remain outstanding; no successful integrated verdict is
claimed. The derived bank uses CRC-32 over stored words as an accidental-error
check, not collision-resistant identity or authentication.

The sampled files at the counterexample were:

```text
e211220cd99fd8849cc46ca4560cd8ed84c721f35c6a83de7e1b5e82b59e7c5f  program_banks_v2.v
c293dd3042f766fc2349e9e2f02d0214cd7968c2a0e6c85d676eab95a461ef23  cpu_program_probe.v
235179303905735f0de0b3195575058921d66b2be230ace0b1e93fbd976069db  cpu_check.v
976a1de137e6b1fba87d8bb4e8e23f9af51df69ea1ddfb8e57e63971148d0203  sources.f
```

The smallest next review must decide how the real registered-retirement timing
and reset/flush guarantee exclude a stale event before permitting same-edge
acceptance, or define an independently verified interface change. A quiet
window alone cannot establish this. No such design change is made here.
