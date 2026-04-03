// rp2350_spu_interface.c (v1.0 - Laminar Controller)
// Target:  Raspberry Pi Pico 2 (RP2350, 150 MHz)
// Role:    Laminar Controller — bridges Tang Primer 25K FPGA to RP2040 visualiser.
//
// Architecture (dual-core):
//   Core 1 — SPU poller:  SPI0 → FPGA at ~1 kHz; assembles 104-byte manifold frame.
//   Core 0 — TX arbiter:  UART1 → RP2040 at 921600 baud; double-buffered swap.
//
// PIO SM0 — Piranha Pulse: 61.44 kHz heartbeat on GP6, phase-locked to FPGA clock.
//
// Connections:
//   SPI0  MISO GP16, CS GP17, SCK GP18, MOSI GP19   (→ Tang 25K SPI slave)
//   UART1 TX   GP4                                   (→ RP2040 UART0 RX, 921600)
//   PIO        GP6                                   (Piranha Pulse out to FPGA)
//
// SPU Sovereign SPI Protocol v1.0 (Mode 0, CPOL=0 CPHA=0, 2 MHz):
//   CMD 0xA0 → read 4-axis manifold burst, response 32 bytes:
//              4 axes × 8 bytes = [{P_hi, P_lo, 0, 0, Q_hi, Q_lo, 0, 0}, ...]
//              P, Q are signed int16 in Q12 fixed-point, big-endian.
//   CMD 0xAC → read status word, response 3 bytes:
//              [dissonance_hi, dissonance_lo, flags]
//              flags bit 0 = snap_lock, bit 1 = janus_stable
//
// Frame format to RP2040 (104 bytes, raw, no header):
//   13 axes × 8 bytes = [{P_hi, P_lo, 0, 0, Q_hi, Q_lo, 0, 0}, ...]
//   Axes 0–3: live SPU-4 ABCD manifold (from SPI read).
//   Axes 4–11: identity (P=0x1000 Q12=1.0, Q=0) — placeholder for SPU-13 axes.
//   Axis 12: status word (P = dissonance, Q = flags packed as int16).
//
// Frame rate: limited by UART bandwidth.
//   104 bytes × 10 bits/byte / 921600 baud = ~1.13 ms/frame → ~885 Hz max.
//   SPI poll at 1 kHz; UART TX throttled to ~800 Hz (sleep_us(250) per loop).
//
// CC0 1.0 Universal.

#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/uart.h"
#include "hardware/pio.h"
#include "pico/multicore.h"
#include "spu_bio_resonance.pio.h"
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// ── Pin assignments ────────────────────────────────────────────────────────
#define SPI_MISO_PIN    16
#define SPI_CS_PIN      17
#define SPI_SCK_PIN     18
#define SPI_MOSI_PIN    19
#define VIS_UART_TX_PIN  4
#define PIRANHA_PIN      6

// ── Peripherals ───────────────────────────────────────────────────────────
#define SPI_PORT        spi0
#define SPI_BAUD_HZ     2000000   // 2 MHz SPI clock
#define VIS_UART        uart1
#define VIS_BAUD        921600

// ── Frame dimensions ──────────────────────────────────────────────────────
#define AXES            13
#define BYTES_PER_AXIS   8
#define FRAME_BYTES     (AXES * BYTES_PER_AXIS)   // 104

// ── SPI commands ──────────────────────────────────────────────────────────
#define CMD_READ_MANIFOLD   0xA0   // → 32 bytes (4 axes × 8 bytes)
#define CMD_READ_STATUS     0xAC   // → 3 bytes  (dissonance[15:8], [7:0], flags)
#define SPU4_AXES            4     // axes returned by CMD_READ_MANIFOLD

// Q12 identity value: 1.0 in Q12 = 0x1000 = 4096
#define Q12_UNITY    0x1000

// ── Double buffer ─────────────────────────────────────────────────────────
static volatile uint8_t  frame_back[FRAME_BYTES];
static volatile uint8_t  frame_front[FRAME_BYTES];
static volatile bool     frame_ready = false;

// ── Forward declarations ──────────────────────────────────────────────────
static void     spi_read_manifold(uint8_t *out32);
static void     spi_read_status(uint16_t *dissonance, uint8_t *flags);
static void     assemble_frame(const uint8_t *abcd32,
                                uint16_t dissonance, uint8_t flags,
                                volatile uint8_t *frame);
static void     pio_piranha_init(void);

// ── Core 1: SPU poller ────────────────────────────────────────────────────
// Runs at ~1 kHz: poll FPGA, assemble frame, signal Core 0.
void core1_spu_poller(void) {
    uint8_t  abcd32[SPU4_AXES * BYTES_PER_AXIS];
    uint16_t dissonance;
    uint8_t  flags;

    while (true) {
        spi_read_manifold(abcd32);
        spi_read_status(&dissonance, &flags);
        assemble_frame(abcd32, dissonance, flags, frame_back);
        frame_ready = true;
        sleep_us(1000);   // ~1 kHz poll; UART TX is the real rate limiter
    }
}

