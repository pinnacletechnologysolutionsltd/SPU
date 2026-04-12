// tang25k_smoke.c - Minimal RP2350 smoke firmware
// Blinks on-board LED and prints a startup handshake message over USB stdio

#include "pico/stdlib.h"
#include <stdio.h>

#define LED_PIN 25

int main(void) {
    stdio_init_all();
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    // Startup blip
    puts("TANG25K_SMOKE: START");
    for (int i = 0; i < 3; ++i) {
        gpio_put(LED_PIN, 1);
        sleep_ms(200);
        gpio_put(LED_PIN, 0);
        sleep_ms(200);
    }

    // Handshake message
    puts("TANG25K_SMOKE: SMOKE_OK");

    // Main heartbeat: slow blink
    while (1) {
        gpio_put(LED_PIN, 1);
        sleep_ms(500);
        gpio_put(LED_PIN, 0);
        sleep_ms(500);
    }

    return 0;
}
