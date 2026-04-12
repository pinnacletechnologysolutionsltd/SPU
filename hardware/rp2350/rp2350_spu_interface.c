// rp2350_spu_interface.c (v2.0 - Laminar Controller)
// Target:  Raspberry Pi Pico 2 (RP2350, 150 MHz)
// Role:    Laminar Controller — bridges Tang Primer 25K FPGA to RP2040 visualiser.
//
// Architecture (dual-core):
//   Core 1 — SPU poller:  SPI0 → FPGA at ~1 kHz; assembles 104-byte manifold frame.
//                         Also receives incoming Chord bytes from RP2040 (UART1 RX)
//                         and forwards them to the FPGA via SPI CMD 0xB1.
//   Core 0 — TX arbiter:  Reads frame from Core 1 via multicore FIFO;
//                         Sends SOF header + 104-byte frame to RP2040 over UART1 TX.
//
// PIO SM0 — Piranha Pulse: 61.44 kHz heartbeat on GP6 (phase-locked to FPGA).
// PIO SM1 — Whisper TX:    PWI 1-wire telemetry on GP7; fires on Cubic Leak events.
//
// Connections:
//   SPI0  MISO GP16, CS GP17, SCK GP18, MOSI GP19   (→ Tang 25K SPI slave)
//   UART1 TX   GP4                                   (→ RP2040 GP5, 921600 baud)
//   UART1 RX   GP5                                   (← RP2040 GP4, Chord passthrough)
//   PIO        GP6                                   (Piranha Pulse out to FPGA)
//   PIO        GP7                                   (Whisper TX PWI out to FPGA)
//
// SPU SPI Protocol v1.1 (Mode 0, CPOL=0 CPHA=0, 2 MHz):
//   CMD 0xA0 → read 4-axis manifold burst, response 32 bytes
//   CMD 0xAC → read status word, response 3 bytes
//   CMD 0xB1 → write 8-byte Chord to FPGA instruction register (execute on next tick)
//
// Frame format to RP2040 (106 bytes = 2 SOF + 104 data):
//   Byte 0:   0xA5  (SOF marker high)
//   Byte 1:   0x5A  (SOF marker low)
//   Bytes 2-105: 13 axes × 8 bytes [{P_hi,P_lo,0,0,Q_hi,Q_lo,0,0}]
//
// SOF framing allows RP2040 and spu_inhale to re-sync after any byte slip.
//
// Frame rate: ~800 Hz (106 bytes × 10 bits / 921600 baud = 1.15 ms; sleep_us(250))
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
#include "rplu_default_tables.h"

// ── Pin assignments ────────────────────────────────────────────────────────
#define SPI_MISO_PIN    16
#define SPI_CS_PIN      17
#define SPI_SCK_PIN     18
#define SPI_MOSI_PIN    19
#define VIS_UART_TX_PIN  4   // UART1 TX → RP2040
#define VIS_UART_RX_PIN  5   // UART1 RX ← RP2040 (Chord passthrough)
#define PIRANHA_PIN      6   // PIO SM0: Piranha Pulse
#define WHISPER_PIN      7   // PIO SM1: Whisper TX

// ── Peripherals ───────────────────────────────────────────────────────────
#define SPI_PORT        spi0
#define SPI_BAUD_HZ     2000000   // 2 MHz SPI clock
#define VIS_UART        uart1
#define VIS_BAUD        921600

// ── Frame dimensions ──────────────────────────────────────────────────────
#define AXES            13
#define BYTES_PER_AXIS   8
#define FRAME_BYTES     (AXES * BYTES_PER_AXIS)   // 104 data bytes
#define SOF_0           0xA5u
#define SOF_1           0x5Au
#define TX_FRAME_BYTES  (FRAME_BYTES + 2)          // 106 with SOF

