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

/**
 * @brief RPLU POLY_STEP intrinsic (emit a single Horner step command to RPLU)
 * @param idx coefficient index (0..4)
 */
static inline void spu_rplu_poly_step(int idx) {
    __asm__ volatile ("rplu_poly_step %0" : : "r"(idx));
}


/**
 * @brief POLY_STEP intrinsic (assemble: POLY_STEP)
 * POLY_STEP Rbase, Rx — evaluate Padé P(x)/Q(x) in hardware. Rbase receives P (numer)
 * Rbase+1 receives Q (den). Rx supplies x as signed integer (Q32) in its .a field.
 */
static inline void spu_poly_step(int rbase, int rx) {
    __asm__ volatile ("polystep %0, %1" : : "r"(rbase), "r"(rx));
}

/**
 * @brief RATIO_CMP intrinsic (assemble: RATIO_CMP)
 * RATIO_CMP Rbase, Rcompare — compare P/Q against compare ratio using cross-multiplication.
 * Returns comparison result in integer register (asm-dependent).  (Stubbed)
 */
static inline int spu_ratio_cmp(int rbase, int rcompare) {
    int out = 0;
    __asm__ volatile ("ratio_cmp %0, %1, %2" : "=r"(out) : "r"(rbase), "r"(rcompare));
    return out;
}

#endif // SPU4_INTRINSICS_H
