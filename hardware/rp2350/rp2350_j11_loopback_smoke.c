// rp2350_j11_loopback_smoke.c
// Target: Raspberry Pi Pico 2 / RP2350-Zero
// Role: Raw-byte smoke test for spu_a7_j11_loopback_top.v (Wukong J11
// bottom-row remap: J4/G4/B4/B5). No southbridge protocol involved —
// the FPGA design under test bypasses spu_spi_slave.v entirely, so this
// firmware talks to it with plain hardware_spi transfers instead of
// spu_link.c.
//
// Wiring (RP2350-Zero header pinset, build with
// -DSPU_RP2350_ZERO_HEADER_SPI=ON):
//   SPI0 MISO GP0, CS GP1, SCK GP2, MOSI GP3 -> Wukong J11 bottom row
//   J11-7 CS#, J11-8 SCK, J11-9 MOSI, J11-10 MISO
//
// spu_a7_j11_loopback_top.v captures MOSI into a register clocked
// directly by spi_sck (no reset) and drives that register straight back
// out on MISO until the next SCK edge; MISO is forced low while CS is
// deasserted. Because the capture register is never reset, whatever it
// last held survives CS transitions and even power-up-to-power-up botstream
// reloads carry no guarantee about its initial value — so this test
// primes the link with one throwaway byte first to pin down a known
// starting state, then predicts each transfer's expected RX byte from
// the previous transfer's LSB: expected[n] = (prev_tx_lsb << 7) | (tx[n] >> 1).

#include "hardware/spi.h"
#include "pico/stdio_usb.h"
#include "pico/stdlib.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>

#define SPI_PORT     spi0
#ifndef SPI_BAUD_HZ
#define SPI_BAUD_HZ  500000
#endif

#ifndef LOOPBACK_CS_SETUP_US
#define LOOPBACK_CS_SETUP_US 50
#endif
#ifndef LOOPBACK_CS_RECOVERY_US
#define LOOPBACK_CS_RECOVERY_US 50
#endif

#ifndef SPU_SPI_MISO_PIN
#define SPU_SPI_MISO_PIN 16
#endif
#ifndef SPU_SPI_CS_PIN
#define SPU_SPI_CS_PIN   17
#endif
#ifndef SPU_SPI_SCK_PIN
#define SPU_SPI_SCK_PIN  18
#endif
#ifndef SPU_SPI_MOSI_PIN
#define SPU_SPI_MOSI_PIN 19
#endif

static const uint8_t test_vector[] = {
    0x00, 0xFF, 0xAA, 0x55, 0x01, 0x80, 0x93, 0x3C,
    0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40,
};

static uint8_t xfer_byte(uint8_t tx) {
    uint8_t rx = 0;

    gpio_put(SPU_SPI_CS_PIN, 0);
    sleep_us(LOOPBACK_CS_SETUP_US);
    spi_write_read_blocking(SPI_PORT, &tx, &rx, 1);
    gpio_put(SPU_SPI_CS_PIN, 1);
    sleep_us(LOOPBACK_CS_RECOVERY_US);

    return rx;
}

int main(void) {
    uint32_t run = 0;

    stdio_init_all();

    spi_init(SPI_PORT, SPI_BAUD_HZ);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPU_SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SPI_MISO_PIN, GPIO_FUNC_SPI);

    gpio_init(SPU_SPI_CS_PIN);
    gpio_set_dir(SPU_SPI_CS_PIN, GPIO_OUT);
    gpio_put(SPU_SPI_CS_PIN, 1);

    while (true) {
        if (!stdio_usb_connected()) {
            sleep_ms(100);
            continue;
        }

        bool pass = true;
        uint8_t prev_tx;

        printf("\r\n=== Wukong J11 loopback smoke run %" PRIu32 " ===\r\n", run++);
        printf("pins miso=GP%d cs=GP%d sck=GP%d mosi=GP%d spi_baud=%u\r\n",
               SPU_SPI_MISO_PIN, SPU_SPI_CS_PIN, SPU_SPI_SCK_PIN,
               SPU_SPI_MOSI_PIN, (unsigned)SPI_BAUD_HZ);

        // Prime: pin down a known capture-register state before predicting
        // anything (see file header — the register is never reset).
        prev_tx = 0x00;
        (void)xfer_byte(prev_tx);

        for (size_t i = 0; i < sizeof(test_vector); i++) {
            uint8_t tx = test_vector[i];
            uint8_t rx = xfer_byte(tx);
            uint8_t expected = (uint8_t)((prev_tx & 0x01u) << 7) | (tx >> 1);
            bool ok = (rx == expected);

            printf("  tx=%02X rx=%02X expected=%02X %s\r\n",
                   tx, rx, expected, ok ? "ok" : "MISMATCH");
            if (!ok) {
                pass = false;
            }
            prev_tx = tx;
        }

        printf("J11_LOOPBACK: %s\r\n", pass ? "PASS" : "FAIL");
        sleep_ms(1500);
    }
}
