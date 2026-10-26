#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include <stdio.h>

#define LOOP_OUT_PIN 0
#define LOOP_IN_PIN  3

int main(void) {
    stdio_init_all();

    gpio_init(LOOP_OUT_PIN);
    gpio_set_dir(LOOP_OUT_PIN, GPIO_OUT);
    gpio_put(LOOP_OUT_PIN, 0);

    gpio_init(LOOP_IN_PIN);
    gpio_set_dir(LOOP_IN_PIN, GPIO_IN);
    gpio_disable_pulls(LOOP_IN_PIN);

    while (!stdio_usb_connected()) {
        sleep_ms(100);
    }

    printf("RP2040 GPIO loopback: GP%d -> GP%d\r\n", LOOP_OUT_PIN, LOOP_IN_PIN);

    while (true) {
        gpio_put(LOOP_OUT_PIN, 0);
        sleep_ms(10);
        int low = gpio_get(LOOP_IN_PIN);

        gpio_put(LOOP_OUT_PIN, 1);
        sleep_ms(10);
        int high = gpio_get(LOOP_IN_PIN);

        printf("LOOP low=%d high=%d %s\r\n",
               low, high, (!low && high) ? "PASS" : "FAIL");
        sleep_ms(500);
    }
}