// ── SPI commands ──────────────────────────────────────────────────────────
#define CMD_READ_MANIFOLD   0xA0   // → 32 bytes (4 axes)
#define CMD_READ_STATUS     0xAC   // → 3 bytes (dissonance + flags)
#define CMD_READ_SCALE      0xAD   // → 9 bytes (7B scale table + 2B overflow)
#define CMD_WRITE_CHORD     0xB1   // ← 8 bytes (one Chord to execute)
#define SPU4_AXES            4

// ── Q12 identity ──────────────────────────────────────────────────────────
#define Q12_UNITY    0x1000    // 1.0 in Q12 = 4096

// ── Whisper PWI pulse width encoding ──────────────────────────────────────
// width = (104 * P + 181 * Q) + 1024_bias  where (P,Q) = RationalSurd of C
// For status use: width = dissonance + 1024 (simple proxy)
#define WHISPER_BIAS    1024u
#define WHISPER_LEAK_THRESHOLD 0x0100u   // dissonance > 256 → Cubic Leak

// ── Double buffer (swapped via multicore FIFO) ────────────────────────────
static uint8_t frame_back[FRAME_BYTES];
static uint8_t frame_front[TX_FRAME_BYTES];   // pre-built with SOF header

// ── Forward declarations ──────────────────────────────────────────────────
static void spi_read_manifold(uint8_t *out32);
static void spi_read_status(uint16_t *dissonance, uint8_t *flags);
static void spi_write_chord(const uint8_t *chord8);
static void assemble_frame(const uint8_t *abcd32, uint16_t dissonance,
                           uint8_t flags, uint8_t *frame);
static void pio_piranha_init(void);
static void pio_whisper_init(void);
static void whisper_send(uint32_t pulse_width);

// ── Core 1: SPU poller + Chord receiver ──────────────────────────────────
// Runs at ~1 kHz: poll FPGA, assemble frame, signal Core 0 via FIFO.
// Also drains UART1 RX: accumulates 8-byte Chords from RP2040 and writes
// them to the FPGA so the PC REPL can inject Lithic-L programs live.
void core1_entry(void) {
    uint8_t  abcd32[SPU4_AXES * BYTES_PER_AXIS];
    uint16_t dissonance;
    uint8_t  flags;

    // Chord receive state (from RP2040 UART and host USB stdio)
    uint8_t chord_buf[8];
    int     chord_pos = 0;
    uint8_t usb_chord_buf[8];
    int     usb_chord_pos = 0;

    while (true) {
        // 1. Poll FPGA manifold + status
        spi_read_manifold(abcd32);
        spi_read_status(&dissonance, &flags);
        uint8_t scale_bytes[9];
        spi_read_scale_table(scale_bytes);
        assemble_frame(abcd32, dissonance, flags, frame_back);
        // Copy first 5 bytes of scale table into spare bytes in axis 12 for telemetry
        {
            int off = 12 * BYTES_PER_AXIS;
            frame_back[off + 2] = scale_bytes[0];
            frame_back[off + 3] = scale_bytes[1];
            frame_back[off + 4] = scale_bytes[2];
            frame_back[off + 6] = scale_bytes[3];
            frame_back[off + 7] = scale_bytes[4];
        }

        // 2. Signal Core 0: frame ready (value 1 = new frame)
        multicore_fifo_push_blocking(1u);

        // 3. Cubic Leak check → Whisper TX pulse
        if (dissonance > WHISPER_LEAK_THRESHOLD) {
            whisper_send(dissonance + WHISPER_BIAS);
        }

        // 4. Drain UART1 RX: receive Chord bytes from RP2040 → FPGA
        while (uart_is_readable(VIS_UART)) {
            chord_buf[chord_pos++] = uart_getc(VIS_UART);
            if (chord_pos == 8) {
                spi_write_chord(chord_buf);
                chord_pos = 0;
            }
        }

        // 5. Drain USB stdio (host): receive raw 8-byte Chords from PC → FPGA
        {
            int usb_ch;
            while ((usb_ch = getchar_timeout_us(0)) != PICO_ERROR_TIMEOUT) {
                usb_chord_buf[usb_chord_pos++] = (uint8_t)usb_ch;
                if (usb_chord_pos == 8) {
                    spi_write_chord(usb_chord_buf);
                    usb_chord_pos = 0;
                }
            }
        }

        sleep_us(1000);   // ~1 kHz poll rate
    }
}

