// rp2040_visualiser.c (v2.0 - Sovereign Visualiser & Debug Bridge)
//
// Role: RP2040 auxiliary device.
//   - Real mode:    Receives 106-byte framed Whisper frames from RP2350 over UART1
//                  (2-byte SOF 0xA5/0x5A + 104-byte payload), forwards 104-byte
//                  payload to PC via USB CDC (/dev/ttyACM0).
//                  Also passes USB input (8-byte Chords) back to RP2350 UART1 TX,
//                  enabling the PC REPL to inject Lithic-L programs into the FPGA.
//   - Emulate mode: Generates synthetic Jitterbug manifold frames internally
//                  (GP28 held LOW at boot = emulate; floating/HIGH = real).
//
// SWD debug:  Flash picoprobe firmware instead; GP2=SWCLK, GP3=SWDIO → RP2350.
//
// Connections (real mode):
//   RP2350 UART1 TX (GP4) → RP2040 GP5  (UART1 RX)
//   RP2040 GP4  (UART1 TX) → RP2350 GP5 (UART1 RX, Chord passthrough)
//   USB CDC: PC ↔ RP2040 (frames up, Chords down)
//
// Frame sync: SOF bytes 0xA5 0x5A allow byte-slip recovery.
// Chord passthrough: any 8-byte aligned USB input is forwarded to RP2350 UART1 TX.

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <stdint.h>

#define AXES              13
#define FRAME_BYTES       (AXES * 8)    // 104 payload bytes
#define SOF_0             0xA5u
#define SOF_1             0x5Au
#define TX_FRAME_BYTES    (FRAME_BYTES + 2)  // 106 on wire from RP2350
#define WHISPER_BAUD      921600
#define UART_RX_PIN       5             // GP5 = UART1 RX ← RP2350
#define UART_TX_PIN       4             // GP4 = UART1 TX → RP2350 (Chord passthrough)
#define MODE_SELECT_PIN   28            // GP28 LOW at boot = emulate mode

// Fibonacci-derived phase offsets (IVM lattice angular distribution)
static const float AXIS_PHASE_DEG[AXES] = {
    0.0f, 27.7f, 55.4f, 83.1f, 110.8f, 138.5f, 166.2f,
    193.8f, 221.5f, 249.2f, 276.9f, 304.6f, 332.3f
};

static const float AXIS_AMP[AXES] = {
    1.0f, 0.95f, 0.90f, 0.85f, 0.80f, 0.75f, 0.70f,
    0.65f, 0.60f, 0.55f, 0.50f, 0.45f, 0.40f
};

// Forward 104-byte payload to PC via USB CDC (raw bytes, no SOF)
static void forward_frame(const uint8_t *frame) {
    for (int i = 0; i < FRAME_BYTES; i++) {
        putchar_raw(frame[i]);
    }
    stdio_flush();
}

// Real mode:
//   - Reads 106-byte SOF-framed frames from UART1, strips SOF, forwards 104 bytes to USB.
//   - Reads USB input (Chord bytes from PC) and passes them to RP2350 via UART1 TX.
//   SOF re-sync: if bytes arrive out of frame, scan forward until 0xA5 0x5A found.
static void real_loop(void) {
    uart_init(uart1, WHISPER_BAUD);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);

    uint8_t buf[TX_FRAME_BYTES];
    int pos = 0;
    bool synced = false;

    // Chord passthrough buffer (USB → RP2350)
    uint8_t chord_buf[8];
    int chord_pos = 0;

    while (true) {
        // ── Receive from RP2350 → forward to PC ──────────────────────── //
        while (uart_is_readable(uart1)) {
            uint8_t b = uart_getc(uart1);

            if (!synced) {
                // Scan for SOF pattern
                if (pos == 0 && b == SOF_0) { buf[pos++] = b; }
                else if (pos == 1 && b == SOF_1) { buf[pos++] = b; synced = true; }
                else { pos = 0; }   // reset on mismatch
            } else {
                buf[pos++] = b;
                if (pos == TX_FRAME_BYTES) {
                    // Validate SOF still present (sanity check)
                    if (buf[0] == SOF_0 && buf[1] == SOF_1) {
                        forward_frame(buf + 2);   // skip 2-byte SOF
                    }
                    pos = 0;
                    synced = false;   // re-sync on next frame boundary
                }
            }
        }

        // ── Receive from PC (USB) → forward to RP2350 ────────────────── //
        int c = getchar_timeout_us(0);   // non-blocking
        if (c != PICO_ERROR_TIMEOUT) {
            chord_buf[chord_pos++] = (uint8_t)c;
            if (chord_pos == 8) {
                uart_write_blocking(uart1, chord_buf, 8);
                chord_pos = 0;
            }
        }
    }
}

