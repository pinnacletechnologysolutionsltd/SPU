// spu_lithic.h
// Lithic-C: The "Sovereign" Intermediate Language for SPU-13/4 Clusters.
// Expansion: Sovereign Cluster System API & Memory Map.

#ifndef SPU_LITHIC_H
#define SPU_LITHIC_H

#include <stdint.h>

/** 
 * MEMORY MAP (Crystalline Layout)
 * Mapping the Artery FIFO and Manifold Status for Ghost OS (RP2040).
 */
#define SPU_ARTERY_BASE       0x50000000 // PIO-Mapped FIFO address (Write-only)
#define SPU_STATUS_BASE       0x50000008 // Manifold telemetry address (Read-only)

/** 
 * SOVEREIGN BOOT MEMORY MAP (SPI Flash / PMOD)
 * Map for Ghost OS and 13-axis Thomson Primes.
 */
#define FLASH_OS_BASE         0x00000000 // Ghost OS code in SPI Flash
#define FLASH_PRIME_BASE      0x00100000 // Thomson Primes (bloom.bin) @ 1MB offset
#define SPU_BOOT_CTRL         0x5000000C // Control register for Flash/PMOD

/** 
 * RationalSurd: Fixed-point representation in Q(sqrt3)
 * Q8.8 format: 16-bit P (Rational), 16-bit Q (Surd)
 */
struct RationalSurd {
    int16_t p; // Rational component
    int16_t q; // Surd component (coefficient of sqrt(3))

    RationalSurd(int16_t _p = 0, int16_t _q = 0) : p(_p), q(_q) {}
};

struct Chord {
    RationalSurd a, b, c, d;
    Chord() : a(0,0), b(0,0), c(0,0), d(0,0) {}
};

/** 
 * Artery Protocol: Hydration & Inhale
 * Ghost OS (133 MHz) streams Chords to the 64-deep FIFO buffer.
 */
inline void manifold_hydrate(Chord c) {
    volatile uint64_t* fifo = (volatile uint64_t*)SPU_ARTERY_BASE;
    uint64_t raw = (uint64_t(uint16_t(c.a.p)) << 48) | (uint64_t(uint16_t(c.b.p)) << 32) |
                    (uint64_t(uint16_t(c.c.p)) << 16) | (uint64_t(uint16_t(c.d.p)) << 0);
    *fifo = raw;
}

/**
 * @brief Triggers the SPU-13 PMOD Prime Loader.
 * Ingests 13-axis Thomson matrices to seed the manifold basis.
 */
inline void manifold_load_primes() {
    volatile uint32_t* ctrl = (volatile uint32_t*)SPU_BOOT_CTRL;
    *ctrl = 0x01; // Trigger PMOD Load
    // Wait for bit-exact 'Crystalline' state (bit 1)
    while(!(*ctrl & 0x02)); 
}

/** 
 * Sovereign Status Monitoring: The Janus Bit
 * Returns true if the manifold is stable (Davis Law Gasket PASS).
 * Returns false if Over-Curvature or Cubic Noise is detected.
 */
inline bool manifold_is_stable() {
    volatile uint32_t* status = (volatile uint32_t*)SPU_STATUS_BASE;
    // Status Register [0] : is_janus_point (1 = stable/pass)
    // Actually, in hardware, is_janus_point usually signals identity, 
    // but here we map it to 'Gasket PASS' bit.
    return (*status & 0x01);
}

/** 
 * System Intrinsics
 */
#define SPU_AXIS_SHIFT(n) (n & 0x0F) // 4-bit Opcode for circulant rotation
#define SPU_SNAP_ALL()     0x80      // Global high-sigma capture

/** 
 * Manifold: The 13-axis Sovereign State.
 */
struct Manifold13 {
    Chord axes[13];
};

#endif // SPU_LITHIC_H
