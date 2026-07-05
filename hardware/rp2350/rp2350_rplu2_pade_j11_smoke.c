// rp2350_rplu2_pade_j11_smoke.c
// Target: Raspberry Pi Pico 2 / RP2350-Zero
// Role: Wukong J11 RPLU2 Padé sidecar smoke test.
//
// Wiring:
//   SPI0 MISO GP0, CS GP1, SCK GP2, MOSI GP3 -> Wukong J11
//   J11-1 CS#, J11-2 SCK, J11-3 MOSI, J11-4 MISO
//
// Build with -DSPU_RP2350_ZERO_HEADER_SPI=ON.

#include "hardware/gpio.h"
#include "hardware/spi.h"
#include "pico/stdio_usb.h"
#include "pico/stdlib.h"
#include "spu_link.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>

#define SPI_PORT     spi0
#ifndef SPI_BAUD_HZ
#define SPI_BAUD_HZ  25000
#endif

#ifndef RPLU2_PADE_LINK_CS_SETUP_US
#define RPLU2_PADE_LINK_CS_SETUP_US       1000
#endif
#ifndef RPLU2_PADE_LINK_CMD_TURNAROUND_US
#define RPLU2_PADE_LINK_CMD_TURNAROUND_US 1000
#endif
#ifndef RPLU2_PADE_LINK_CRC_HOLD_US
#define RPLU2_PADE_LINK_CRC_HOLD_US       1000
#endif
#ifndef RPLU2_PADE_LINK_CS_RECOVERY_US
#define RPLU2_PADE_LINK_CS_RECOVERY_US    1000
#endif

#ifndef RPLU2_PADE_BB_HALF_PERIOD_US
#define RPLU2_PADE_BB_HALF_PERIOD_US 20
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

#define RPLU2_OP_START      0x2Au
#define RPLU2_CFG_PADE_NUM  1u
#define RPLU2_CFG_PADE_DEN  2u
#define RPLU2_CFG_SADDLE    3u
#define RPLU2_RESULT_LANE   4u
#define M31_P               0x7FFFFFFFu

typedef struct {
    bool valid;
    uint8_t lane;
    uint64_t a;
    uint64_t b;
    uint64_t c;
    uint64_t d;
} qrtele_t;

typedef struct {
    const char *name;
    uint32_t numerator;
    uint32_t denominator;
    uint32_t expected;
} pade_case_t;

static const pade_case_t PADE_CASES[] = {
    {"two_over_one", 2u, 1u, 2u},
    {"two_over_two", 2u, 2u, 1u},
    {"five_over_two", 5u, 2u, 1073741826u},
    {"seven_over_three", 7u, 3u, 1431655767u},
    {"wide_constants", 12345u, 6789u, 801866410u},
};

static uint64_t read_be64(const uint8_t *bytes) {
    uint64_t value = 0;

    for (size_t i = 0; i < 8; i++) {
        value = (value << 8) | bytes[i];
    }
    return value;
}

