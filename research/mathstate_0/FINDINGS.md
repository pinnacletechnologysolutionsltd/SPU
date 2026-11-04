# MATHSTATE-0 findings

**REVISE — useful partial evidence; architectural substitution is not
qualified.** Exact fusion can change first-refusal behavior. A narrow
final-state-only cancellation condition was investigated, but the enabled
dispatch interface exposes retirement/write events, and this experiment does
not establish that an arbitrary observer cannot see the removed instructions.
The implemented CERTIFIED mode is a conditional predicate, not an independent
certificate verifier or an authorized compiler transformation.

## Reference and RTL evidence

The selected core is `hardware/boards/artix7/wukong_v3/cpu_v02/rtl/spu13_core.v`
with `ENABLE_SURD_CPU=1`. The reference stream is
`software/experiments/surd_cpu_stream.py`, which independently computes tuple
expectations using integer arithmetic and `Fraction`. The existing
`hardware/tests/spu13/spu13_core_surd_tb.v` and guards compare status,
retirement, reads, atomic writes, initialization-valid bits and the entire
bank after each issued instruction. F1–F5 and F7 used denominator-one inputs;
the mathematical model does **not** implement general Gen-1 tuple/refusal
semantics. See [SPECIFICATION.md](SPECIFICATION.md) for the actual subset and
source boundaries.

With Icarus 11.0, the focused differential trace passed **320 instructions**;
the guard counted eight non-success preservation checks. The trace covers
F1–F5 and both eager and no-op forms of F7, plus invalid-register reads.
It checks the eager stream against the reference, not an independent RTL
implementation of matrix fusion or symbolic exponents. Six 32-bit read slices
check final tuples. F5 retains the earlier tuple in S5 before overwriting S0,
then materializes from S5; this costs one additional 192-bit bank tuple and
its initialization-valid bit. It is a concrete retention strategy, not a
proof for arbitrary aliasing or register allocation.

The actual Surd bank has initialization-valid bits and a four-bit status.
Its register reads and status reads are explicit instructions; an intervening
read can observe an intermediate value. The core also exposes write-valid and
retirement signals. A trace signal alone would not prove architectural
observability, but these are actual core interface outputs. The restricted
frozen demonstration frontend is not a general execution interface, so the
system-level observer boundary beyond the dispatch port remains unresolved.
**EAGER_COHERENCY_METADATA = UNKNOWN / NOT ESTABLISHED IN GEN-1.** The
software-only Pell metadata is not attributed to this RTL. F6 therefore
characterizes validity, status and write events, not a non-unit coherency bit.

## Fixtures and cost observations

The following are mathematical-model counts, separated from RTL cycle costs;
the program prints the full per-mode values. Width means signed coefficient
or matrix-entry width, not every product, accumulator, denominator or scratch
width. A resident tuple is 192 bits excluding its validity bit. The 2×2
matrix representation and exponent sizes omit Python object overhead. No
runtime, power, hardware area or speedup is claimed.

| Fixture | Eager tuple operations / successful writes | Eager peak coefficient bits | Fused matrix entry bits; compositions | Generator exponent; power bits | Result and refusal |
|---|---:|---:|---:|---:|---|
| F1: u,u from (1,0) | 2 / 2 | 4 | 5; 2 | 2; 5 | Exact (7,4), no refusal. |
| F2: u³⁴ from u⁻¹⁷ | 34 / 34 | 33 | 66; 34 | 34; 66 | Final fits; expanded positive generator matrix needs 66 signed bits. |
| F3: u,u⁻¹ from (2⁶³−1,0) | 1 / 0 | 65 | 2; 2 | 0; 2 | Eager refuses at 1 with status 2 and unchanged valid destination; fused final fits. |
| F4: u,−I | 2 / 2 | 5 | 3; 2 | unsupported | Exact (−13,−8); negative sign is outside the uⁿ-only family. |
| F7: u,u⁻¹ from (3,−2) | 2 / 2 | 3 | 2; 2 | 0; 2 | Final tuple, validity and status match a no-op under the stated boundary. |

