// spu_isa_defines.vh — SPU-13 Instruction Set Architecture v1.0
// Opcode constants and instruction format definitions.
// Include in any module that decodes or dispatches SPU-13 instructions.

// ──────────────────────────────────────────────────────────────────────────────
// Opcode Width and Register Count
// ──────────────────────────────────────────────────────────────────────────────
`ifndef SPU_ISA_DEFINES_VH
`define SPU_ISA_DEFINES_VH

`define SPU_OPCODE_WIDTH      8
`define SPU_REG_ADDR_WIDTH    5       // 32 registers
`define SPU_REG_COUNT         32
`define SPU_NUM_AXES          13      // Full SPU-13
`define SPU_NUM_AXES_SENTINEL  4      // SPU-4 compact

// ──────────────────────────────────────────────────────────────────────────────
// Instruction Format Field Positions (within 64-bit instruction word)
// ──────────────────────────────────────────────────────────────────────────────
// Universal: opcode always at [63:56]
`define SPU_FIELD_OPCODE     63:56

// Format R (Register 3-op): arithmetic / geometric / temporal
`define SPU_R_DEST           55:51
`define SPU_R_SRCA           50:46
`define SPU_R_SRCB           45:41

// Format L (Load/Store): memory access with offset
`define SPU_L_DEST           55:51
`define SPU_L_BASE           50:46
`define SPU_L_OFFSET         45:36       // signed 10-bit

// Format I (Immediate): 51-bit constant
`define SPU_I_DEST           55:51
`define SPU_I_IMM            50:0        // 51-bit unsigned

// Format U (Unary): single source + condition
`define SPU_U_DEST           55:51
`define SPU_U_SRC            50:46
`define SPU_U_COND           45:44

// Format B (Branch): offset
`define SPU_B_FLAGS          55:51
`define SPU_B_OFFSET         50:0        // 51-bit signed

// ──────────────────────────────────────────────────────────────────────────────
// Condition Codes (Format U)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_COND_ALWAYS      2'b00
`define SPU_COND_COHERENT    2'b01       // Execute if phase-lock coherent
`define SPU_COND_NOTCOH      2'b10       // Execute if phase-lock NOT coherent
`define SPU_COND_RESERVED    2'b11

// ──────────────────────────────────────────────────────────────────────────────
// System & Control (0x00–0x0F)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_OP_NOP           8'h00
`define SPU_OP_HALT          8'h01
`define SPU_OP_SYNC          8'h02

// ──────────────────────────────────────────────────────────────────────────────
// Data Movement (0x10–0x1F)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_OP_LOAD          8'h10
`define SPU_OP_STORE         8'h11
`define SPU_OP_MOV           8'h12
`define SPU_OP_MOVI          8'h13
`define SPU_OP_LDO           8'h14       // Load to Offer slot only
`define SPU_OP_LDC           8'h15       // Load to Confirmation slot only
`define SPU_OP_MOV_O         8'h16       // Copy .O slot to .O
`define SPU_OP_MOV_C         8'h17       // Copy .C slot to .O

// ──────────────────────────────────────────────────────────────────────────────
// Quadrance Arithmetic (0x20–0x2F)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_OP_QADD          8'h20
`define SPU_OP_QSUB          8'h21
`define SPU_OP_QMUL          8'h22
`define SPU_OP_QDIV          8'h23
`define SPU_OP_QNORM         8'h24       // Reduce fraction
`define SPU_OP_QCMP          8'h25       // Compare quadrances
`define SPU_OP_SOM           8'h2A       // SOM classify (PHSLK vs RPLU material)
`define SPU_OP_SOM_TRAIN     8'h2B       // SOM train (update RPLU weights)

// ──────────────────────────────────────────────────────────────────────────────
// Geometric Operations (0x30–0x3F)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_OP_SPRD          8'h30       // Calculate spread
`define SPU_OP_ROTR          8'h31       // Apply spread-rotor
`define SPU_OP_CROSS         8'h32       // Quadray cross product
`define SPU_OP_DOT           8'h33       // Quadray dot product
`define SPU_OP_TNSR          8'h34       // Apply metric tensor M=4I-J
`define SPU_OP_PROJ          8'h35       // Project B onto A

// ──────────────────────────────────────────────────────────────────────────────
// Bidirectional / Temporal Operations (0x40–0x4F)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_OP_OFFR          8'h40       // Load Offer wave (past boundary)
`define SPU_OP_CNFM          8'h41       // Load Confirmation wave (future boundary)
`define SPU_OP_PHSLK         8'h42       // Phase-lock: solve Offer ∩ Confirmation
`define SPU_OP_INVJ          8'h43       // Invert through Janus point
`define SPU_OP_PHSTA         8'h44       // Read phase-lock status
`define SPU_OP_PHCLR         8'h45       // Clear phase-lock status
`define SPU_OP_NSA_DQADD      8'h46       // NSA dual quadrance add over F_{p^4}[epsilon]
`define SPU_OP_NSA_DQMUL      8'h47       // NSA dual quadrance multiply over F_{p^4}[epsilon]