static void bitbang_spi_init(void) {
    gpio_init(SPU_SPI_CS_PIN);
    gpio_set_function(SPU_SPI_CS_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(SPU_SPI_CS_PIN, GPIO_OUT);
    gpio_put(SPU_SPI_CS_PIN, 1);

    gpio_init(SPU_SPI_SCK_PIN);
    gpio_set_function(SPU_SPI_SCK_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(SPU_SPI_SCK_PIN, GPIO_OUT);
    gpio_put(SPU_SPI_SCK_PIN, 0);

    gpio_init(SPU_SPI_MOSI_PIN);
    gpio_set_function(SPU_SPI_MOSI_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(SPU_SPI_MOSI_PIN, GPIO_OUT);
    gpio_put(SPU_SPI_MOSI_PIN, 0);

    gpio_init(SPU_SPI_MISO_PIN);
    gpio_set_function(SPU_SPI_MISO_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(SPU_SPI_MISO_PIN, GPIO_IN);
    gpio_disable_pulls(SPU_SPI_MISO_PIN);
}

static uint8_t bitbang_spi_xfer(uint8_t out) {
    uint8_t in = 0;

    for (int bit = 7; bit >= 0; bit--) {
        gpio_put(SPU_SPI_MOSI_PIN, (out >> bit) & 0x1u);
        sleep_us(RPLU2_PADE_BB_HALF_PERIOD_US);
        gpio_put(SPU_SPI_SCK_PIN, 1);
        sleep_us(RPLU2_PADE_BB_HALF_PERIOD_US);
        in = (uint8_t)((in << 1) | (gpio_get(SPU_SPI_MISO_PIN) & 0x1u));
        gpio_put(SPU_SPI_SCK_PIN, 0);
    }

    gpio_put(SPU_SPI_MOSI_PIN, 0);
    sleep_us(RPLU2_PADE_BB_HALF_PERIOD_US);
    return in;
}

static void bus_select(void) {
    gpio_put(SPU_SPI_CS_PIN, 0);
    sleep_us(RPLU2_PADE_LINK_CS_SETUP_US);
}

static void bus_deselect(void) {
    gpio_put(SPU_SPI_SCK_PIN, 0);
    gpio_put(SPU_SPI_CS_PIN, 1);
    sleep_us(RPLU2_PADE_LINK_CS_RECOVERY_US);
}

static void bus_write_bytes(const uint8_t *bytes, size_t count) {
    for (size_t i = 0; i < count; i++) {
        (void)bitbang_spi_xfer(bytes[i]);
    }
}

static void bus_read_bytes(uint8_t *out, size_t count) {
    for (size_t i = 0; i < count; i++) {
        out[i] = bitbang_spi_xfer(0x00);
    }
}

static void bus_read_command(uint8_t cmd, uint8_t *out, size_t out_len) {
    bus_select();
    bus_write_bytes(&cmd, 1);
    sleep_us(RPLU2_PADE_LINK_CMD_TURNAROUND_US);
    bus_read_bytes(out, out_len);
    bus_deselect();
}

static void write_rplu_cfg(uint8_t sel, uint16_t addr, uint64_t data) {
    uint8_t cmd = SPU_CMD_WRITE_RPLU_CFG;
    uint64_t header = spu_rplu_header(sel, 0, addr);
    uint8_t header_bytes[8];
    uint8_t data_bytes[8];
    uint8_t crc;

    spu_u64_to_be(header, header_bytes);
    spu_u64_to_be(data, data_bytes);
    crc = spu_crc8_byte(0x00, cmd);
    crc = spu_crc8_bytes(crc, header_bytes, sizeof(header_bytes));
    crc = spu_crc8_bytes(crc, data_bytes, sizeof(data_bytes));

    bus_select();
    bus_write_bytes(&cmd, 1);
    bus_write_bytes(header_bytes, sizeof(header_bytes));
    bus_write_bytes(data_bytes, sizeof(data_bytes));
    bus_write_bytes(&crc, 1);
    sleep_us(RPLU2_PADE_LINK_CRC_HOLD_US);
    bus_deselect();
}

static void send_instruction(uint64_t word) {
    uint8_t cmd = SPU_CMD_WRITE_CHORD;
    uint8_t word_bytes[8];
    uint8_t crc;

    spu_u64_to_be(word, word_bytes);
    crc = spu_crc8_byte(0x00, cmd);
    crc = spu_crc8_bytes(crc, word_bytes, sizeof(word_bytes));

    bus_select();
    bus_write_bytes(&cmd, 1);
    bus_write_bytes(word_bytes, sizeof(word_bytes));
    bus_write_bytes(&crc, 1);
    sleep_us(RPLU2_PADE_LINK_CRC_HOLD_US);
    bus_deselect();
}

static void read_status(uint8_t raw[4]) {
    bus_read_command(SPU_CMD_READ_STATUS, raw, 4);
}

static bool status_crc_error(const uint8_t raw[4]) {
    return ((raw[3] >> 1) & 0x1u) != 0u;
}

static bool status_busy(const uint8_t raw[4]) {
    return (raw[3] & 0x1u) != 0u;
}

static void print_status(const char *tag, const uint8_t raw[4]) {
    printf("%s status raw=%02X %02X %02X %02X dbg=0x%02X op=0x%02X"
           " crc_error=%u busy=%u\r\n",
           tag, raw[0], raw[1], raw[2], raw[3], raw[0], raw[1],
           status_crc_error(raw) ? 1u : 0u, status_busy(raw) ? 1u : 0u);
}

static qrtele_t read_qr(void) {
    uint8_t raw[SPU_LINK_QR_BYTES] = {0};
    qrtele_t qr = {0};

    bus_read_command(SPU_CMD_READ_QR, raw, sizeof(raw));
    qr.valid = (raw[0] & 0x01u) != 0u;
    qr.lane = raw[1] & 0x0Fu;
    qr.a = read_be64(&raw[2]);
    qr.b = read_be64(&raw[10]);
    qr.c = read_be64(&raw[18]);
    qr.d = read_be64(&raw[26]);
    return qr;
}

static void print_qr(const char *tag, const qrtele_t *qr) {
    printf("%s qr valid=%u lane=%u A=0x%016" PRIX64
           " B=0x%016" PRIX64 " C=0x%016" PRIX64
           " D=0x%016" PRIX64 "\r\n",
           tag, qr->valid ? 1u : 0u, qr->lane,
           qr->a, qr->b, qr->c, qr->d);
}

static void hydrate_fixture(uint32_t numerator, uint32_t denominator) {
    write_rplu_cfg(RPLU2_CFG_PADE_NUM, 0, (uint64_t)numerator);
    write_rplu_cfg(RPLU2_CFG_PADE_NUM, 8, 0x0000000000000000ull);

    write_rplu_cfg(RPLU2_CFG_PADE_DEN, 0, (uint64_t)denominator);
    write_rplu_cfg(RPLU2_CFG_PADE_DEN, 8, 0x0000000000000000ull);

    write_rplu_cfg(RPLU2_CFG_SADDLE, 1, 0x0000000000000001ull);
    write_rplu_cfg(RPLU2_CFG_SADDLE, 65, 0x0000000000000000ull);
}

static bool poll_result(qrtele_t *qr_out, uint32_t timeout_ms) {
    uint32_t elapsed = 0;

    while (elapsed <= timeout_ms) {
        uint8_t status[4] = {0};
        qrtele_t qr;

        read_status(status);
        qr = read_qr();
        if (qr.valid && qr.lane == RPLU2_RESULT_LANE) {
            *qr_out = qr;
            return true;
        }
        if (status_crc_error(status)) {
            print_status("poll", status);
            *qr_out = qr;
            return false;
        }
        sleep_ms(20);
        elapsed += 20;
    }

    *qr_out = read_qr();
    return false;
}

static bool run_smoke_case(const pade_case_t *tc) {
    uint8_t status[4] = {0};
    qrtele_t qr = {0};
    uint64_t start_word = ((uint64_t)RPLU2_OP_START << 56) |
                          ((uint64_t)RPLU2_RESULT_LANE << 48);
    bool ok;

    printf("case=%s numerator=%" PRIu32 " denominator=%" PRIu32
           " expected=%" PRIu32 "\r\n",
           tc->name, tc->numerator, tc->denominator, tc->expected);

    read_status(status);
    print_status("before", status);

    hydrate_fixture(tc->numerator, tc->denominator);
    sleep_ms(20);
    read_status(status);
    print_status("after_cfg", status);
    if (status_crc_error(status)) {
        return false;
    }

    printf("start word=0x%016" PRIX64 "\r\n", start_word);
    send_instruction(start_word);
    sleep_ms(20);

    ok = poll_result(&qr, 3000);
    print_qr("result", &qr);
    read_status(status);
    print_status("after_eval", status);

    ok = ok &&
         !status_crc_error(status) &&
         qr.valid &&
         qr.lane == RPLU2_RESULT_LANE &&
         qr.a == tc->expected &&
         qr.b == 0u &&
         qr.c == 0u &&
         qr.d == 0u;

    printf("case=%s %s\r\n", tc->name, ok ? "PASS" : "FAIL");
    return ok;
}

static bool run_smoke_once(void) {
    bool pass = true;

    for (size_t i = 0; i < sizeof(PADE_CASES) / sizeof(PADE_CASES[0]); i++) {
        if (!run_smoke_case(&PADE_CASES[i])) {
            pass = false;
        }
        sleep_ms(100);
    }
    return pass;
}

int main(void) {
    uint32_t run = 0;

    stdio_init_all();
    bitbang_spi_init();

    while (true) {
        if (!stdio_usb_connected()) {
            sleep_ms(100);
            continue;
        }

        bool pass;

        printf("\r\n=== Wukong J11 RPLU2 Padé smoke run %" PRIu32 " ===\r\n", run++);
        printf("pins miso=GP%d cs=GP%d sck=GP%d mosi=GP%d spi_baud=%u"
               " bus=bitbang timing=%u/%u/%u/%uus half=%uus\r\n",
               SPU_SPI_MISO_PIN, SPU_SPI_CS_PIN, SPU_SPI_SCK_PIN,
               SPU_SPI_MOSI_PIN, (unsigned)SPI_BAUD_HZ,
               (unsigned)RPLU2_PADE_LINK_CS_SETUP_US,
               (unsigned)RPLU2_PADE_LINK_CMD_TURNAROUND_US,
               (unsigned)RPLU2_PADE_LINK_CRC_HOLD_US,
               (unsigned)RPLU2_PADE_LINK_CS_RECOVERY_US,
               (unsigned)RPLU2_PADE_BB_HALF_PERIOD_US);

        pass = run_smoke_once();
        printf("RPLU2PADE_J11: %s\r\n", pass ? "PASS" : "FAIL");
        sleep_ms(1500);
    }
}
