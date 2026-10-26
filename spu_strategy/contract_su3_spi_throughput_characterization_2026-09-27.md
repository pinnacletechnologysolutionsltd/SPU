# Engineering Contract: SU3 Existing-Image SPI Throughput Characterization

**Date:** 2026-09-27  
**Contract ID:** `SU3-SPI-THROUGHPUT-2026-09-27`  
**Status:** `Q0 PASS; Q1 IMPLEMENTATION PASS; PHYSICAL SWEEP NOT RUN`  
**Owner:** John Curley

## 1. Objective and boundary

Measure the reliable end-to-end SPI-visible throughput of the already-qualified
standalone SU3 Wukong J11 image before authorizing another FPGA build. Reuse the
exact existing FPGA image and frozen dense A/B workload. This tranche changes
only the RP2350 characterization firmware and its build configuration; it does
not change FPGA RTL, constraints, bitstreams, fixtures, SU3 arithmetic, or the
shared-multiplier image.

The primary result is the highest tested **achieved SCK rate** at which repeated
full SU3 operations produce exact expected results, plus the first tested
unreliable rate. Report the end-to-end operation rate for the fixed workload;
do not label it arithmetic-core throughput or compare it to a different
matrix, result-selection, guard, or firmware configuration.

## 2. Frozen baseline and workload

Use the standalone Wukong J11 SU3 image recorded in
`docs/hardware_evidence.md` §3.2e.6:

* FPGA artifact SHA-256:
  `a8b9f661892fd0520afa5e685e40757d3edadcde97c206ba086f1c2018b77d96`
* Existing RP2350 firmware SHA-256:
  `d2dabc0b6d7639de63a42136bf14d68a965a118d08a36d89dab2df5a81ffde91`
* Frozen input: existing `dense_a` and `dense_b` matrices in
  `hardware/rp2350/rp2350_su3_j11_smoke.c`.
* One measured operation: send `SU3_START` selecting one output element, send
  all 9 elements of A and all 9 elements of B (eight 32-bit chunks per element),
  wait for the existing sidecar-ready state, issue `SU3_READ`, read the QR
  record, and compare all four 64-bit result fields plus valid/lane against the
  existing exact expected tuple.
* Cycle the selected output element 0 through 8 so the characterization checks
  every result element. A one-operation latency measurement uses element 0 and
  the same complete transaction.

This is deliberately a full load/compute/read transaction, not nine separate
products grouped and presented as one product. The current smoke's nine-case
loop performs nine independent products because each `SU3_START` selects a
single result element.

## 3. Measurement protocol to implement in Q1

Add a dedicated characterization mode to the existing RP2350 smoke target, or
an equivalent narrowly scoped target that reuses the exact fixture and
transaction helpers. A single firmware image shall sweep the requested baud
rates by calling `spi_set_baudrate`; print both requested and achieved rates.
Use this fixed requested sequence:

```text
100000, 250000, 500000, 1000000, 2000000,
4000000, 6000000, 7000000, 8000000 Hz
```

Do not test a requested rate above 8 MHz. Do not treat the requested rate as
the measurement: each result row is indexed and classified by the achieved
rate returned by the RP2350 SDK. If two requests quantize to the same achieved
rate, record the duplicate and do not count it as a distinct sweep point.
Before sending any command at a new point, stop without exercising that point
if the achieved SCK is above `SPU_CORELESS_SPIN_SCK_CEILING_HZ` (8.3 MHz).

For every distinct rate:

1. Set the frozen four J11 link guard values to **20 us each**. This is a
   characterization control, not a claim that 20 us is a minimum; current
   silicon has prior successful evidence at 5 us, while this experiment is
   intended to isolate SCK rate.
2. Run three consecutive blocks. Each block is nine back-to-back full
   operations, selecting output elements 0 through 8 once each.
3. Compare every reported A/B/C/D tuple, valid bit, and lane with the frozen
   expected value. Any dropped command, timeout, invalid result, or mismatch
   marks that rate unreliable. Preserve the failing status and result bytes.
4. Measure one element-0 operation from immediately before its START command
   through completion of its QR read. Also time each nine-operation block.
   Report median and maximum operation latency and each block's operations per
   second. Include loading, FPGA preparation/computation, result polling/read,
   firmware call overhead, and configured guard delays in this end-to-end
   metric.
5. Count bytes clocked in the characterization firmware, including variable
   status polls. Each operation has 146 instruction-write chords (10 bytes
   each), one QR read (35 bytes), plus five bytes per status poll. Calculate
   the ideal wire-time lower bound from that measured byte count and achieved
   SCK. Report measured-minus-wire time as residual
   protocol/guard/compute/software time. Do not label that residual “host
   overhead” or “compute latency” because this measurement does not separate
   those components.

Start at 100 kHz and progress upward. On the first unreliable rate, record it,
then stop the upward sweep and report the immediately preceding rate as the
highest tested reliable rate. That preceding rate already has three complete
clean blocks. Do not continue using a potentially desynchronized FPGA after
the first failed operation, and do not automatically retry a failed operation
until it passes; retries would hide the first failure.

## 4. Q0 source review result

PASS for the measurement boundary. The existing firmware already contains the
frozen dense matrices, all nine exact expected outputs, QR decoding, status
polling, and configurable SPI initialization. The standalone image and
firmware hashes are documented. The current `run_case()` selects one result
element at `SU3_START`, reloads both full matrices, then reads that one result;
therefore the proposed one-operation and nine-element blocks have precise
transaction meanings.