// NOTE: Emulate loop uses floating-point trig intentionally — it is a test
// stimulus only, not a Q(√3) reference. Laminar flags in spu_inhale will
// show ⚠ until real FPGA-computed values arrive.
static void emulate_loop(void) {
    float t = 0.0f;
    uint8_t frame[FRAME_BYTES];

    while (true) {
        memset(frame, 0, FRAME_BYTES);

        for (int i = 0; i < AXES; i++) {
            float phase = t + AXIS_PHASE_DEG[i] * (3.14159265f / 180.0f);
            float amp   = AXIS_AMP[i];
            int16_t a   = (int16_t)(cosf(phase) * 4096.0f * amp);
            int16_t b   = (int16_t)(sinf(phase) * 4096.0f * amp * 0.57735027f);
            int off     = i * 8;
            frame[off + 0] = (uint8_t)(a >> 8);
            frame[off + 1] = (uint8_t)(a);
            frame[off + 4] = (uint8_t)(b >> 8);
            frame[off + 5] = (uint8_t)(b);
        }

        forward_frame(frame);

        t += 0.08f;
        if (t > 6.28318f) t -= 6.28318f;

        sleep_ms(50);   // 20 Hz
    }
}

int main(void) {
    stdio_usb_init();

    gpio_init(MODE_SELECT_PIN);
    gpio_set_dir(MODE_SELECT_PIN, GPIO_IN);
    gpio_pull_up(MODE_SELECT_PIN);

    while (!stdio_usb_connected()) sleep_ms(100);
    sleep_ms(200);

    bool emulate = !gpio_get(MODE_SELECT_PIN);   // LOW = emulate

    if (emulate) {
        emulate_loop();
    } else {
        real_loop();
    }

    return 0;
}

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <stdint.h>

#define AXES              13
#define FRAME_BYTES       (AXES * 8)    // 104
#define WHISPER_BAUD      921600
#define UART_RX_PIN       5             // GP5 = UART1 RX
#define MODE_SELECT_PIN   28            // GP28 LOW at boot = emulate mode

// Fibonacci-derived phase offsets (IVM lattice angular distribution)
static const float AXIS_PHASE_DEG[AXES] = {
    0.0f, 27.7f, 55.4f, 83.1f, 110.8f, 138.5f, 166.2f,
    193.8f, 221.5f, 249.2f, 276.9f, 304.6f, 332.3f
};

static const float AXIS_AMP[AXES] = {
    1.0f, 0.95f, 0.90f, 0.85f, 0.80f, 0.75f, 0.70f,
    0.65f, 0.60f, 0.55f, 0.50f, 0.45f, 0.40f
};

static void forward_frame(const uint8_t *frame) {
    for (int i = 0; i < FRAME_BYTES; i++) {
        putchar_raw(frame[i]);
    }
    stdio_flush();
}

// Real mode: read exactly FRAME_BYTES from UART1, then forward over USB.
static void real_loop(void) {
    uart_init(uart1, WHISPER_BAUD);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    uint8_t frame[FRAME_BYTES];
    int pos = 0;

    while (true) {
        if (uart_is_readable(uart1)) {
            frame[pos++] = uart_getc(uart1);
            if (pos == FRAME_BYTES) {
                forward_frame(frame);
                pos = 0;
            }
        }
    }
}

// NOTE: This emulator uses floating-point trig (cosf/sinf) intentionally.
// It is a TEST STIMULUS only — not a Q(√3) reference implementation.
// The ⚠ Laminar flags in spu_inhale are the correct/expected output here;
// they will turn ✓ only when real FPGA-computed field values arrive.
// For a field-correct reference, see the Verilog testbenches and run_all_tests.py.
static void emulate_loop(void) {
    float t = 0.0f;
    uint8_t frame[FRAME_BYTES];

    while (true) {
        memset(frame, 0, FRAME_BYTES);

        for (int i = 0; i < AXES; i++) {
            float phase = t + AXIS_PHASE_DEG[i] * (3.14159265f / 180.0f);
            float amp   = AXIS_AMP[i];
            int16_t a   = (int16_t)(cosf(phase) * 4096.0f * amp);
            int16_t b   = (int16_t)(sinf(phase) * 4096.0f * amp * 0.57735027f);
            int off     = i * 8;
            frame[off + 0] = (uint8_t)(a >> 8);
            frame[off + 1] = (uint8_t)(a);
            frame[off + 4] = (uint8_t)(b >> 8);
            frame[off + 5] = (uint8_t)(b);
        }

        forward_frame(frame);

        t += 0.08f;
        if (t > 6.28318f) t -= 6.28318f;

        sleep_ms(50); // 20 Hz
    }
}

int main(void) {
    stdio_usb_init();

    // Mode select pin: pull up internally; short to GND for emulate mode
    gpio_init(MODE_SELECT_PIN);
    gpio_set_dir(MODE_SELECT_PIN, GPIO_IN);
    gpio_pull_up(MODE_SELECT_PIN);

    // Wait for USB host
    while (!stdio_usb_connected()) sleep_ms(100);
    sleep_ms(200);

    bool emulate = !gpio_get(MODE_SELECT_PIN); // LOW = emulate

    if (emulate) {
        emulate_loop();
    } else {
        real_loop();
    }

    return 0;
}
