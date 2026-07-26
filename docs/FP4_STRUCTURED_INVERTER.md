# Structured A31 inverter candidate

Status: arithmetic blocks only; production default unchanged.

This tranche replaces the inverter's seven general A31 transactions (112
logical M31 products) with four structure-specific requests totaling exactly
20 products:

| Request | Products | Result |
|---|---:|---|
| Stage A | 6 | `Z * conj_5(Z) -> (w0,w1,0,0)` |
| Stage B | 2 | `w0^2 - 3*w1^2 -> N` |
| Stage D1 | 8 | `Z_conj * (wc0,wc1,0,0) -> Temp` |
| Stage D2 scale | 4 | four independent `Temp[i] * N_inv` products |
| **Total** | **20** | **four structured requests** |

The general Padé multiplier remains required. The candidate shared-parallel
backend will therefore multiplex these operands onto the existing 16-product
bank; it must not add a second narrow multiplier bank. The sequential backend
will execute only the declared number of schedule entries. Both candidates
must retain mod-3 residue checking for every structured result.

## Formal resolution

This tranche uses contract resolution **(b), the split gate**. The new
operand-map and modular-combiner blocks are parameterized and proven against
an independently written full-product reference at field/product width pairs
3/6 and 4/8. The complete candidate will additionally be checked at true M31
width against committed v1, comparing values and `flags_v` at each
implementation's own `done`.

## Predeclared physical and latency gates

These thresholds were fixed before any candidate-enabled backend synthesis or
place-and-route run. Each physical comparison uses matched source commits,
tool versions, constraints, and a fresh artifact name. Seeds 1, 7, 13, and 2
remain unavailable for ad-hoc work.

| Backend | DSP gate | LUT gate | FF gate | Fmax gate | Unit latency | Singular latency |
|---|---:|---:|---:|---:|---:|---:|
| Shared parallel | candidate <= matched v1 | <= 1.08x v1 | <= 1.05x v1 | >= 0.90x v1 | <= 77 clocks | <= 7 clocks |
| Sequential | candidate <= matched v1 | <= 1.10x v1 | <= 1.10x v1 | >= 0.90x v1 | <= 160 clocks | <= 35 clocks |

Latency is rising-edge index difference from accepted `start` to `done`.
There must be no operand-dependent variance within either outcome class.
The shared-parallel gate measures released occupancy as well as end-to-end
latency; unchanged DSP count is expected because Padé retains the general
multiplier.

## Preserved findings outside this change

- Historical sequential integration is invalid because its shared-operand mux
  does not hold inverter operands over the sequential multiplier schedule.
  Candidate plumbing must fix that structurally; the v1 artifact is not
  rewritten.
- `spu13_batch_inverter.v` leaves its multiplier `rns_error` unconnected. This
  pre-existing gap remains recorded and is not silently folded into the
  structured-inverter change.
