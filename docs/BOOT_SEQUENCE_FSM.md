# Boot Sequence FSM — Canonical Hydration Interlock

**Status:** software oracle complete and suite-registered
(`software/tests/test_boot_sequence.py`). RTL integration not started. The
reserved RTL changes are `hardware/rtl/core/spu13/spu13_core.v` and
`hardware/rtl/peripherals/io/spu_spi_slave.v`.

## 3.1 Purpose

The current core has one structural boot interlock: instructions are gated by
`qrf_hydrated` in `spu13_core.v`. That fixes VE QR register hydration but does
not define one canonical boot contract for RPLU table configuration, SOM weight
hydration, Pell rotor-vault data, or firmware-side reset pacing.

The canonical boot FSM makes the safety invariant explicit:

```
RESET -> HYDRATING -> READY
             |
             v
        FAULT.HYDRATION_TIMEOUT
```

`FAULT.HYDRATION_TIMEOUT` is terminal until explicit reset.

## 3.2 Existing Signals

Existing RTL signals that can feed or motivate the join:

| Subsystem | Generate/enable condition | Existing signal or path | Source |
|---|---|---|---|
| VE QR hydration | QR file generated when `ENABLE_MATH || ENABLE_CORE_SOM || ENABLE_CORE_RPLU_V2 || ENABLE_IROTC` | `ve_qr_init_done`, currently folded into `qrf_hydrated` | `hardware/rtl/core/spu13/spu13_core.v` lines 653-685 |
| Instruction acceptance | core instruction path | `eff_inst_valid = ... && qrf_hydrated`; `inst_accept = eff_inst_valid && !inst_seen` | `hardware/rtl/core/spu13/spu13_core.v` lines 620-645 |
| RPLU v2 config | `ENABLE_CORE_RPLU_V2` | `rplu_cfg_wr_en`, `rplu_cfg_loaded`, `boot_done`; no core-local `rplu_table_loaded` signal yet | `hardware/rtl/top/spu_laminar_boot.v` lines 34-43 and 403-418 |
| SOM weights | `ENABLE_CORE_SOM` | host write path `host_som_we`; no `som_bram_hydrated` signal yet | `hardware/rtl/core/spu13/spu13_core.v` lines 1789-1814 |
| Pell rotor vault | `ENABLE_MATH` | `pell_we && !boot_done` writes `spu_rotor_vault`; no SPI-spin readiness exposure | `hardware/rtl/core/spu13/spu13_core.v` lines 438-451 |

Do not invent implicit readiness. RPLU and SOM need explicit ready lines in the
RTL integration:

- `rplu_table_loaded`: true when the enabled RPLU config record counter reaches
  the build's `RPLU_CFG_RECORDS`.
- `som_bram_hydrated`: true when the enabled SOM weight write counter reaches
  the build's required node-feature count, or true at reset only for fixed
  initial-block fixture spins that deliberately do not use host hydration.

## 3.3 Join Guard

The HYDRATING exit guard is the generate-conditional AND-join:

```
boot_ready =
    (!VE_ENABLED   || ve_qr_init_done) &&
    (!RPLU_ENABLED || rplu_table_loaded) &&
    (!SOM_ENABLED  || som_bram_hydrated)
```

`VE_ENABLED` is the existing QR-file generate predicate in `spu13_core.v`:
`ENABLE_MATH || ENABLE_CORE_SOM || ENABLE_CORE_RPLU_V2 || ENABLE_IROTC`
(`hardware/rtl/core/spu13/spu13_core.v` lines 653-660).

This subsumes `qrf_hydrated`. The instruction license becomes:

> No instruction is accepted outside READY.

That means the current `qrf_hydrated` term in `eff_inst_valid` becomes one input
to the boot join, not a separate one-off interlock.

## 3.4 Watchdog Bound

The watchdog is parameter-derived, not estimated:

```
BOOT_WATCHDOG_CYCLES =
    max(enabled_ready_line_lengths)
```

Current lengths:

| Ready line | Length | Provenance |
|---|---:|---|
| VE QR hydration | 13 cycles | `spu_ve_qr_init.v` documents 13 init cycles and emits one lane per active cycle; see lines 19-20 and 99-112 |
| RPLU table load | build parameter `RPLU_CFG_RECORDS`; 149 in the RPLU2 consume probe, 2051 default in `spu_laminar_boot.v` | consume probe lines 25 and 58-61; module default lines 8-11 |
| SOM BRAM host hydration | 28 writes for current 7-node, 4-feature core path | config address is `{node_id[2:0], feature_id[1:0]}` and the BMU instance is `NUM_FEATURES=4`, `MAX_NODES=7`; see `spu13_core.v` lines 1789-1814 |

For the IROTC SPI spin with no RPLU/SOM boot, the current bound is 13. For the
RPLU2 consume profile, the bound is 149 if VE is also enabled. For the
`spu_laminar_boot.v` default parameter, the RPLU length is 2051.

If HYDRATING has not reached the join at `BOOT_WATCHDOG_CYCLES + 1`, transition
to `FAULT.HYDRATION_TIMEOUT`. Completion exactly at the bound reaches READY.

## 3.5 Pell Vault Scope

The Pell rotor vault has a hydration port: `spu_rotor_vault` takes `init_we`,
`init_step`, and `init_rotor` (`hardware/rtl/core/shared/spu_rotor_vault.v`
lines 23-33), and `spu13_core.v` drives it from `pell_we && !boot_done`
(`hardware/rtl/core/spu13/spu13_core.v` lines 438-451).

The current SPI instruction spins do not expose a southbridge path for Pell
vault hydration. QROT/rotor behavior on such spins therefore depends on the
vault's initial orbit contents, not a link-verified hydration transaction. The
southbridge path should be a future `0xA5`-style config stream for the eight
Pell orbit records, with a `pell_vault_loaded` ready line added to the join
when QROT is enabled. That is explicitly out of scope for this order.

## 3.6 Status Exposure

Firmware must poll readiness instead of sleeping after reset.

Current `0xAC` status returns `[laminar_hi, laminar_lo, flags, rplu_mode]`
(`hardware/rtl/peripherals/io/spu_spi_slave.v` lines 10-14 and 430-438). The
current flags byte is saturated:

```
flags[7:5] = ratio_lat[2:0]
flags[4]   = ratio_valid
flags[3]   = fifo_full
flags[2]   = turbulence
flags[1]   = janus
flags[0]   = snap
```

There is no free bit in the current flags byte. The implementable reserved bit
without repacking is status byte 3 bit 2:

```
status[3][2] = boot_ready
```

If the reserved RTL change instead repacks the flags byte, the firmware compile
defines `SPU_BOOT_READY_STATUS_BYTE` and `SPU_BOOT_READY_STATUS_MASK` identify
the selected byte/bit.

## 3.7 Oracle Coverage

`software/lib/boot_sequence_oracle.py` models the finite automaton exactly.
`software/tests/test_boot_sequence.py` checks:

- watchdog boundary: completion at the bound reaches READY, bound+1 faults;
- all 2^3 VE/RPLU/SOM generate combinations collapse the join correctly;
- exhaustive reachability has no instruction-accept edge from non-READY states;
- `FAULT.HYDRATION_TIMEOUT` has no outgoing edge except explicit reset.