The current firmware's per-word status polling, retry loop, verbose USB output,
and 250 us unchecked word delay are unsuitable for timing measurements. Q1
must use a deterministic no-retry measurement loop with explicit timeout/error
handling and low-volume logging. It must report achieved SCK, not just the
requested setting. No source or hardware was changed during Q0 review.

## 5. Q1 implementation and gates — pending authorization

1. Add the characterization mode and rate-setting path without changing the
   default smoke behavior or frozen SU3 fixture/transaction encoding.
2. Add a non-retrying exact-result operation and the fixed three-block sweep.
3. Emit machine-readable per-rate output containing requested/achieved SCK,
   pass/fail count, first failure details, one-operation latency, block
   durations, operations/second, exact wire-byte count, and ideal wire-time
   lower bound.
4. Run the existing SU3 software oracle and the focused SU3 Verilog tests after
   firmware changes. No FPGA synthesis, place-and-route, programming, or
   bitstream change is in Q1.

Commands after Q1 implementation:

```bash
cmake -S hardware/rp2350 -B build/rp2350_su3_throughput -G Ninja \
  -DPICO_SDK_PATH=/home/user/.pico/pico-sdk \
  -DPICO_BOARD=pico2 -DSPU_RP2350_ZERO_HEADER_SPI=ON
cmake --build build/rp2350_su3_throughput --target \
  rp2350_su3_j11_smoke rp2350_su3_j11_characterize -j4
python3 software/tests/test_su3_oracle.py
iverilog -g2012 -I hardware/rtl/arch \
  -y hardware/rtl/core/spu13 \
  -o build/spu13_su3_mult_tb.vvp \
  hardware/tests/spu13/spu13_su3_mult_tb.v
vvp build/spu13_su3_mult_tb.vvp
iverilog -g2012 -I hardware/rtl/arch \
  -y hardware/rtl/core/spu13 \
  -o build/spu13_su3_sidecar_tb.vvp \
  hardware/tests/spu13/spu13_su3_sidecar_tb.v
vvp build/spu13_su3_sidecar_tb.vvp
```

The physical sweep reuses the exact FPGA image named above. RP2350 firmware
build/load and operator-attended USB capture are separate evidence dimensions;
record hashes for the resulting firmware and the actual Artix image used.

**Q1 result: PASS.** The opt-in `rp2350_su3_j11_characterize` target was added;
the default `rp2350_su3_j11_smoke` path retains its historical compile-time
defaults. The characterization mode performs three blocks of nine exact
checked full operations at each achieved rate, with no command retries. It
records status-poll bytes, the complete QR read in operation latency, operation
latencies and wire counts, and block throughput. Per-operation diagnostics
print after each block so USB logging is outside the measured block interval.
It stops at the first failed operation and refuses an achieved SCK above
8.3 MHz. The hardware sweep has not been run; no image was programmed and no
FPGA build was performed.

Built characterization UF2:
`build/rp2350_su3_throughput/rp2350_su3_j11_characterize.uf2`,
SHA-256 `1b1c93a90f9cf5c0676a7900fc3093410558f9f4e12c803be847c39c57a230ad`.

Focused verification PASS:

```text
cmake --build build/rp2350_su3_throughput --target \
  rp2350_su3_j11_smoke rp2350_su3_j11_characterize -j4
python3 software/tests/test_su3_oracle.py              (20 checks)
spu13_su3_mult_tb                                      (0 errors)
spu13_su3_sidecar_tb                                   (0 errors)
```

## 6. Later Karatsuba comparison — explicitly out of scope

Do not implement or build a Karatsuba candidate under this contract. The next
arithmetic-comparison contract must first state which level it changes. The
source review found two distinct candidate locations:

1. **Complex A31 product schedule in `spu13_su3_mult`:** the FSM currently
   issues four A31 multiplies in sequence (`RR`, `II`, `RI`, `IR`) for each
   complex product. A complex Karatsuba identity could reduce that schedule
   from four A31 operations to three, adding modular operand/result additions
   and changing SU3 operation latency while leaving the M31 multiplier's
   physical product bank unchanged. This is the direct candidate if the
   throughput sweep shows compute latency dominates.
2. **Base-field 32x32 product implementation in
   `spu13_m31_multiplier`:** a 16x16 Karatsuba decomposition changes the
   shared M31 multiplier's internal DSP/LUT/timing tradeoff and affects every
   consumer of that unit. This is a different, broader hardware experiment;
   it is relevant only if the arithmetic implementation, rather than SPI
   transport or the SU3 FSM schedule, is the measured bottleneck.

The existing source therefore makes the first candidate the smaller SU3
experiment. Do not call either candidate simply “Karatsuba reduction” in
results; identify which schedule or multiplier was changed.

Any later comparison must hold operand domain, modular semantics, FPGA part,
timing constraints, and workload constant. For the complex-product schedule,
report changed internal initiation/latency and end-to-end matrix latency; for
the base-field multiplier, report LUT/FF/DSP and routed Fmax as well. Report
SPI-visible throughput separately. Do not use this transport characterization
alone to claim Karatsuba benefit.

## 7. Evidence record

| Evidence dimension | Status |
|---|---|
| Structural validation | Q0 source/workload review PASS |
| Functional simulation | Existing SU3 oracle: 20 checks PASS; multiplier and sidecar testbenches PASS |
| Synthesis / place-and-route | NOT RUN; no FPGA build authorized or needed |
| Interface validation | Existing J11 mapping evidence; characterization firmware built; new rate sweep NOT RUN |
| Silicon observation | Existing full-oracle SU3 proof at 25 kHz; new throughput campaign NOT RUN |