// ── Main (Core 0: TX arbiter) ─────────────────────────────────────────────
int main(void) {
    stdio_init_all();

    // UART1 bidirectional: TX→RP2040, RX←RP2040 (Chord passthrough)
    uart_init(VIS_UART, VIS_BAUD);
    gpio_set_function(VIS_UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(VIS_UART_RX_PIN, GPIO_FUNC_UART);

    // SPI0 → Tang 25K FPGA (Mode 0, CS active-low)
    spi_init(SPI_PORT, SPI_BAUD_HZ);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPI_SCK_PIN,  GPIO_FUNC_SPI);
    gpio_set_function(SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MISO_PIN, GPIO_FUNC_SPI);
    gpio_init(SPI_CS_PIN);
    gpio_set_dir(SPI_CS_PIN, GPIO_OUT);
    gpio_put(SPI_CS_PIN, 1);   // CS idle-high

    // PIO SM0: Piranha Pulse (61.44 kHz heartbeat) on GP6
    pio_piranha_init();
    // PIO SM1: Whisper TX (PWI rational telemetry) on GP7
    pio_whisper_init();

    // Pre-fill SOF header (constant for every frame)
    frame_front[0] = SOF_0;
    frame_front[1] = SOF_1;

    // Launch Core 1 poller
    // Before starting the background poller, push default RPLU tables into the FPGA
    // so runtime parameters are initialized (can be overwritten later via Artery).
    rplu_boot_load();
    multicore_launch_core1(core1_entry);

    // Core 0: wait for FIFO signal → swap buffers → transmit
    while (true) {
        multicore_fifo_pop_blocking();   // wait for Core 1 signal
        memcpy(frame_front + 2, frame_back, FRAME_BYTES);   // copy data after SOF
        uart_write_blocking(VIS_UART, frame_front, TX_FRAME_BYTES);
    }
}

// ── SPI helpers ───────────────────────────────────────────────────────────

static void spi_read_manifold(uint8_t *out32) {
    uint8_t cmd = CMD_READ_MANIFOLD;
    gpio_put(SPI_CS_PIN, 0);
    spi_write_blocking(SPI_PORT, &cmd, 1);
    spi_read_blocking(SPI_PORT, 0x00, out32, SPU4_AXES * BYTES_PER_AXIS);
    gpio_put(SPI_CS_PIN, 1);
}

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

// Read the per-axis scale table and overflow flags from FPGA.
// out9 must point to at least 9 bytes.
static void spi_read_scale_table(uint8_t *out9) {
    uint8_t cmd = CMD_READ_SCALE;
    gpio_put(SPI_CS_PIN, 0);
    spi_write_blocking(SPI_PORT, &cmd, 1);
    spi_read_blocking(SPI_PORT, 0x00, out9, 9);
    gpio_put(SPI_CS_PIN, 1);
}

// Send one 8-byte Chord to the FPGA for execution.
// FPGA latches it on the next Fibonacci tick (see spu13_sequencer.v).
static void spi_write_chord(const uint8_t *chord8) {
    uint8_t cmd = CMD_WRITE_CHORD;
    gpio_put(SPI_CS_PIN, 0);
    spi_write_blocking(SPI_PORT, &cmd, 1);
    spi_write_blocking(SPI_PORT, chord8, 8);
    gpio_put(SPI_CS_PIN, 1);
}

// Send a 64-bit value as an 8-byte chord (big-endian MSB first)
static void send_u64_as_chord(uint64_t v) {
    uint8_t chord[8];
    for (int i = 0; i < 8; i++) {
        chord[i] = (v >> (56 - 8*i)) & 0xFF;
    }
    spi_write_chord(chord);
}

