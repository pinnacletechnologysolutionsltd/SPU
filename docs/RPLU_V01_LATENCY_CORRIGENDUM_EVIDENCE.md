# RPLU v0.1 inverter-latency corrigendum evidence

Date: 2026-07-26 NZST

This note pins the historical v1 latency measurement required before the
structured-inverter v2 tranche.  The measured RTL is the exact source named by
the RPLU v0.1 Zenodo deposit, not current `master` and not a back-port of the
new latency bench.

## Result

Rising-edge index convention:

```text
latency = done_rising_edge_index - debug_start_accept_rising_edge_index
```

| Historical backend/path | Unit completion | Stage-B singular | Status |
|---|---:|---:|---|
| Parallel leaf inverter | 83 | 7 | PASS |
| Parallel integrated shared path, uncontended | 83 | 7 | PASS |
| Sequential-fallback leaf inverter | 314 | 73 | PASS |
| Sequential-fallback integrated shared path | not valid | not valid | FAIL; pre-existing ownership defect |

The parallel shared-multiplier arbitration delta is zero clocks for both
outcome classes.  Four distinct units produced the same 83-clock latency.
Both zero and the nonzero zero-divisor `(753804466,0,0,1)` produced the same
7-clock exception latency and asserted `flags_v`.

The published parallel tower constant is therefore **83 clocks**, not 76.
The tower-plus-12-clock shadow-chain model is **95 clocks**, not 88.

The sequential leaf result is a newly clarified backend-specific number; it
does not replace the parallel number in the v0.1 cycle model.  The historical
sidecar cannot validly share the sequential fallback as wired.  Its mux selects
inverter operands only during the one-cycle `inv_mult_start` pulse, whereas
`spu13_m31_multiplier_seq` rereads its operand ports throughout the 16-product
schedule.  After launch, the mux returns to the idle Padé inputs.  The raw run
below consequently shows unknown unit results and missed singular faults.  No
integrated sequential latency is claimed from that run.

## Provenance

- Historical RTL commit:
  `f1e4dbf06aa1163cc98005feb063ec8aae7c933a`
- Historical worktree: detached clean worktree at `/tmp/spu-f1e4dbf`
- Bench:
  `hardware/tests/spu13/spu13_fp4_inverter_latency_tb.v`
- Bench SHA-256:
  `b17087a3c1e0ee3d38130ec69f6db42de1e663b1c8b2527163fd4cf8c7177029`
- Simulator/compiler: Icarus Verilog and VVP 14.0 (devel),
  `s20251012-123-g49126efa7`
- Historical RTL was unmodified: `git -C /tmp/spu-f1e4dbf diff --exit-code`
  returned exit 0 with no output.

## Exact commands

Parallel compile:

```sh
iverilog -g2012 -o /tmp/spu-f1e4-latency-par.vvp hardware/tests/spu13/spu13_fp4_inverter_latency_tb.v /tmp/spu-f1e4dbf/hardware/rtl/core/spu13/spu13_fp4_inverter.v /tmp/spu-f1e4dbf/hardware/rtl/core/spu13/spu13_m31_multiplier.v /tmp/spu-f1e4dbf/hardware/rtl/core/spu13/spu13_rplu2_pade_sidecar.v /tmp/spu-f1e4dbf/hardware/rtl/gpu/rplu_thimble_pade.v
```

Parallel run:

```sh
vvp /tmp/spu-f1e4-latency-par.vvp
```

Sequential-fallback compile:

```sh
iverilog -g2012 -DSPU_LATENCY_SEQ -o /tmp/spu-f1e4-latency-seq.vvp hardware/tests/spu13/spu13_fp4_inverter_latency_tb.v /tmp/spu-f1e4dbf/hardware/rtl/core/spu13/spu13_fp4_inverter.v /tmp/spu-f1e4dbf/hardware/rtl/core/spu13/spu13_m31_multiplier_seq.v /tmp/spu-f1e4dbf/hardware/rtl/core/spu13/spu13_m31_multiplier_seq_fallback.v /tmp/spu-f1e4dbf/hardware/rtl/core/spu13/spu13_rplu2_pade_sidecar.v /tmp/spu-f1e4dbf/hardware/rtl/gpu/rplu_thimble_pade.v
```

Sequential-fallback run:

```sh
vvp /tmp/spu-f1e4-latency-seq.vvp
```

## Raw unedited output — parallel

