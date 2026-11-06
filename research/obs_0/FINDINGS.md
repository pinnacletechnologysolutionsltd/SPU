# SPU-OBS-0 — Gen-1 Surd observation boundary

**REVISE — interface behavior identified; complete architectural equivalence
boundary unresolved.** Inspection and focused simulation identify several
distinguishable behaviors of the enabled Gen-1 Surd dispatch path. The evidence
does not define a universal software-visible architecture or establish that
every exposed core handshake is an architectural trace event. In particular,
F7's two-instruction-to-no-op replacement is not qualified generally.

## Findings by observation surface

| Surface | Established behavior and scope |
|---|---|
| Tuple state | The enabled Surd bank holds eight 192-bit tuples. Subsequent `SRD` instructions can read six 32-bit slices of an initialized tuple. A later instruction may use the intermediate tuple, so changing it can change a program result. |
| Initialization validity | The bank resets its eight initialized bits low; successful writes set the selected bit. An uninitialized `SRD` or arithmetic source returns status 1. Validity is observable through subsequent instruction success/refusal; the raw bit vector is not a documented software register here. |
| Status and refusal | The dispatch path returns a four-bit status with retirement; `SSTAT` reads the prior status. The selected overflow case returns status 2 without a destination write. Refusal location and resulting state matter when the issuing environment can observe them. |
| Retirement and write events | The frozen core exposes `surd_retire_valid`, `surd_write_valid`, status and destination on its dispatch interface. The frozen frontend consumes retirement, read/write validity and status to advance or fault. This establishes an implemented interface dependency, not a general requirement to preserve a performance-counter or trace event under every future software equivalence relation. |
| Debug/testbench observations | Hierarchical access to the bank in a testbench is verification instrumentation. It demonstrates internal state but does not by itself make the entire hierarchy architecturally accessible. |
| External frontend | The frozen ROM frontend admits only its fixed 14-instruction load/square/read profile, not arbitrary F7 programs. Its result, result-valid, halt and fault outputs are exposed by that frontend. The experimental H0 controller likewise checks per-instruction status and read/write/retirement handshakes for its restricted profile. These implementations do not establish a generalized optimizer contract. |
| Counters, interrupts, timing and external interactions | No complete applicable contract for performance counters, interruptibility, timing equivalence or external interactions was established in this review. Absence of such a contract in the inspected slice is not proof that these observations are forbidden elsewhere. They must be explicitly included, excluded or resolved before a substitution claim. |
| Eager Coherency metadata | UNKNOWN / NOT ESTABLISHED IN THE ENABLED GEN-1 SURD PATH. Software Pell metadata is not evidence of a hardware field. |

Sources: [Surd bank](../../hardware/rtl/core/spu13/spu13_surd_bank.v),
[dispatch](../../hardware/rtl/core/spu13/spu13_surd_exec.v), [frozen
core](../../hardware/boards/artix7/wukong_v3/cpu_v02/rtl/spu13_core.v),
[frozen frontend](../../hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_fetch_1b.v),
and [experimental H0 controller](../h0_phys_1a/h0_cpu_controller.v). The
older [oracle review](../../docs/SURD_CPU_ORACLE_REVIEW_2026-10-07.md) cites a
build-resident approved annex; that annex was absent in this checkout and could
not be inspected. Do not infer missing contract terms from this review.

## Focused evidence

The [MATHSTATE-0](../mathstate_0/FINDINGS.md) 320-instruction dispatch test was
reproduced before preservation. OBS-0 adds an intervening read to F7:
starting S0=(3,−2,1), multiplication by 2+√3 yields (0,−1,1), which `SRD`
reads; multiplication by 2−√3 returns (3,−2,1). An uninitialized S7 read
then produces status 1 and `SSTAT` reads it. The established core testbench
checks every retirement, status, tuple write, bank validity and preservation.
The focused RTL simulation passed and counted two failed-retirement bank
preservation checks. An intermediate read is a distinguishable legal dispatch
sequence; it is not part of the two-instruction F7 sequence itself, nor is it
admitted by the frozen fixed ROM frontend.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.obs_0.observability_test)
```

Observed with Python 3.10.12 and Icarus 11.0: `OBS0 PASS` and
`VERIFICATION preservation=2 aliases=0 injections=0`. The script uses the
unchanged frozen core and existing testbench, with temporary outputs. This is
a focused dispatch simulation, not full ISA conformance, a timing experiment,
a physical result, or formal proof.

## F7 interpretation

The previously tested eager and no-op cases agree on one final tuple, validity
and status, under MATHSTATE-0's initialization assumptions. They do not emit
the same number of dispatch write/retirement events. A consumer that depends
on those events, or reads the intermediate value, can distinguish them. A
final-state-only relation that excludes such observations could still consider
them equivalent, but no applicable complete architectural contract was found
that authorizes that exclusion. Timing, interrupts and interaction with
external state remain open rather than silently ignored. No hardware or ISA
change follows from this inspection.
