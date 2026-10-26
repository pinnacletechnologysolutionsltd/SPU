#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include <stdint.h>
#include <stdio.h>

#define PIN_TDI 0
#define PIN_TMS 1
#define PIN_TCK 2
#define PIN_TDO 3

static int jtag_clock(int tms, int tdi) {
    gpio_put(PIN_TMS, tms ? 1 : 0);
    gpio_put(PIN_TDI, tdi ? 1 : 0);
    sleep_us(2);
    gpio_put(PIN_TCK, 1);
    sleep_us(2);
    int tdo = gpio_get(PIN_TDO);
    gpio_put(PIN_TCK, 0);
    sleep_us(2);
    return tdo;
}

static uint32_t read_idcode(void) {
    uint32_t id = 0;

    // TAP reset.
    for (int i = 0; i < 8; i++) {
        (void)jtag_clock(1, 0);
    }

    // Test-Logic-Reset -> Run-Test/Idle -> Select-DR -> Capture-DR -> Shift-DR.
    (void)jtag_clock(0, 0);
    (void)jtag_clock(1, 0);
    (void)jtag_clock(0, 0);
    (void)jtag_clock(0, 0);

    for (int bit = 0; bit < 32; bit++) {
        int tdo = jtag_clock(bit == 31, 0);
        id |= ((uint32_t)(tdo & 1) << bit);
    }

    // Exit1-DR -> Update-DR -> Run-Test/Idle.
    (void)jtag_clock(1, 0);
    (void)jtag_clock(0, 0);

    return id;
}

int main(void) {
    stdio_init_all();

    gpio_init(PIN_TDI);
    gpio_init(PIN_TMS);
    gpio_init(PIN_TCK);
    gpio_init(PIN_TDO);
    gpio_set_dir(PIN_TDI, GPIO_OUT);
    gpio_set_dir(PIN_TMS, GPIO_OUT);
    gpio_set_dir(PIN_TCK, GPIO_OUT);
    gpio_set_dir(PIN_TDO, GPIO_IN);
    gpio_disable_pulls(PIN_TDO);
    gpio_put(PIN_TDI, 0);
    gpio_put(PIN_TMS, 1);
    gpio_put(PIN_TCK, 0);

    while (!stdio_usb_connected()) {
        sleep_ms(100);
    }

    printf("RP2040 JTAG IDCODE probe: TDI=GP%d TMS=GP%d TCK=GP%d TDO=GP%d\r\n",
           PIN_TDI, PIN_TMS, PIN_TCK, PIN_TDO);

    while (true) {
        int idle_low;
        int idle_high;

        gpio_put(PIN_TDI, 0);
        gpio_put(PIN_TMS, 0);
        gpio_put(PIN_TCK, 0);
        sleep_ms(10);
        idle_low = gpio_get(PIN_TDO);

        gpio_put(PIN_TMS, 1);
        sleep_ms(10);
        idle_high = gpio_get(PIN_TDO);

        uint32_t id = read_idcode();
        printf("TDO_IDLE tms0=%d tms1=%d IDCODE=0x%08lx %s\r\n",
               idle_low, idle_high, (unsigned long)id,
               (id == 0 || id == 0xffffffffu) ? "FAIL" : "PASS");
        sleep_ms(1000);
    }
}