```text
HISTORICAL_RTL_COMMIT f1e4dbf06aa1163cc98005feb063ec8aae7c933a
CYCLE_CONVENTION done_rising_edge_index - debug_start_accept_rising_edge_index
BACKEND spu13_m31_multiplier.v parallel uncontended
LATENCY path=leaf class=unit case=identity accept_edge=6 done_edge=89 delta=83 flags_v=0
LATENCY path=integrated class=unit case=identity accept_edge=91 done_edge=174 delta=83 flags_v=0
LATENCY path=leaf class=unit case=scalar_two accept_edge=176 done_edge=259 delta=83 flags_v=0
LATENCY path=integrated class=unit case=scalar_two accept_edge=261 done_edge=344 delta=83 flags_v=0
LATENCY path=leaf class=unit case=pure_sqrt3 accept_edge=346 done_edge=429 delta=83 flags_v=0
LATENCY path=integrated class=unit case=pure_sqrt3 accept_edge=431 done_edge=514 delta=83 flags_v=0
LATENCY path=leaf class=unit case=mixed_unit accept_edge=516 done_edge=599 delta=83 flags_v=0
LATENCY path=integrated class=unit case=mixed_unit accept_edge=601 done_edge=684 delta=83 flags_v=0
LATENCY path=leaf class=singular case=zero accept_edge=686 done_edge=693 delta=7 flags_v=1
LATENCY path=integrated class=singular case=zero accept_edge=695 done_edge=702 delta=7 flags_v=1
LATENCY path=leaf class=singular case=nonzero_zero_divisor accept_edge=704 done_edge=711 delta=7 flags_v=1
LATENCY path=integrated class=singular case=nonzero_zero_divisor accept_edge=713 done_edge=720 delta=7 flags_v=1
SUMMARY leaf_unit=83 leaf_singular=7 integrated_unit=83 integrated_singular=7 arbitration_delta_unit=0 arbitration_delta_singular=0
PASS historical_fp4_latency (0 failures)
hardware/tests/spu13/spu13_fp4_inverter_latency_tb.v:286: $finish called at 7206000 (1ps)
```

## Raw unedited output — sequential fallback

```text
HISTORICAL_RTL_COMMIT f1e4dbf06aa1163cc98005feb063ec8aae7c933a
CYCLE_CONVENTION done_rising_edge_index - debug_start_accept_rising_edge_index
BACKEND spu13_m31_multiplier_seq.v fallback uncontended
LATENCY path=leaf class=unit case=identity accept_edge=6 done_edge=320 delta=314 flags_v=0
FAIL result path=integrated case=identity expected=00000001,00000000,00000000,00000000 got=xxxxxxxx,xxxxxxxx,xxxxxxxx,xxxxxxxx
LATENCY path=integrated class=unit case=identity accept_edge=322 done_edge=636 delta=314 flags_v=0
LATENCY path=leaf class=unit case=scalar_two accept_edge=638 done_edge=952 delta=314 flags_v=0
FAIL result path=integrated case=scalar_two expected=40000000,00000000,00000000,00000000 got=xxxxxxxx,xxxxxxxx,xxxxxxxx,xxxxxxxx
LATENCY path=integrated class=unit case=scalar_two accept_edge=954 done_edge=1268 delta=314 flags_v=0
LATENCY path=leaf class=unit case=pure_sqrt3 accept_edge=1270 done_edge=1584 delta=314 flags_v=0
FAIL result path=integrated case=pure_sqrt3 expected=00000000,55555555,00000000,00000000 got=xxxxxxxx,xxxxxxxx,xxxxxxxx,xxxxxxxx
LATENCY path=integrated class=unit case=pure_sqrt3 accept_edge=1586 done_edge=1900 delta=314 flags_v=0
LATENCY path=leaf class=unit case=mixed_unit accept_edge=1902 done_edge=2216 delta=314 flags_v=0
FAIL result path=integrated case=mixed_unit expected=7122397b,1212af65,4d457009,1d8ab3fe got=xxxxxxxx,xxxxxxxx,xxxxxxxx,xxxxxxxx
LATENCY path=integrated class=unit case=mixed_unit accept_edge=2218 done_edge=2532 delta=314 flags_v=0
LATENCY path=leaf class=singular case=zero accept_edge=2534 done_edge=2607 delta=73 flags_v=1
FAIL flags path=integrated case=zero expected=1 got=0
LATENCY path=integrated class=singular case=zero accept_edge=2609 done_edge=2923 delta=314 flags_v=0
LATENCY path=leaf class=singular case=nonzero_zero_divisor accept_edge=2925 done_edge=2998 delta=73 flags_v=1
FAIL flags path=integrated case=nonzero_zero_divisor expected=1 got=0
LATENCY path=integrated class=singular case=nonzero_zero_divisor accept_edge=3000 done_edge=3314 delta=314 flags_v=0
SUMMARY leaf_unit=314 leaf_singular=73 integrated_unit=314 integrated_singular=314 arbitration_delta_unit=0 arbitration_delta_singular=241
FAIL historical_fp4_latency (6 failures)
hardware/tests/spu13/spu13_fp4_inverter_latency_tb.v:286: $finish called at 33146000 (1ps)
```
