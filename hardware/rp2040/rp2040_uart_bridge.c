// rp2040_uart_bridge.c — Minimal USB-UART Bridge
//
// Reads UART0 RX (GP5) and forwards to USB CDC serial.
// Use with openFPGALoader dirtyjtag on a second RP2040,
// or use one RP2040 + one RP2350.
//
// Wiring:  RP2040 GP5 → Wukong V4 (uart_tx), GND → GND
// Output:  /dev/ttyACM0 at 115200 baud

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/irq.h"
#include "tusb.h"

#define UART_RX 5
#define UART_BAUD 115200

static uint8_t buf[256];
static volatile uint32_t wr = 0, rd = 0;

void on_uart_rx() {
    while (uart_is_readable(uart0)) {
        uint32_t n = (wr + 1) % 256;
        if (n != rd) { buf[wr] = uart_getc(uart0); wr = n; }
    }
}

int main() {
    stdio_init_all();
    uart_init(uart0, UART_BAUD);
    gpio_set_function(UART_RX, GPIO_FUNC_UART);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_fifo_enabled(uart0, true);
    irq_set_exclusive_handler(UART0_IRQ, on_uart_rx);
    irq_set_enabled(UART0_IRQ, true);
    uart_set_irq_enables(uart0, true, false);

    while (!tud_cdc_connected()) sleep_ms(100);

    while (1) {
        tud_task();
        while (rd != wr) {
            if (tud_cdc_write_available()) {
                tud_cdc_write_char(buf[rd]);
                rd = (rd + 1) % 256;
                tud_cdc_write_flush();
            } else break;
        }
    }
}
