#ifndef SPU4_INTRINSICS_H
#define SPU4_INTRINSICS_H

#include <stdint.h>

/**
 * @typedef q4_vector
 * @brief 4D± Quadray Vector (A, B, C, D)
 * Each component is a 16-bit Q8.8 fixed-point rational.
 */
typedef struct {
    int16_t a;
    int16_t b;
    int16_t c;
    int16_t d;
} q4_vector;

/**
 * @brief Quadray Add (0x40)
 * Sum two 4D vectors in a single-cycle manifold addition.
 */
static inline q4_vector spu_qadd(q4_vector v1, q4_vector v2) {
    q4_vector result;
    __asm__ volatile ("qadd %0, %1, %2" : "=r"(result) : "r"(v1), "r"(v2));
    return result;
}

/**
 * @brief Rational Rotation (0x45)
 * Rotate a 4D vector by the internal Thomson Prime manifold.
 * Maintains Magnitude Integrity (No drift).
 */
static inline q4_vector spu_qrot(q4_vector v) {
    q4_vector result;
    __asm__ volatile ("qrot %0, %1" : "=r"(result) : "r"(v));
    return result;
}

/**
 * @brief Assert 15-Sigma Snap (0x80)
 * Stall the pipeline until the rational field closure is verified.
 */
static inline void spu_snap() {
    __asm__ volatile ("snap" : : : "memory");
}

/**
 * @brief Whisper 60° Transmit (0xA0)
 * Broadcast the 4D state over the dual-wire bio-resonant bus.
 */
static inline void spu_whisper(q4_vector v) {
    __asm__ volatile ("whisper %0" : : "r"(v));
}

#endif // SPU4_INTRINSICS_H