// Boot-time RPLU loader: push default params and Pade coeffs into FPGA.
static void rplu_boot_load(void) {
    // Params: a_q16, re_q16, De_q16 (addr 0..2)
    for (int i = 0; i < 3; i++) {
        uint64_t header = ((uint64_t)0xA5 << 56) | ((uint64_t)0 << 48) | ((uint64_t)0 << 47) | (((uint64_t)i & 0x3FF) << 37);
        uint64_t data   = (uint64_t)RPLU_PARAMS_CARBON[i];
        send_u64_as_chord(header);
        send_u64_as_chord(data);
        sleep_us(50);
    }
    for (int i = 0; i < 3; i++) {
        uint64_t header = ((uint64_t)0xA5 << 56) | ((uint64_t)0 << 48) | ((uint64_t)1 << 47) | (((uint64_t)i & 0x3FF) << 37);
        uint64_t data   = (uint64_t)RPLU_PARAMS_IRON[i];
        send_u64_as_chord(header);
        send_u64_as_chord(data);
        sleep_us(50);
    }
    // Pade numerator (sel=1)
    for (int i = 0; i < 5; i++) {
        uint64_t header = ((uint64_t)0xA5 << 56) | ((uint64_t)1 << 48) | ((uint64_t)0 << 47) | (((uint64_t)i & 0x3FF) << 37);
        uint64_t data   = PADE_NUM_Q32[i];
        send_u64_as_chord(header);
        send_u64_as_chord(data);
        sleep_us(50);
    }
    // Pade denominator (sel=2)
    for (int i = 0; i < 5; i++) {
        uint64_t header = ((uint64_t)0xA5 << 56) | ((uint64_t)2 << 48) | ((uint64_t)0 << 47) | (((uint64_t)i & 0x3FF) << 37);
        uint64_t data   = PADE_DEN_Q32[i];
        send_u64_as_chord(header);
        send_u64_as_chord(data);
        sleep_us(50);
    }
}

// ── Frame assembly ────────────────────────────────────────────────────────
static void assemble_frame(const uint8_t *abcd32, uint16_t dissonance,
                            uint8_t flags, uint8_t *frame) {
    memset(frame, 0, FRAME_BYTES);

    // Axes 0–3: live SPU-4 ABCD (copied from SPI burst)
    memcpy(frame, abcd32, SPU4_AXES * BYTES_PER_AXIS);

    // Axes 4–11: identity manifold {P=Q12_UNITY, Q=0}
    for (int i = SPU4_AXES; i < AXES - 1; i++) {
        int off = i * BYTES_PER_AXIS;
        frame[off + 0] = (Q12_UNITY >> 8) & 0xFF;
        frame[off + 1] =  Q12_UNITY       & 0xFF;
    }

    // Axis 12: status word {P=dissonance, Q=flags}
    int off = 12 * BYTES_PER_AXIS;
    frame[off + 0] = (dissonance >> 8) & 0xFF;
    frame[off + 1] =  dissonance       & 0xFF;
    frame[off + 5] =  flags;
}

// ── PIO: Piranha Pulse ────────────────────────────────────────────────────
static void pio_piranha_init(void) {
    PIO  pio    = pio0;
    uint sm     = 0;
    uint offset = pio_add_program(pio, &piranha_pulse_program);
    piranha_pulse_program_init(pio, sm, offset, PIRANHA_PIN);
}

// ── PIO: Whisper TX ───────────────────────────────────────────────────────
static void pio_whisper_init(void) {
    PIO  pio    = pio0;
    uint sm     = 1;
    uint offset = pio_add_program(pio, &whisper_tx_program);
    whisper_tx_program_init(pio, sm, offset, WHISPER_PIN);
}

// Push a PWI pulse to the Whisper TX state machine.
// pulse_width is in PIO clock cycles (12 MHz ticks after the 12.5× divider).
static void whisper_send(uint32_t pulse_width) {
    pio_sm_put_blocking(pio0, 1, pulse_width);
}
