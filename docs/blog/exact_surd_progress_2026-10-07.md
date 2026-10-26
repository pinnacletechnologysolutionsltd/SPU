# Exact Surd arithmetic: progress and its measured costs

7 October 2026

The experimental CPU Surd path stores `(a+b√3)/d` with two signed 64-bit
coefficients and a positive unsigned 64-bit denominator. Its useful promise is
exact arithmetic with explicit failure: compute wide intermediates, commit a
fitting result, and try common-GCD reduction if the raw result is too large.
If reduction still cannot fit, preserve the destination. ADD and SUB align
denominators by GCD before combining coefficients. A fitting zero retains its
raw denominator; scheduled normalization gives `(0,0,1)`. This distinction
preserves the declared raw-fit contract and makes reduction work visible.
The [frozen interface](../../build/spu_surd_register/main_cpu_integration_20261007/implementation_freeze_01/snapshots/knowledge/isa_reference.md)
defines these experimental operations; the older S0 study has a different
unconditional zero-canonicalization policy.

The completed [CPU RTL simulation record](../../build/spu_surd_register/main_cpu_integration_20261007/focused_01/cpu/results.json)
covers 32 retained inputs at each of four chain lengths, including CPU inverse
coefficient preparation, forward transforms and recovery. At twelve joints,
each record retires 2,620 instructions, including 2,056 tuple transfer
instructions and 96 scheduled boundary reductions. Across those 32 records,
simulation records 1,568,084 total cycles, of which 800,820 are alignment cycles
and 383,904 are normalization cycles. The cohort records zero rescue requests,
failures and fallbacks. Zero rescues therefore does not mean zero GCD/quotient
work: alignment and scheduled reduction remain substantial. These measurements
include issuer and transfer costs and exclude boot/reset. Joint coefficients
are rational-only; radical diagnostic cases are separate. The enclosing
[detached result](../../build/spu_surd_register/main_cpu_integration_20261007/focused_01/result.json)
records exit 0. These are simulation cycles, not elapsed board time.

Multiplier parallelism has a concrete resource cost. At W=16, simulation gives
fit-only latency/II of 6/7, 4/5 and 1/2 cycles for one, two and five multiplier
lanes. The corresponding XC7 wrapper maps to 1, 2 and 5 DSP48E1 blocks and
623, 728 and 382 LUTs. All three standalone wrappers route at a 25 MHz target;
their post-route estimates are 108.85, 100.82 and 245.94 MHz. The shorter
five-lane control schedule reduces LUT use in this particular small wrapper,
while spending more DSPs. These wrappers exclude the normalizer, so their
figures do not describe a complete CPU or a normalized kernel.
[Lane simulation and route evidence](../../build/spu_surd_register/mul_arch_20261007/architecture_comparison.md)
preserves the configuration and logs; the timing numbers are tool estimates.

At W=64, the standalone five-lane multiplier plus real normalizer routes with
80 DSP48E1 blocks, 15,341 LUTs and 4,683 flip-flops. Its post-route clock estimate
is 46.90 MHz against a 25 MHz target. This
[combined wrapper result](../../build/spu_surd_register/mul_arch_20261007/combined_w64_lanes5_01/summary.md)
shows the cost of retaining wide exact intermediates and doing exact reduction.
It establishes route feasibility for that wrapper, not integrated CPU timing,
application throughput or energy. A fair integer baseline still lacks an
established executable path in the active canonical CPU; speedup and instruction
elimination remain unmeasured. The
[baseline capability specification](../../spu_strategy/spec_surd_integer_baseline_capabilities_2026-10-07.md)
lists the missing load/readback, wide product/carry, GCD/quotient, status and
sequencing capabilities without expanding the ISA.

Physical evidence has a narrower, historical scope. The
[Wukong ROBOTICS main-core smoke entry](../hardware_evidence.md#30-wukong-artix-7-robotics-main-core-smoke)
records a loaded bitstream and J11 output `13/13 PASSED` and
`ARITHMETIC_BLAZE: PASS` for QLDI, QSUB, ROTC angles 0–5 and six-step closure.
That observation supports those operations in that image. It does not verify
the new explicit-denominator Surd CPU path. The current preparation work reads
existing evidence and prepares analysis; it starts no physical campaign.
