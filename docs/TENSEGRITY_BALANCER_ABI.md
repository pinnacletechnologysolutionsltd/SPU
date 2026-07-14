# Tensegrity Balancer Table ABI (TGR1)

TGR1 is the versioned binary contract shared by the exact Python oracle, a
future FPGA sidecar BRAM image, and a future southbridge transport command.
It is deliberately **not an SPU opcode or assembler syntax**. The first
hardware-in-the-loop experiment must use this table alongside the existing
southbridge contract without changing its frozen opcodes.

## Scope and boundary

- TGR1 records topology and exact `Z[phi]` node coordinates; all coefficients
  are signed 32-bit integers. Fractional `Q(phi)` fixtures are rejected rather
  than rounded.
- TGR1 validates transport integrity and representation only. Mechanical
  admissibility remains the oracle/sidecar guard evaluator's responsibility.
- The current core QR file is not the TGR1 store. A canonical fixture has 12
  three-coordinate nodes plus 30 edges, so a future sidecar owns node/edge
  BRAM.

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
28-byte nodes, and thirty 4-byte edges.

## Status layout

The sidecar status record is exactly eight bytes:

```text
byte 0 ABI version       byte 1 balancer state
byte 2 terminal fault    byte 3 reserved = 0
bytes 4..7 vector id (big-endian uint32)
```

This is sufficient for the first BRAM/golden-vector probe. It does not yet
reserve a southbridge command byte. A transport extension requires a new SPI
opcode outside the frozen `0xA0–0xB1` allocation, an RTL/firmware/oracle
update, and a compatibility test.

## Golden corpus

`tools/gen_tensegrity_vectors.py` emits the first probe corpus. Vector IDs
`0..6` are frozen in this order: canonical balanced, topology, strut collision,
cable slack, strut intersection, grid mismatch, and not-in-equilibrium. Each
fixture has a `.tgr` table and an eight-byte `.status` golden response; the
manifest records both exact names and expected terminal verdict. The oracle
test `software/tests/test_tensegrity_vectors.py` pins this ordering before RTL
or southbridge work may rely on it.

The first Artix admission probe exercised five fixtures: IDs 0, 1, 2, 3, and
5, reporting `TGR:P V:5 E:00`. The second RTL tranche adds ID 4's exact
closed-segment strut-contact predicate and reports `TGR:P V:6 E:00` after IDs
0 through 5 have completed. In both lines, `V` is the completed-fixture count,
not a vector ID. ID 6 (force-density equilibrium) remains oracle-only and is
never fed to the bounded guard as if it could classify it.

## ISA / assembler decision

No new SPU ISA opcode or assembler keyword is introduced by TGR1. Add a
dedicated `TGR_CONFIG` / `TGR_VERIFY` instruction family only if profiling
shows that instruction-sequenced core access, rather than a sidecar command
path, is required for deterministic latency. At that point the instruction
format, VM semantics, assembler, RTL decoder, and tests must land together.
