// rp2350_uart_injector.c
// Target: Raspberry Pi Pico 2 (RP2350)
// Role: Minimal PC USB CDC to Tang Primer 25K periph_rx UART bridge.
//
// Wiring:
//   RP2350 GP4 / UART1 TX -> FPGA periph_rx / B3
//   RP2350 GND            -> FPGA GND
//
// The proven Tang 25K RPLU full-probe top accepts single-byte controls at
// 115200 baud: w, a, s, d, and space.

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include <stdio.h>

#define FPGA_UART        uart1
#define FPGA_UART_TX_PIN 4
#define FPGA_UART_RX_PIN 5
#define FPGA_UART_BAUD   115200

#define DEMO_PIN         15
#define DEMO_PERIOD_MS   250

static void uart_send_byte(uint8_t byte)
{
    uart_putc_raw(FPGA_UART, byte);
}

static void send_demo_step(void)
{
    static const uint8_t sequence[] = {'w', 'a', 's', 'd', ' '};
    static size_t idx = 0;

    uart_send_byte(sequence[idx]);
    idx++;
    if (idx >= sizeof(sequence)) {
        idx = 0;
    }
}

int main(void)
{
    stdio_init_all();

    uart_init(FPGA_UART, FPGA_UART_BAUD);
    gpio_set_function(FPGA_UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(FPGA_UART_RX_PIN, GPIO_FUNC_UART);

    gpio_init(DEMO_PIN);
    gpio_set_dir(DEMO_PIN, GPIO_IN);
    gpio_pull_up(DEMO_PIN);

    sleep_ms(500);
    printf("SPU RP2350 UART injector ready: USB CDC -> UART1 GP4 @ %u baud\r\n",
           FPGA_UART_BAUD);
    printf("Type w/a/s/d/space, or hold GP15 low for demo sequence.\r\n");

    absolute_time_t next_demo = make_timeout_time_ms(DEMO_PERIOD_MS);
    while (true) {
        int ch = getchar_timeout_us(0);
        if (ch != PICO_ERROR_TIMEOUT) {
            uart_send_byte((uint8_t)ch);
        }

        if (!gpio_get(DEMO_PIN) && absolute_time_diff_us(get_absolute_time(), next_demo) <= 0) {
            send_demo_step();
            next_demo = make_timeout_time_ms(DEMO_PERIOD_MS);
        }

        tight_loop_contents();
    }
}
