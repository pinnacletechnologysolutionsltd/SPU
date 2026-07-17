# SOM1 decision-evidence frame

Date: 2026-07-17
Status: RTL, SPI testbench, firmware transport, host parser, and renewed Tang
25K build verified; silicon proof pending.

## Purpose

`SOM1` is the stable observation-to-decision ABI for the writable rational SOM
sidecar. It reports enough evidence to replay a classification exactly instead
of exposing only a winning label. The legacy one-byte UART telemetry and SPI
command `0x01` remain unchanged.

## Transport

The standalone SOM sidecar assigns local SPI read command `0x02` to `SOM1`.
With CS asserted, the master writes `0x02`, observes the normal command-byte
turnaround, then clocks 52 dummy bytes. Byte 0 is returned first. The FPGA
snapshots the complete frame at CS assertion, so one read cannot mix result
generations.

The RP2350 diagnostic console exposes the same transaction as `som1` and prints
`OK som1 raw=<52 hexadecimal bytes>`. `spu_host.SPUHostClient.som1_result()`
validates and decodes it.

## Fixed v1 layout

All multibyte integers and the appended CRC are big-endian.

| Offset | Size | Field |
|---:|---:|---|
| 0 | 4 | magic, ASCII `SOM1` |
| 4 | 1 | version, `1` |
| 5 | 1 | total frame length, `52` |
| 6 | 1 | flags |
| 7 | 1 | error code |
| 8 | 4 | map generation |
| 12 | 4 | result generation |
| 16 | 2 | winning node |
| 18 | 2 | runner-up node |
| 20 | 2 | semantic class label from the hydrated map |
| 22 | 2 | reserved, zero |
| 24 | 8 | best quadrance, packed `{P[31:0],Q[31:0]}` |
| 32 | 8 | second quadrance, same packing |
| 40 | 8 | component-wise confidence gap `second - best`, same packing |
| 48 | 4 | IEEE CRC-32 over bytes 0 through 47 |

`P` is an unsigned 32-bit coefficient for the non-negative distance path. `Q`
is a signed two's-complement 32-bit coefficient. Together they represent
`P + Q*sqrt(3)`; consumers must use exact field ordering rather than comparing
the packed integer lexicographically.

### Flags

| Bit | Meaning |
|---:|---|
| 0 | result valid |
| 1 | classifier busy |
| 2 | runner-up present |
| 3 | ambiguous: exact confidence gap is zero in the v1 sidecar |
| 4 | map valid: one complete hydration generation is active |
| 7:5 | reserved, zero |

### Errors

| Code | Meaning |
|---:|---|
| 0 | no error |
| 1 | map incomplete: hydration began but not all 35 records arrived |
| 2 | no runner-up was produced |

Unknown nonzero codes must be preserved and reported by consumers rather than
silently treated as success.

## Generation and hydration rules

Generation zero denotes the map compiled into the bitstream. The first valid
prototype or semantic-label write starts a new hydration generation and clears
`map_valid`. A generation becomes active only after all 28 distinct prototype
addresses and all seven semantic-label addresses have been written. At that
point `map_generation` increments and `map_valid` asserts.

`result_generation` increments on every completed BMU scan. It allows a host to
detect stale, duplicated, or skipped observations independently of map changes.

Prototype writes remain `sel=4`, feature writes `sel=5`, and classify remains
`sel=6` under command `0xA5`. `sel=7` writes one semantic label with node in
`addr[2:0]` and the unsigned 16-bit label in `data[15:0]`.

## Integrity and timing

The encoder calculates the CRC byte-serially in 48 FPGA clocks after BMU
completion. A direct SPI master must wait at least 48 system clocks after the
legacy done indication before requesting the new generation. The RP2350
console's turnaround delay is already longer than this interval.

The parser rejects bad magic, version, declared length, reserved fields, and
CRC. A structurally valid frame with a nonzero error remains parseable evidence;
the application decides whether that classification is admissible.

## Tang 25K build evidence

The 2026-07-17 OSS CAD Suite build completed synthesis, place-and-route, and
packing at 14,068/23,040 LUT4 (61%), 3,251/23,040 DFF (14%), and 8/56 BSRAM
(14%). The routed maximum frequency was 75.79 MHz against the 50 MHz constraint.
The generated bitstream SHA-256 is
`8753c4924ed6952c049a038a80cbe3bfb8b930e038842631665108af4ad1ff92`.
This is build evidence only; the image has not yet been exercised on the board.
