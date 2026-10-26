# SOM-RP0a — HALTED at the width review (contract §3 step 1)

2026-10-20. Contract: [`spu_strategy/contract_som_rp0_2026-10-20.md`](../../spu_strategy/contract_som_rp0_2026-10-20.md),
owner-approved for host-only Class A work. **Stopped before implementation**, as the contract
requires: the RTL, the C++ header and the Python oracle disagree on inputs that the SOM v1
uploader accepts. No C BMU was written. No firmware, RTL, simulator, oracle or product file
changed. Nothing was flashed or run on hardware.

## The supported domain

SOM v1 (`docs/SOM_V1_PRODUCT_CONTRACT.md`): features and prototypes are `{Q[17:0], P[17:0]}`,
signed 18-bit. The uploader (`tools/som_map.py`, `COEFFICIENT_BITS = 18`) accepts **every**
signed 18-bit coefficient for features, prototypes and the four feature weights. So the
supported input domain is the full signed 18-bit Q(√3) range.

## Evidence (executed, not inferred)

| Case (all inputs uploader-valid) | Python oracle (exact) | RTL `spu_som_bmu.v` (unmodified, iverilog) | RTL overflow flag | C++ `spu_rational_som.h` |
|---|---|---|---|---|
| control: x₀ = 100+3√3, w₀ = −20+√3, r = 1 | (14412, 480) | (14412, 480) | 0 | (14412, 480) |
| diffwrap: x₀ = 131071, w₀ = −131072, r = 1 | (68718952449, 0) | **(1, 0)** | **0** | (−524287, 0); UBSan: signed overflow |
| prodwrap: x₀ = 65536, w₀ = 0, r₀ = 16 | (68719476736, 0) | **(0, 0)** | **0** | (0, 0); signed overflow |
| sumflag: x = 60000 in all 4 features, w = 0, r = 1 | (14400000000, 0) | (1515098112, 0) | 1 | (1515098112, 0); signed overflow |

The control confirms the probe harness is correct. **diffwrap** and **prodwrap** are silent
wrong distances: the RTL raises no flag. In sumflag the flag fires, but a truncated distance is
still emitted as the result (it is a flag, not a refusal).

Mechanism (from `rs_weighted_quadrance`, `spu_som_bmu.v`):

1. The difference x − w of two signed 18-bit values needs 19 bits. It is passed into a
   `signed [17:0]` argument, so it wraps silently.
2. dp², 3dq², sq_p, sq_q and the weighted products are held in 36-bit signed registers.
   sq_p can reach 2³⁶, and sq_p·r_p is truncated back to 36 bits, so both wrap silently.
3. The only overflow check is at the 4-feature sum, 64 → 32 bits. Mechanisms 1 and 2 occur
   before it and are invisible to it.

The C++ header stores coefficients in `int32_t`, so its arithmetic overflows: this is undefined
behaviour, not a defined wrap. Separately, its `rs_lt` takes int32 differences.

## Sufficient safe range (derived; not adopted)

Let |Δp|, |Δq| ≤ D and |r_p|, |r_q| ≤ R. Then the per-feature |w_p| ≤ 10D²R and
|w_q| ≤ 6D²R, and the 4-feature p sum is ≤ 40D²R. The RTL is exact and unflagged if
D ≤ 2¹⁷ − 1, 10D²R < 2³⁵ and 40D²R < 2³². With unit weights (R = 1) that means
**D ≤ 10,362**, i.e. coefficients |·| ≤ 5,181. The SOM v1 Iris map (features ×10, unit weights)
lies far inside this range, so **existing SOM silicon evidence is not contradicted**. The defect
concerns inputs the uploader admits but that no test exercises. Real sensor features could reach
it: for example, the INA226 currents in microamps were around 10⁵.

## Decision needed (owner)

1. **Named restricted profile.** Define e.g. `SOM-v1-safe` with a proven bound such as the one
   above, enforced by the uploader. The RTL is unchanged. This narrows the published domain, so
   it is a product decision, not an implementer's.
2. **RTL repair.** Use a 19-bit difference, wide enough products, and refusal rather than
   flag-and-emit. That needs a separate RTL contract, regression and re-qualification of
   affected silicon claims.
3. **C BMU follows the oracle** on the full domain (64-bit arithmetic, 128-bit or bounded
   comparison) and flags any input outside the RTL-safe range. RP0a would then no longer match
   the silicon outside that range. That divergence would have to be stated in every result.

My recommendation is option 3 for RP0a (exact everywhere, plus an explicit "outside RTL-safe"
status), together with option 2 tracked as a real defect. The decision is yours: the
contract forbids choosing silently.

## Reproduction

```bash
mkdir -p build/som_rp0
timeout 60 bash -c 'ulimit -v 1048576; iverilog -g2012 -o build/som_rp0/probe.vvp research/som_rp0/som_width_probe.v hardware/rtl/core/spu13/spu_som_bmu.v hardware/rtl/core/spu13/spu_som_weight_bram.v && vvp -n build/som_rp0/probe.vvp'
```

`som_width_probe.v` is deliberately not named `*tb*`, so `run_all_tests.py` does not pick it up.
It prints raw values, not PASS/FAIL. The C++ UBSan probe and the Python oracle commands were
run from the session scratchpad. The four oracle values above are reproducible with
`rational_som.weighted_quadrance`.
