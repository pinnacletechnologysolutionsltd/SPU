// spu_lithic_l.h (v1.0 - Sentinel Autonomy)
// Lithic-L Lite: 16-bit Instruction Set for SPU-4 Euclidean Ganglia.

#ifndef SPU_LITHIC_L_H
#define SPU_LITHIC_L_H

#include <stdint.h>

/**
 * INSTRUCTION FORMAT (16-bit)
 * [15:12] Opcode
 * [11]    HUSH (Clock Gating) 
 * [10:8]  Immediate / Modifier
 * [7:0]   Address / Payload
 */

// Opcodes
#define L_OP_NOP      0x0
#define L_OP_LOAD_ABC 0x1 // Load initial state from buffer address
#define L_OP_ROTATE   0x2 // Trigger ALU
#define L_OP_GOTO     0x3 // Jump PC 
#define L_OP_WHISPER  0x4 // Push current state to PWI
#define L_OP_HUSH     0x5 // Deprecated (now bit 11)
#define L_OP_BUS_W    0x6 // Write to SovereignBus (addr in [7:0])
#define L_OP_BUS_R    0x7 // Read from SovereignBus
#define L_OP_RAM_ADDR 0x8 // RAM_SET_ADDR — payload is 8 MSBs of 23-bit ptr
#define L_OP_RAM_FETCH 0x9 // RAM_FETCH — load 16-bit word into A register

// Flags
#define L_FLAG_HUSH   (1 << 11)

/**
 * @brief Encodes a 16-bit Lithic-L instruction with optional HUSH flag.
 */
constexpr uint16_t lithic_l_encode(uint8_t opcode, bool hush, uint8_t imm, uint8_t payload) {
    return (uint16_t(opcode & 0xF) << 12) | 
           (hush ? L_FLAG_HUSH : 0) |
           (uint16_t(imm & 0x7) << 8) | 
           (uint16_t(payload));
}

/**
 * @brief Sample 'Dream' Program (The Jitterbug Morph)
 * Step 0: Rotate 45deg
 * Step 1: Whisper State
 * Step 2: Loop to 0
 */
static const uint16_t JITTERBUG_DREAM[] = {
    0x2000, // ROTATE
    0x4000, // WHISPER
    0x3000  // GOTO 0
};

#endif // SPU_LITHIC_L_H
