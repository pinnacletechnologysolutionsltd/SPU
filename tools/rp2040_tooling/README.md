# RP2040 Tooling Cache

Local third-party RP2040 utility checkouts live under `repos/`. That directory
is intentionally git-ignored so external source trees do not become part of the
SPU repository history.

## Current Tools

| Tool | Upstream | Pinned commit | Purpose |
|---|---|---|---|
| `pico-dirtyJtag` | `https://github.com/phdussud/pico-dirtyJtag.git` | `59b7f34fb031e164dafae6b3a56875687d1acf77` | RP2040 DirtyJTAG adapter for Wukong Artix-7 JTAG bring-up |

## Rebuild DirtyJTAG

```bash
cmake -S tools/rp2040_tooling/repos/pico-dirtyJtag \
  -B build/pico_dirtyjtag_zero \
  -G Ninja \
  '-DCMAKE_C_FLAGS=-mcpu=cortex-m0plus -mthumb -DBOARD_TYPE=BOARD_RP2040_ZERO'
cmake --build build/pico_dirtyjtag_zero --target dirtyJtag -j
```

Expected output:

```text
build/pico_dirtyjtag_zero/dirtyJtag.uf2
```

The UF2 flashed on 2026-06-30 was also copied to:

```text
build/pico_dirtyjtag/dirtyJtag.uf2
```

Rebuild before using that cached UF2 on Wukong. Older copies may still use the
upstream Pico default pinout on GP16-GP19.

Verify the generated UF2 before flashing:

```bash
picotool info -a build/pico_dirtyjtag_zero/dirtyJtag.uf2
```

The fixed-pin block must include:

```text
0: TDI
1: TMS
2: TCK
3: TDO
4: RST
5: TRST
```

Do not use a UF2 that reports the upstream Pico default `16: TDI`,
`17: TDO`, `18: TCK`, `19: TMS` with the low-pin GP0-GP3 bench wiring.

## Wukong Low-Pin DirtyJTAG Pinout

Build with `BOARD_TYPE=BOARD_RP2040_ZERO` as shown above. This avoids the
upstream Pico default on GP16-GP19, which is not accessible in the current
Wukong bench wiring.

```text
RP2040 GP2  -> target TCK
RP2040 GP1  -> target TMS
RP2040 GP0  -> target TDI
RP2040 GP3  <- target TDO
RP2040 GND  -> target GND
```

For the QMTech Wukong V02 J1 schematic, the visible JTAG header nets are:

```text
J1-1  3V3 target reference
J1-2  TCK
J1-3  TDO
J1-4  TDI
J1-5  TMS
J1-6  no visible net label in the V02 schematic crop
```

Do not use J1-3 as ground; it is TDO on the V02 schematic. Use a confirmed
Wukong GND point for the RP2040 ground lead.
Power Wukong from its normal input and measure J1-1 only as the target 3.3 V
reference. Before first SRAM load, set any configuration-mode jumpers or DIP
switches to the board's JTAG/safe mode per silkscreen.

Optional reset pin:

```text
RP2040 GP4  -> target RST
```

Leave TRST disconnected unless the target header exposes it and the wiring has
been checked.

Current bench result, 2026-07-02: the corrected low-pin UF2 above builds and
`picotool info -a` reports `0:TDI 1:TMS 2:TCK 3:TDO`. It has not yet been
flashed because `picotool load -f build/pico_dirtyjtag_zero/dirtyJtag.uf2`
reported no RP2040 in BOOTSEL/Picoboot mode. Treat earlier
`TDO is stuck at 0` detect results as inconclusive until the corrected UF2 is
flashed and the Wukong J1 wiring is changed to the pinout above.
