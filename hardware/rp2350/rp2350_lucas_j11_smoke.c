// rp2350_lucas_j11_smoke.c
// Target: Raspberry Pi Pico 2 / RP2350-Zero
// Role: One-shot/repeating Wukong J11 Lucas sidecar smoke test.
//
// Wiring:
//   SPI0 MISO GP0, CS GP1, SCK GP2, MOSI GP3 -> Wukong J11
//   J11-1 CS#, J11-2 SCK, J11-3 MOSI, J11-4 MISO
//
// Build with -DSPU_RP2350_ZERO_HEADER_SPI=ON.

#include "hardware/spi.h"
#include "pico/stdio_usb.h"
#include "pico/stdlib.h"
#include "spu_link.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>

#define SPI_PORT     spi0
#define SPI_BAUD_HZ  2000000

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

typedef struct {
    const char *name;
    uint64_t word;
    uint8_t expected_lane;
    uint64_t expected_a;
    uint32_t settle_ms;
} lucas_case_t;

static const lucas_case_t lucas_cases[] = {
    {
        .name = "PSCALE",
        .word = 0xD0200C0500000000ULL,
        .expected_lane = 2,
        .expected_a = 0x0000000800000005ULL,
        .settle_ms = 20,
    },
    {
        .name = "PCHIRAL",
        .word = 0xD1C00C0500000000ULL,
        .expected_lane = 12,
        .expected_a = 0x0000020400000008ULL,
        .settle_ms = 20,
    },
    {
        .name = "PMUL",
        .word = 0xD2300C0500807000ULL,
        .expected_lane = 3,
        .expected_a = 0x0000004200000029ULL,
        .settle_ms = 100,
    },
    {
        .name = "PINV",
        .word = 0xD3400C0500000000ULL,
        .expected_lane = 4,
        .expected_a = 0x0000000500000201ULL,
        .settle_ms = 250,
    },
};

static uint64_t read_be64(const uint8_t *bytes) {
    uint64_t value = 0;

    for (size_t i = 0; i < 8; i++) {
        value = (value << 8) | bytes[i];
    }
    return value;
}

static void print_status(spu_link_t *link, const char *tag) {
    uint8_t raw[4] = {0};

    spu_link_read_status_raw(link, raw);
    printf("%s status raw=%02X %02X %02X %02X\r\n",
           tag, raw[0], raw[1], raw[2], raw[3]);
}

static void send_word(spu_link_t *link, uint64_t word) {
    uint8_t chord[SPU_LINK_CHORD_BYTES];

    spu_u64_to_be(word, chord);
    spu_link_write_chord(link, chord);
}

static bool run_case(spu_link_t *link, const lucas_case_t *test) {
    uint8_t qr[SPU_LINK_QR_BYTES] = {0};
    uint8_t lane;
    uint64_t a;
    uint64_t b;
    uint64_t c;
    uint64_t d;
    bool valid;
    bool ok;

    printf("case %s word=0x%016" PRIX64 "\r\n", test->name, test->word);
    send_word(link, test->word);
    sleep_ms(test->settle_ms);

    spu_link_read_qr(link, qr);
    valid = (qr[0] & 1u) != 0;
    lane = qr[1] & 0x0Fu;
    a = read_be64(&qr[2]);
    b = read_be64(&qr[10]);
    c = read_be64(&qr[18]);
    d = read_be64(&qr[26]);

    ok = valid && lane == test->expected_lane && a == test->expected_a &&
         b == 0 && c == 0 && d == 0;

    printf("  qr valid=%u lane=%u A=0x%016" PRIX64
           " B=0x%016" PRIX64 " C=0x%016" PRIX64
           " D=0x%016" PRIX64 " %s\r\n",
           valid ? 1u : 0u, lane, a, b, c, d, ok ? "PASS" : "FAIL");
    print_status(link, "  after");

    return ok;
}

int main(void) {
    spu_link_t link;
    uint32_t run = 0;

    stdio_init_all();

    spi_init(SPI_PORT, SPI_BAUD_HZ);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPU_SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SPI_MISO_PIN, GPIO_FUNC_SPI);
    spu_link_init(&link, SPI_PORT, SPU_SPI_CS_PIN);

    while (true) {
        if (!stdio_usb_connected()) {
            sleep_ms(100);
            continue;
        }

        bool pass = true;

        printf("\r\n=== Wukong J11 Lucas smoke run %" PRIu32 " ===\r\n", run++);
        printf("pins miso=GP%d cs=GP%d sck=GP%d mosi=GP%d spi_baud=%u\r\n",
               SPU_SPI_MISO_PIN, SPU_SPI_CS_PIN, SPU_SPI_SCK_PIN,
               SPU_SPI_MOSI_PIN, (unsigned)SPI_BAUD_HZ);
        print_status(&link, "before");

        for (size_t i = 0; i < sizeof(lucas_cases) / sizeof(lucas_cases[0]); i++) {
            if (!run_case(&link, &lucas_cases[i])) {
                pass = false;
            }
        }

        printf("LUCAS_J11: %s\r\n", pass ? "PASS" : "FAIL");
        sleep_ms(1000);
    }
}
