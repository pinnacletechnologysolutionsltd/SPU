// spu_flash_map.vh — W25Q128JVSQ (16MB) Address Map
// AUTO-CONSISTENT with software/tools/gen_pell_table.py
// All offsets are 24-bit byte addresses.

// ── Boot regions ─────────────────────────────────────────────────────────────
`define FLASH_BITSTREAM_BASE   24'h000000  // FPGA bitstream (~150KB, UP5K)
`define FLASH_FALLBACK_BASE    24'h040000  // Safe Soul fallback bootloader
`define FLASH_GHOST_OS_BASE    24'h080000  // Ghost OS kernel / Lithic-L programs

// ── Rational table region ─────────────────────────────────────────────────────
`define FLASH_TABLE_BASE       24'h100000  // Start of all surd/prime tables

`define FLASH_PELL_BASE        24'h100000  // Pell sequence: 13 × 8 bytes = 104B
`define FLASH_PELL_STRIDE      8           // Bytes per entry: int32 a + int32 b
`define FLASH_PELL_COUNT       13

`define FLASH_GOLDEN_BASE      24'h100100  // Golden Prime LUT: 13 × 4 bytes = 52B
`define FLASH_GOLDEN_STRIDE    4           // Bytes per entry: uint32 prime
`define FLASH_GOLDEN_COUNT     13

`define FLASH_QROT_VEL_BASE    24'h100200  // QROT velocity table (reserved)

// ── World / archive region ────────────────────────────────────────────────────
`define FLASH_BLOOM_BASE       24'h200000  // bloom.bin / IVM Golden Prime bloom
`define FLASH_WORLD_BASE       24'h400000  // Ghost OS world data, Lithic programs
// 0x400000 – 0xFFFFFF: ~12MB free for sovereign archives

// ── Helper: byte address of Pell step n (0..12) ──────────────────────────────
// Usage: addr = `FLASH_PELL_BASE + (n * `FLASH_PELL_STRIDE)
// Gives base of 8-byte record: [3:0]=a (int32 BE), [7:4]=b (int32 BE)