Fused evaluation performs one final numerical application and one numerical
materialization in each example; constructing its matrix takes the listed
number of matrix compositions. Generator evaluation retains an exponent
(signed widths for these fixtures: 3, 7, 1 and 1 bits), then the sample
implementation computes a power by |n| matrix compositions before one
application and one materialization. A symbolic exponent can instead remain
unmaterialized; that avoids those steps only until a numeric value is required.
Retaining the original tuple is also required, so the exponent is not the
whole retained-state cost. The report does not measure intermediate product
widths or full matrix storage cost. Fused and generator first-refusal/state
agreement with eager is **not established**, and F3 directly disproves it.

For F7, the candidate predicate accepts the cancellation only for |a|,|b|
≤16, initialized destination, prior status zero and an assumed boundary with
no observation of intermediate states or omitted write/retirement events.
It returns UNKNOWN for the other four synthetic fixtures and for any requested
intermediate read: 1/5 is only this selected sample, not general prevalence.
The two RTL traces establish matching final tuple/validity/status for the one
fixture, while the write-event sequences differ. External event blindness is
an assumption, not established hardware behavior. The predicate is therefore
not evidence of safe substitution under the general Gen-1 interface.

## Formal record

Z3 4.15.5 checks [verification.smt2](verification.smt2), QF_LIA. Under
−16≤a,b≤16, it proves no counterexample to |2a+3b|≤80, |a+2b|≤48 and
inverse reconstruction; the intentionally wrong inverse is SAT. A second
abstract final-state formula is UNSAT and an intermediate-value observer is
SAT. Outcomes: `unsat, sat, unsat, sat`. These integer formulas establish
the encoded bounds and algebra, not the Python model, status transition RTL,
the RTL observation boundary or a general finite-width proof. The width
bounds are far inside signed 64 bits, but all actual instruction effects and
resource intermediates are not independently solver-verified.

## Reproduction

Python 3.10.12, Icarus Verilog 11.0 and Z3 4.15.5. HEAD observed after the
run: `677ba14`. The shared checkout contains unrelated pre-existing changes.
Key source SHA-256 values (other transitive RTL dependencies are not individually
recorded here, so this is not a complete source manifest):

```text
frozen spu13_core.v       e5701e5e0f267531726268fe2f52e7b1dede5eac04d3e532aecfd585828fcc3b
spu13_surd_exec.v         2ff5c0ec8b8eefe8fab96ac5ac2a899ee90398b969b7c5c803e01d59581166fe
spu13_surd_bank.v         8e3a2f0afdc7f14289b83feaf73151f244afc21f01e2a3d91447c833afa8657c
spu13_surd_arith.v        1b82e9d0b48d90aaa10e938254a554c3db3345d8ef62156cef7acb3f0f832ba8
surd_cpu_stream.py        bc67034e75f2e524b2506445485cccaebbc2252fed52efca64ed407642c9eaec
spu13_core_surd_tb.v      f407e254f26b2fa1f5c0e6ad1e5cef783438fa75394b5d2885fdc9d3c0286704
```

No random seed. Each
command has a 30-second external timeout and 1-GiB per-process virtual memory
limit. The RTL script uses a temporary directory and deletes its outputs;
the testbench prints its PASS and preservation count. No Vivado or physical
hardware is used.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.mathstate_0.test_experiment -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.mathstate_0.experiment)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/mathstate_0/verification.smt2)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.mathstate_0.rtl_diff)
```

## Architectural implications

The exponent and immutable source identity can remain symbolic until numerical
use, provided source lifetime is retained. F2 demonstrates that eagerly
materializing the generator itself may need a wider representation than the
eager data path. F3 demonstrates that final exact equality does not preserve
refusal. F7 demonstrates a possible final-state-only cancellation, but exposed
intermediate writes and retirement prevent claiming unrestricted substitution.
The non-cyclic F4 needs general fusion rather than a u-only exponent.
Compiler specialization is a candidate only with validated data, liveness,
status and observer assumptions; no new hardware primitive is demonstrated.
QCG-0 and v0.2 qualification dispositions are unchanged.
