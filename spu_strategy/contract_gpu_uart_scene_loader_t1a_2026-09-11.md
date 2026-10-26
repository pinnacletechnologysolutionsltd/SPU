# Engineering Contract: Wukong GPU Two-Bank UART Scene Loader T1a

**Date:** 2026-09-11  
**Status:** COMPLETE — T1a-A PASS, 2026-09-11  
**Target:** standalone Wukong GPU control-plane logic

## Objective

Implement and simulate a byte-level two-bank loader that reconstructs exactly
504 scene bits in an inactive bank and exposes the whole scene only at an
abstract `frame_start`. This contract makes no rendered-scene atomicity claim.

## Frozen interface

Inputs: `clk`, active-low `rst_n`, `rx_byte[7:0]`, `rx_valid`, and synchronous
`frame_start`. Outputs: `active_scene[503:0]` and `commit_pending`.
`spu_uart_rx` is not instantiated.

## Frozen packet and packing

- Idle `0xA5` begins a transaction; it is followed by exactly 63 payload bytes.
- Payload byte `i` maps to `scene[8*i +: 8]` for `i=0..62`.
- Triangle 0 is bits `[251:0]`; triangle 1 is `[503:252]`.
- Within each 252-bit record, increasing bit positions contain
  `a0,b0,c0,a1,b1,c1,a2,b2,c2,r,g,b,z0,z1,z2`, with widths
  `16,16,32,16,16,32,16,16,32,4,4,4,16,16,16`.
- Embedded `0xA5` is payload. There is no checksum, timeout, escape, length,
  resynchronizer, FIFO, retransmission, or general command protocol.

## Frozen state semantics

- Reset clears both banks, selects bank 0, and clears receive/count/pending.
- Payload writes target only the inactive bank.
- Byte 63 establishes `commit_pending`; it never activates the bank itself.
- While pending, all bytes are ignored.
- A pending bank activates only on a later edge with `frame_start=1`.
- Byte 63 coincident with `frame_start` completes only; it cannot activate.
- A truncated packet stays incomplete until reset.

## Verification and terminal gate

The self-checking simulation must pass P1/P2 and N1–N6, including two distinct
nontrivial payloads, embedded `0xA5`, pending-byte rejection, exact packing,
truncation, and completion/frame collision. Then run exactly one detached
`bash tools/verify_repo.sh` with a 3,600-second timeout.

Classify T1a-A only if scoped simulation and the repository gate pass. Classify
T1a-D on a reproducible semantic violation, or T1a-E on an inconclusive gate.
Stop after classification. No retry is implicit.

## Prohibited

No GPU/raster/depth/VGA integration, `spu_uart_rx` modification, arithmetic,
extra triangles, protocol expansion, synthesis, P&R, bitstream, physical UART,
FPGA programming, VGA testing, T1b, performance work, or unrelated repair.
