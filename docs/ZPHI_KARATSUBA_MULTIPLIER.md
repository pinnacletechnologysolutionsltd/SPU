# Z[phi] Three-Product Serial Multiplier Contract

Status: proof candidate; the committed four-product
`spu13_zphi_mul_serial` remains the production reference until every gate in
this document passes.

The phased production evaluation, matched P&R gates, rollback rules, and
coding-agent handoff are in `docs/ZPHI_KARATSUBA_INTEGRATION_PLAN.md`.

## 1. Scope

For signed integers `xa`, `xb`, `ya`, and `yb`, compute the unreduced product

```text
(xa + xb*phi)(ya + yb*phi) = out_a + out_b*phi
phi^2 = phi + 1
```

with

```text
out_a = xa*ya + xb*yb
out_b = xa*yb + xb*ya + xb*yb
```

The candidate must preserve the reference module's interface and acceptance
semantics: `start` is accepted only while idle; inputs are captured on the
accepted edge; `busy` remains high during evaluation; `done` pulses with stable
registered outputs. Starts while busy are ignored.

The intended change is exactly four busy cycles to three. No modular
reduction, saturation, truncation, or change to signed interpretation is
permitted.

## 2. Three-product identity

```text
t_ac  = xa*ya
t_bd  = xb*yb
t_sum = (xa+xb)(ya+yb)

out_a = t_ac + t_bd
out_b = t_sum - t_ac
```

Expansion gives

```text
t_sum - t_ac
  = xa*yb + xb*ya + xb*yb
```

so the candidate is algebraically identical over the integers. The proof does
not depend on a modulus.

## 3. Width contract

The reference defaults are `X_W=72`, `Y_W=34`, and `OUT_W=108`.

- `xa+xb` needs 73 signed bits.
- `ya+yb` needs 35 signed bits.
- Their product needs 108 signed bits.
- Therefore unrestricted signed inputs require
  `OUT_W >= X_W + Y_W + 2`.

The default 108-bit output is exact but has no spare sign bit for a wider input
contract. Width extension must occur before addition; wrapping either sum back
to its original width is a correctness failure.

## 4. Acceptance gates

1. Existing four-product testbench remains green.
2. Full-width directed extrema and deterministic random equivalence pass.
3. SymbiYosys exhaustively proves the reduced-width sequential transaction:
   same signed result, candidate completion one cycle before the reference.
4. The unrestricted integer identity above is retained beside the proof.
5. Standalone Artix-7 synthesis compares the mapped multiplier/DSP cost. A
   latency win alone does not authorize replacement if the wider third product
   causes an unacceptable physical-resource or timing regression.
6. Production users are switched only in a separate change after their own
   regressions and, where relevant, board proof.

## 5. Current proof-candidate result (2026-07-20)

Gates 1--4 pass. The full-width comparison covers directed signed extrema and
64 deterministic random vectors. The reduced-width SymbiYosys transaction
proof exhaustively covers every 4-bit by 3-bit signed operand tuple and pins
the three-cycle/four-cycle completion relationship.

Standalone Artix-7 synthesis used:

```bash
yosys -p 'read_verilog <module>; synth_xilinx -family xc7 -noiopad \
  -top <module>; stat'
```

| Metric | Four-product reference | Three-product candidate | Delta |
|---|---:|---:|---:|
| Busy cycles | 4 | 3 | -25% |
| Estimated LCs | 353 | 357 | +4 (+1.1%) |
| DSP48E1 | 8 | 8 | 0 |
| FDRE | 751 | 649 | -102 |
| CARRY4 | 96 | 125 | +29 |

This is a favourable synthesis screen: the wider 73-by-35 third product stays
inside the same eight-DSP mapping. It is not a timing or placement result.
Gate 5 therefore remains partially open until an integration-shaped P&R
comparison exists, and gate 6 remains intentionally open. No production
instance has been replaced.

## 6. Reproduction

```bash
iverilog -g2012 -o build/zphi_karatsuba_tb.vvp \
  hardware/rtl/core/spu13/spu13_zphi_mul_serial.v \
  hardware/rtl/core/spu13/spu13_zphi_mul_serial_karatsuba.v \
  hardware/tests/spu13/spu13_zphi_mul_serial_karatsuba_tb.v
vvp build/zphi_karatsuba_tb.vvp

sby -f hardware/tests/spu13/spu13_zphi_mul_serial_karatsuba_formal.sby
```
