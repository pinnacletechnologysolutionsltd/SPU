// rp2040_wukong_bridge.c — RP2040 UART Bridge for Wukong Artix-7
//
// This is a UART telemetry bridge only. Use the pinned pico-dirtyJtag firmware
// in tools/rp2040_tooling/repos/pico-dirtyJtag for JTAG programming.
//
// Wiring:
//   Wukong UART TX (pin V4) → RP2040 GP4
//   RP2040 GND  → Wukong GND
//   RP2040 VBUS → Wukong 3.3V (if powering from RP2040; else leave disconnected)
//
// One USB CDC port appears for UART telemetry at 115200 baud, 8N1.

#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/pio.h"
#include "hardware/uart.h"
#include "hardware/irq.h"
#include "tusb.h"

#define UART_RX_PIN 4   // Wukong V4 (uart_tx) → RP2040 GP4 (RX)
#define UART_BAUD   115200

// ── UART RX → USB CDC bridge ─────────────────────────────────────────

static uint8_t uart_buf[256];
static volatile uint32_t uart_wr = 0;
static volatile uint32_t uart_rd = 0;

void uart_rx_handler(void) {
    while (uart_is_readable(uart0)) {
        uint8_t ch = uart_getc(uart0);
        uint32_t next = (uart_wr + 1) % sizeof(uart_buf);
        if (next != uart_rd) {
            uart_buf[uart_wr] = ch;
            uart_wr = next;
        }
    }
}

void uart_init_bridge(void) {
    uart_init(uart0, UART_BAUD);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    uart_set_hw_flow(uart0, false, false);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_fifo_enabled(uart0, true);

    irq_set_exclusive_handler(UART0_IRQ, uart_rx_handler);
    irq_set_enabled(UART0_IRQ, true);
    uart_set_irq_enables(uart0, true, false);
}

// ── Main ──────────────────────────────────────────────────────────────

int main(void) {
    stdio_init_all();
    uart_init_bridge();

    // Wait for USB enumeration
    while (!tud_cdc_connected()) {
        sleep_ms(100);
    }

    // Main loop: forward UART RX to USB CDC, handle JTAG via TinyUSB
    while (1) {
        // Forward buffered UART data to USB CDC
        while (uart_rd != uart_wr) {
            if (tud_cdc_write_available()) {
                tud_cdc_write_char(uart_buf[uart_rd]);
                uart_rd = (uart_rd + 1) % sizeof(uart_buf);
                tud_cdc_write_flush();
            } else {
                break;
            }
        }
        // TinyUSB task handles JTAG on the other CDC endpoint
        tud_task();
    }
}
