# Tensegrity Balancer Table ABI (TGR1)

TGR1 is the versioned binary contract shared by the exact Python oracle, the
FPGA sidecar's double-buffered BRAM image, and the southbridge transport.
It is deliberately **not an SPU opcode or assembler syntax**. The first
hardware-in-the-loop path uses new optional southbridge opcodes alongside the
existing frozen base commands; no earlier opcode format changed.

## Scope and boundary

- TGR1 records topology and exact `Z[phi]` node coordinates; all coefficients
  are signed 32-bit integers. Fractional `Q(phi)` fixtures are rejected rather
  than rounded.
- TGR1 validates transport integrity and representation only. Mechanical
  admissibility remains the oracle/sidecar guard evaluator's responsibility.
- The current core QR file is not the TGR1 store. The sidecar owns two raw
  508-byte banks in one RAMB18E1: one active and one transactional staging
  bank.

## Table layout (big-endian)

| Offset | Bytes | Field |
|---|---:|---|
| 0 | 4 | ASCII magic `TGR1` |
| 4 | 1 | ABI version: `1` |
| 5 | 1 | node count |
| 6 | 1 | edge count |
| 7 | 1 | flags, must be zero |
| 8 | 4 | CRC-32 of the payload |
| 12 | 28 × N | nodes |
| … | 4 × E | edges |

Each node stores six signed 32-bit words `x.a, x.b, y.a, y.b, z.a, z.b`,
representing each coordinate as `a + bφ`, followed by a one-byte grid state
(`UNTAGGED=0`, `MAIN=1`, `CONJ=2`) and three zero pad bytes. Each edge stores
`node_a`, `node_b`, `edge_type` (`CABLE=0`, `STRUT=1`, `GAP=2`), and one zero
reserved byte.

The canonical six-strut fixture is exactly 468 bytes: 12-byte header, twelve
28-byte nodes, and thirty 4-byte edges. The bounded RTL accepts at most 12
nodes and 40 edges, so 508 bytes is the largest legal TGR1 image.

## Status layout

The sidecar status record is exactly eight bytes:

```text
byte 0 ABI version       byte 1 balancer state
byte 2 terminal fault    byte 3 reserved = 0
bytes 4..7 vector id (big-endian uint32)
```

The first eight bytes of `0xB3` are exactly this record. `0xB3` then appends
eight bytes of diagnostics without altering the frozen prefix:

```text
byte 8 flags: bit3 active-valid, bit2 verify-busy, bit1 RX-busy,
              bit0 error-present
byte 9 loader error
byte 10 active node count       byte 11 active edge count
bytes 12..13 last received      bytes 14..15 last expected
```

Loader errors are `0=NONE`, `1=TRANSPORT`, `2=MAGIC`, `3=VERSION`,
`4=FLAGS`, `5=BOUNDS`, `6=LENGTH`, `7=CRC32`, `8=NODE`, and `9=EDGE`.

## Southbridge transport

`0xB2` is one transactional load under a single CS# assertion:

```text
B2 | length:uint16 | vector_id:uint32 | exact TGR1 bytes | CRC-8-CCITT
```

All multi-byte fields are big-endian. The CRC-8 covers the command, prefix,
and table. The table's own CRC-32 independently covers its payload. A valid
transport is parsed from the inactive BRAM bank and replayed synchronously
through the guard. Only a coherent terminal guard result switches the active
bank. Transport aborts, either CRC failure, malformed records, and count or
length violations leave the previous active table and status untouched while
recording the staging error in the diagnostic suffix.

`0xB3` reads the 16-byte status above. These opcodes are optional and appear
only when `spu_spi_slave.v` is built with `ENABLE_TENSEGRITY=1`; unsupported
base-v1 images retain the standard one-byte-zero unknown-command response.

## Golden corpus

`tools/gen_tensegrity_vectors.py` emits the first probe corpus. Vector IDs
`0..6` are frozen in this order: canonical balanced, topology, strut collision,
cable slack, strut intersection, grid mismatch, and not-in-equilibrium. Each
fixture has a `.tgr` table and an eight-byte `.status` golden response; the
manifest records both exact names and expected terminal verdict. The oracle
test `software/tests/test_tensegrity_vectors.py` pins this ordering before RTL
or southbridge work may rely on it.

The first Artix admission probe exercised five fixtures: IDs 0, 1, 2, 3, and
5, reporting `TGR:P V:5 E:00`. The second RTL tranche added ID 4's exact
closed-segment strut-contact predicate and produced `TGR:P V:6 E:00` in
silicon after IDs 0 through 5 completed. The final admission tranche adds an
exact type-uniform Z[phi] equilibrium predicate and feeds ID 6 to the guard;
the packed V:7 wrapper reports `TGR:P V:7 E:00` only after all IDs 0 through 6
match their state/fault pairs. In every line, `V` is the completed-fixture
count, not a vector ID. The V:7 image produced that verdict in Wukong Artix-7
silicon on 2026-07-14.

The hardware equilibrium contract is deliberately bounded: all cable/GAP
members share one density and all struts share another. It derives their exact
ratio and sign rather than hard-coding the canonical `2:-3` result. The Python
oracle first tries this same symmetric solution, then may search a small
per-edge nullspace; therefore an oracle-only nonuniform self-stress is not yet
licensed for acceptance by the RTL guard.

## ISA / assembler decision

No new SPU ISA opcode or assembler keyword is introduced by TGR1. Add a
dedicated `TGR_CONFIG` / `TGR_VERIFY` instruction family only if profiling
shows that instruction-sequenced core access, rather than a sidecar command
path, is required for deterministic latency. At that point the instruction
format, VM semantics, assembler, RTL decoder, and tests must land together.
