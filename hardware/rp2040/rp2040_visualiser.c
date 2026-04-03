// rp2040_visualiser.c (v1.0 - Sovereign Visualiser & Debug Bridge)
//
// Role: RP2040 auxiliary device.
//   - Real mode:    Receives 104-byte Whisper frames from RP2350 over UART1
//                  and forwards them to the PC via USB CDC (/dev/ttyACM0).
//   - Emulate mode: Generates synthetic Jitterbug manifold frames internally
//                  (GP28 held LOW at boot = emulate; floating/HIGH = real).
//
// SWD debug:  Wire GP2 → RP2350 SWCLK, GP3 → RP2350 SWDIO and flash
//             picoprobe firmware instead for hardware debugging sessions.
//
// Connections (real mode):
//   RP2350 UART1 TX  →  RP2040 GP5  (UART1 RX)
//   RP2350 GND       →  RP2040 GND

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