// ──────────────────────────────────────────────────────────────────────────────
// RPLU Configuration (0x50–0x5F)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_OP_RCFG          8'h50       // Write RPLU config record
`define SPU_OP_RREAD         8'h51       // Read RPLU config record
`define SPU_OP_RLOAD         8'h52       // Burst load RPLU table from memory
`define SPU_OP_RDISSOC       8'h53       // Read RPLU dissociation table

// ──────────────────────────────────────────────────────────────────────────────
// Flow Control (0x60–0x6F)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_OP_CMP           8'h60       // Compare, set flags
`define SPU_OP_JMP           8'h61       // Unconditional jump
`define SPU_OP_JZ            8'h62       // Jump if zero flag
`define SPU_OP_JNZ           8'h63       // Jump if not zero
`define SPU_OP_JC            8'h64       // Jump if coherent
`define SPU_OP_JNC           8'h65       // Jump if not coherent
`define SPU_OP_CALL          8'h66       // Call subroutine
`define SPU_OP_RET           8'h67       // Return from subroutine
`define SPU_OP_IRET          8'h68       // Return from interrupt

// ──────────────────────────────────────────────────────────────────────────────
// Telemetry / Output (0x70–0x7F)
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_OP_MFOLD         8'h70       // Emit manifold to SPI output
`define SPU_OP_STAT          8'h71       // Emit status to SPI output
`define SPU_OP_SCALE         8'h72       // Emit scale table to SPI output
`define SPU_OP_QR            8'h73       // Emit QR commit registers
`define SPU_OP_HEX           8'h74       // Emit hex (q,r) to output
`define SPU_OP_SENT          8'h75       // Emit sentinel telemetry burst
`define SPU_OP_CHRDOUT       8'h76       // Output chord to SPI master

// ──────────────────────────────────────────────────────────────────────────────
// Special Register Indices
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_REG_ZERO         5'd0        // Always zero
`define SPU_REG_PC           5'd1        // Program counter
`define SPU_REG_FLAGS        5'd2        // Status flags: Z=bit0, C=bit1, S=bit2
`define SPU_REG_MANIFOLD_PTR 5'd3        // Manifold read pointer
`define SPU_REG_SCALE_PTR    5'd4        // Scale table index
`define SPU_REG_CHORD_IN     5'd5        // Incoming chord (read-only)
`define SPU_REG_CHORD_OUT    5'd6        // Outgoing chord (write-only)
`define SPU_REG_QUAD_OUT     5'd7        // Quadrance output (read-only)

// ──────────────────────────────────────────────────────────────────────────────
// Flags Register Bit Positions
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_FLAG_ZERO        0           // Zero result
`define SPU_FLAG_COHERENT    1           // Phase-lock coherent
`define SPU_FLAG_SCALE_OVF   2           // Scale overflow
`define SPU_FLAG_FIFO_FULL   3           // Instr FIFO full (SPI flow control)

// ──────────────────────────────────────────────────────────────────────────────
// Memory Map Constants
// ──────────────────────────────────────────────────────────────────────────────
`define SPU_MEM_RPLU_BASE    12'h000     // RPLU config table: 512 × 64-bit
`define SPU_MEM_RPLU_SIZE    512
`define SPU_MEM_SCALE_BASE   12'h200     // Spread LUT: 257 entries
`define SPU_MEM_SCALE_SIZE   257
`define SPU_MEM_UCROM_BASE   12'h300     // Microcode ROM: 256 instructions
`define SPU_MEM_UCROM_SIZE   256
`define SPU_MEM_PELL_BASE    12'h400     // Pell cache
`define SPU_MEM_BOOT_BASE    12'h500     // Boot parameters
`define SPU_MEM_SCRATCH      12'h800     // Scratch: 2K

// ──────────────────────────────────────────────────────────────────────────────
// Quadray / Rational Type Helpers
// ──────────────────────────────────────────────────────────────────────────────
`define QUADRAY_WIDTH        64
`define QUADRAY_A            63:48
`define QUADRAY_B            47:32
`define QUADRAY_C            31:16
`define QUADRAY_D            15:0

`define RATIONAL_WIDTH       64
`define RATIONAL_NUM         63:32
`define RATIONAL_DEN         31:0

`endif // SPU_ISA_DEFINES_VH