// ── Main (Core 0: TX arbiter) ─────────────────────────────────────────────
int main(void) {
    stdio_init_all();

    // UART1 → RP2040 visualiser (GP4)
    uart_init(VIS_UART, VIS_BAUD);
    gpio_set_function(VIS_UART_TX_PIN, GPIO_FUNC_UART);

    // SPI0 → Tang 25K FPGA (Mode 0, CS active-low)
    spi_init(SPI_PORT, SPI_BAUD_HZ);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPI_SCK_PIN,  GPIO_FUNC_SPI);
    gpio_set_function(SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MISO_PIN, GPIO_FUNC_SPI);
    gpio_init(SPI_CS_PIN);
    gpio_set_dir(SPI_CS_PIN, GPIO_OUT);
    gpio_put(SPI_CS_PIN, 1);   // CS idle-high

    // PIO SM0: Piranha Pulse (61.44 kHz) on GP6
    pio_piranha_init();

    // Launch Core 1 poller
    multicore_launch_core1(core1_spu_poller);

    // Core 0: transmit loop
    while (true) {
        if (frame_ready) {
            memcpy((void *)frame_front, (void *)frame_back, FRAME_BYTES);
            frame_ready = false;
            uart_write_blocking(VIS_UART,
                                (const uint8_t *)frame_front,
                                FRAME_BYTES);
        }
        sleep_us(250);   // ~4000 Hz check; UART throttles actual rate
    }
}

// ── SPI helpers ───────────────────────────────────────────────────────────

// Read 4-axis manifold burst: sends CMD 0xA0, reads 32 bytes.
// out32 layout: 4 × [{P_hi, P_lo, 0, 0, Q_hi, Q_lo, 0, 0}]
static void spi_read_manifold(uint8_t *out32) {
    uint8_t cmd = CMD_READ_MANIFOLD;
    static const uint8_t dummy[SPU4_AXES * BYTES_PER_AXIS] = {0};

    gpio_put(SPI_CS_PIN, 0);
    spi_write_blocking(SPI_PORT, &cmd, 1);
    spi_read_blocking(SPI_PORT, 0x00, out32, SPU4_AXES * BYTES_PER_AXIS);
    gpio_put(SPI_CS_PIN, 1);
    (void)dummy;
}

// Read status word: sends CMD 0xAC, reads 3 bytes.
static void spi_read_status(uint16_t *dissonance, uint8_t *flags) {
    uint8_t cmd = CMD_READ_STATUS;
    uint8_t resp[3] = {0};

    gpio_put(SPI_CS_PIN, 0);
    spi_write_blocking(SPI_PORT, &cmd, 1);
    spi_read_blocking(SPI_PORT, 0x00, resp, 3);
    gpio_put(SPI_CS_PIN, 1);

    *dissonance = ((uint16_t)resp[0] << 8) | resp[1];
    *flags      = resp[2];
}

// ── Frame assembly ────────────────────────────────────────────────────────
// Layout (104 bytes):
//   Axes 0–3:  live SPU-4 ABCD (copied from abcd32)
//   Axes 4–11: identity manifold  {P=Q12_UNITY, Q=0}
//   Axis 12:   status             {P=dissonance, Q=flags as int16}
static void assemble_frame(const uint8_t *abcd32,
                            uint16_t dissonance, uint8_t flags,
                            volatile uint8_t *frame) {
    // Zero entire frame first (clears reserved bytes cleanly)
    memset((void *)frame, 0, FRAME_BYTES);

    // Axes 0–3: copy directly from SPI burst (already in correct 8-byte format)
    memcpy((void *)frame, abcd32, SPU4_AXES * BYTES_PER_AXIS);

    // Axes 4–11: identity — rational part = Q12_UNITY (1.0 in Q12), surd = 0
    for (int i = SPU4_AXES; i < AXES - 1; i++) {
        int off = i * BYTES_PER_AXIS;
        frame[off + 0] = (Q12_UNITY >> 8) & 0xFF;
        frame[off + 1] =  Q12_UNITY       & 0xFF;
        // bytes 2–7 already zero
    }

    // Axis 12: status word
    int off = 12 * BYTES_PER_AXIS;
    frame[off + 0] = (dissonance >> 8) & 0xFF;
    frame[off + 1] =  dissonance       & 0xFF;
    frame[off + 4] = 0x00;
    frame[off + 5] = flags;   // flags in surd byte so display highlights it
}

// ── PIO: Piranha Pulse ────────────────────────────────────────────────────
// Loads piranha_pulse program from spu_bio_resonance.pio.h onto PIO0 SM0.
static void pio_piranha_init(void) {
    PIO  pio    = pio0;
    uint sm     = 0;
    uint offset = pio_add_program(pio, &piranha_pulse_program);
    piranha_pulse_program_init(pio, sm, offset, PIRANHA_PIN);
}
