// rp2350_su3_j11_smoke.c
// Target: Raspberry Pi Pico 2 / RP2350-Zero
// Role: Repeating Wukong J11 SU3 sidecar smoke test.
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
#ifndef SPI_BAUD_HZ
#define SPI_BAUD_HZ  25000
#endif

#ifndef SU3_LINK_CS_SETUP_US
#define SU3_LINK_CS_SETUP_US       1000
#endif
#ifndef SU3_LINK_CMD_TURNAROUND_US
#define SU3_LINK_CMD_TURNAROUND_US 1000
#endif
#ifndef SU3_LINK_CRC_HOLD_US
#define SU3_LINK_CRC_HOLD_US       1000
#endif
#ifndef SU3_LINK_CS_RECOVERY_US
#define SU3_LINK_CS_RECOVERY_US    1000
#endif

#ifndef SU3_SMOKE_USE_STATUS_CHECKS
#define SU3_SMOKE_USE_STATUS_CHECKS 1
#endif
#ifndef SU3_UNCHECKED_WORD_DELAY_US
#define SU3_UNCHECKED_WORD_DELAY_US 250
#endif
#ifndef SU3_UNCHECKED_RESULT_WAIT_MS
#define SU3_UNCHECKED_RESULT_WAIT_MS 1500
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

#define OP_SU3_LOAD_A 0xE8u
#define OP_SU3_LOAD_B 0xE9u
#define OP_SU3_START  0xEAu
#define OP_SU3_READ   0xEBu

#define SU3_SIDE_IDLE   0u
#define SU3_SIDE_LOAD_A 1u
#define SU3_SIDE_LOAD_B 2u
#define SU3_SIDE_WAIT   3u

typedef struct {
    uint8_t elem;
    uint8_t lane;
    uint64_t exp_a;
    uint64_t exp_b;
    uint64_t exp_c;
    uint64_t exp_d;
} su3_case_t;

// Words are in sidecar stream order: word 0 is the low 32 bits
// (real c0), word 7 is the high 32 bits (imag c3).
static const uint32_t dense_a[9][8] = {
    {0x00000004u, 0x00000006u, 0x00000008u, 0x0000000au,
     0x00000011u, 0x00000013u, 0x00000017u, 0x00000019u},
    {0x0000000fu, 0x00000011u, 0x00000013u, 0x00000015u,
     0x00000027u, 0x00000029u, 0x0000002du, 0x0000002fu},
    {0x0000001au, 0x0000001cu, 0x0000001eu, 0x00000020u,
     0x0000003du, 0x0000003fu, 0x00000043u, 0x00000045u},
    {0x00000009u, 0x0000000bu, 0x0000000du, 0x0000000fu,
     0x0000001bu, 0x0000001du, 0x00000021u, 0x00000023u},
    {0x00000014u, 0x00000016u, 0x00000018u, 0x0000001au,
     0x00000031u, 0x00000033u, 0x00000037u, 0x00000039u},
    {0x0000001fu, 0x00000021u, 0x00000023u, 0x00000025u,
     0x00000047u, 0x00000049u, 0x0000004du, 0x0000004fu},
    {0x0000000eu, 0x00000010u, 0x00000012u, 0x00000014u,
     0x00000025u, 0x00000027u, 0x0000002bu, 0x0000002du},
    {0x00000019u, 0x0000001bu, 0x0000001du, 0x0000001fu,
     0x0000003bu, 0x0000003du, 0x00000041u, 0x00000043u},
    {0x00000024u, 0x00000026u, 0x00000028u, 0x0000002au,
     0x00000051u, 0x00000053u, 0x00000057u, 0x00000059u},
};

static const uint32_t dense_b[9][8] = {
    {0x0000001eu, 0x00000020u, 0x00000022u, 0x00000024u,
     0x00000045u, 0x00000047u, 0x0000004bu, 0x0000004du},
    {0x0000002bu, 0x0000002du, 0x0000002fu, 0x00000031u,
     0x0000005fu, 0x00000061u, 0x00000065u, 0x00000067u},
    {0x00000038u, 0x0000003au, 0x0000003cu, 0x0000003eu,
     0x00000079u, 0x0000007bu, 0x0000007fu, 0x00000081u},
    {0x00000025u, 0x00000027u, 0x00000029u, 0x0000002bu,
     0x00000053u, 0x00000055u, 0x00000059u, 0x0000005bu},
    {0x00000032u, 0x00000034u, 0x00000036u, 0x00000038u,
     0x0000006du, 0x0000006fu, 0x00000073u, 0x00000075u},
    {0x0000003fu, 0x00000041u, 0x00000043u, 0x00000045u,
     0x00000087u, 0x00000089u, 0x0000008du, 0x0000008fu},
    {0x0000002cu, 0x0000002eu, 0x00000030u, 0x00000032u,
     0x00000061u, 0x00000063u, 0x00000067u, 0x00000069u},
    {0x00000039u, 0x0000003bu, 0x0000003du, 0x0000003fu,
     0x0000007bu, 0x0000007du, 0x00000081u, 0x00000083u},
    {0x00000046u, 0x00000048u, 0x0000004au, 0x0000004cu,
     0x00000095u, 0x00000097u, 0x0000009bu, 0x0000009du},
};

static const su3_case_t su3_cases[] = {
    {0, 2, 0x7ffe271f7ffc43efULL, 0x7fff6b677ffed36fULL,
     0x00021510000446a0ULL, 0x0000a30000014f30ULL},
    {4, 5, 0x7ffd2a6b7ffa47ffULL, 0x7fff196b7ffe2e9fULL,
     0x00034b480006baa8ULL, 0x00010678000218a8ULL},
    {8, 8, 0x7ffbf6df7ff7de5fULL, 0x7ffeb5277ffd653fULL,
     0x0004caa00009c0f0ULL, 0x00018250000312e0ULL},
};

static uint64_t read_be64(const uint8_t *bytes) {
    uint64_t value = 0;

    for (size_t i = 0; i < 8; i++) {
        value = (value << 8) | bytes[i];
    }
    return value;
}

static void send_word_unchecked(spu_link_t *link, uint64_t word) {
    uint8_t chord[SPU_LINK_CHORD_BYTES];

    spu_u64_to_be(word, chord);
    spu_link_write_chord_nowait(link, chord);
}

static bool send_word_probe(spu_link_t *link, uint64_t word,
                            uint8_t state, uint8_t stream, uint8_t chunk);

static bool read_debug_status(spu_link_t *link, uint8_t raw[4]) {
    spu_link_read_status_raw(link, raw);
    return (raw[2] & 0x10u) != 0u;
}

static uint8_t dbg_state(const uint8_t raw[4]) {
    return (raw[2] >> 5) & 0x07u;
}

static uint8_t dbg_stream(const uint8_t raw[4]) {
    return raw[0] >> 4;
}

static uint8_t dbg_chunk(const uint8_t raw[4]) {
    return (raw[0] >> 1) & 0x07u;
}

static bool dbg_result_ready(const uint8_t raw[4]) {
    return (raw[0] & 0x01u) != 0u;
}

static bool status_matches(const uint8_t raw[4], uint8_t state,
                           uint8_t stream, uint8_t chunk) {
    if ((raw[2] & 0x10u) == 0u || dbg_state(raw) != state) {
        return false;
    }
    if (state == SU3_SIDE_LOAD_A || state == SU3_SIDE_LOAD_B) {
        return dbg_stream(raw) == stream && dbg_chunk(raw) == chunk;
    }
    if (state == SU3_SIDE_IDLE) {
        return dbg_result_ready(raw);
    }
    return true;
}

static bool status_position_same(const uint8_t raw[4],
                                 const uint8_t before[4]) {
    uint8_t state = dbg_state(before);

    if ((raw[2] & 0x10u) == 0u || (before[2] & 0x10u) == 0u) {
        return false;
    }
    if (dbg_state(raw) != state) {
        return false;
    }
    if (state == SU3_SIDE_LOAD_A || state == SU3_SIDE_LOAD_B) {
        return dbg_stream(raw) == dbg_stream(before) &&
               dbg_chunk(raw) == dbg_chunk(before);
    }
    if (state == SU3_SIDE_IDLE) {
        return dbg_result_ready(raw) == dbg_result_ready(before);
    }
    return true;
}

static bool wait_for_status(spu_link_t *link, uint8_t state,
                            uint8_t stream, uint8_t chunk,
                            uint32_t timeout_ms, uint8_t last_raw[4]) {
    uint32_t waited_ms = 0;

    while (waited_ms <= timeout_ms) {
        read_debug_status(link, last_raw);
        if (status_matches(last_raw, state, stream, chunk)) {
            return true;
        }
        sleep_ms(5);
        waited_ms += 5;
    }
    return false;
}

static bool send_word_checked(spu_link_t *link, uint64_t word,
                              uint8_t state, uint8_t stream, uint8_t chunk) {
    uint8_t before[4] = {0};
    uint8_t raw[4] = {0};

    read_debug_status(link, before);
    for (uint8_t attempt = 0; attempt < 4; attempt++) {
        send_word_unchecked(link, word);
        if (wait_for_status(link, state, stream, chunk, 250, raw)) {
            return true;
        }
        if (status_matches(raw, state, stream, chunk)) {
            return true;
        }
        if (!status_position_same(raw, before)) {
            break;
        }
        before[0] = raw[0];
        before[1] = raw[1];
        before[2] = raw[2];
        before[3] = raw[3];
    }

    printf("  checked write failed target state=%u stream=%u chunk=%u raw=%02X %02X %02X %02X\r\n",
           state, stream, chunk, raw[0], raw[1], raw[2], raw[3]);
    return false;
}

static bool send_word_probe(spu_link_t *link, uint64_t word,
                            uint8_t state, uint8_t stream, uint8_t chunk) {
#if SU3_SMOKE_USE_STATUS_CHECKS
    return send_word_checked(link, word, state, stream, chunk);
#else
    (void)state;
    (void)stream;
    (void)chunk;
    send_word_unchecked(link, word);
    sleep_us(SU3_UNCHECKED_WORD_DELAY_US);
    return true;
#endif
}

static bool wait_for_opcode(spu_link_t *link, uint8_t opcode,
                            uint32_t timeout_ms, uint8_t last_raw[4]) {
    uint32_t waited_ms = 0;

    while (waited_ms <= timeout_ms) {
        read_debug_status(link, last_raw);
        if ((last_raw[2] & 0x10u) != 0u && last_raw[1] == opcode) {
            return true;
        }
        sleep_ms(1);
        waited_ms += 1;
    }
    return false;
}

static bool send_read_checked(spu_link_t *link, uint64_t word) {
    uint8_t raw[4] = {0};

#if !SU3_SMOKE_USE_STATUS_CHECKS
    send_word_unchecked(link, word);
    sleep_us(SU3_UNCHECKED_WORD_DELAY_US);
    return true;
#else
    for (uint8_t attempt = 0; attempt < 4; attempt++) {
        send_word_unchecked(link, word);
        if (wait_for_opcode(link, OP_SU3_READ, 50, raw)) {
            return true;
        }
    }

    printf("  checked read failed raw=%02X %02X %02X %02X\r\n",
           raw[0], raw[1], raw[2], raw[3]);
    return false;
#endif
}

static uint64_t inst_start(uint8_t elem) {
    return ((uint64_t)OP_SU3_START << 56) |
           ((uint64_t)(elem & 0x0fu) << 48);
}

static uint64_t inst_load(uint8_t op, uint8_t elem, uint8_t word_idx,
                          uint32_t data) {
    return ((uint64_t)op << 56) |
           ((uint64_t)(elem & 0x0fu) << 52) |
           ((uint64_t)(word_idx & 0x07u) << 48) |
           (uint64_t)data;
}

static uint64_t inst_read(uint8_t lane, uint8_t elem) {
    return ((uint64_t)OP_SU3_READ << 56) |
           ((uint64_t)(lane & 0x0fu) << 52) |
           ((uint64_t)(elem & 0x0fu) << 48);
}

static void print_status(spu_link_t *link, const char *tag) {
    uint8_t raw[4] = {0};

    spu_link_read_status_raw(link, raw);
    printf("%s status raw=%02X %02X %02X %02X\r\n",
           tag, raw[0], raw[1], raw[2], raw[3]);
}

static bool wait_sidecar_idle(spu_link_t *link, uint32_t timeout_ms) {
    uint8_t raw[4] = {0};
    uint32_t waited_ms = 0;

#if !SU3_SMOKE_USE_STATUS_CHECKS
    (void)link;
    (void)timeout_ms;
    sleep_ms(SU3_UNCHECKED_RESULT_WAIT_MS);
    printf("  fixed wait %ums\r\n", (unsigned)SU3_UNCHECKED_RESULT_WAIT_MS);
    return true;
#else
    while (waited_ms <= timeout_ms) {
        spu_link_read_status_raw(link, raw);
        if (((raw[2] & 0x10u) != 0u) && ((raw[3] & 1u) == 0u)) {
            printf("  wait status raw=%02X %02X %02X %02X waited=%" PRIu32 "ms\r\n",
                   raw[0], raw[1], raw[2], raw[3], waited_ms);
            return true;
        }
        sleep_ms(5);
        waited_ms += 5;
    }

    printf("  wait timeout raw=%02X %02X %02X %02X waited=%" PRIu32 "ms\r\n",
           raw[0], raw[1], raw[2], raw[3], waited_ms);
    return false;
#endif
}

static bool load_matrix(spu_link_t *link, uint8_t op,
                        const uint32_t matrix[9][8]) {
    for (uint8_t elem = 0; elem < 9; elem++) {
        for (uint8_t word_idx = 0; word_idx < 8; word_idx++) {
            uint8_t next_state;
            uint8_t next_stream;
            uint8_t next_chunk;

            if (word_idx != 7) {
                next_state = (op == OP_SU3_LOAD_A) ? SU3_SIDE_LOAD_A : SU3_SIDE_LOAD_B;
                next_stream = elem;
                next_chunk = word_idx + 1;
            } else if (elem != 8) {
                next_state = (op == OP_SU3_LOAD_A) ? SU3_SIDE_LOAD_A : SU3_SIDE_LOAD_B;
                next_stream = elem + 1;
                next_chunk = 0;
            } else if (op == OP_SU3_LOAD_A) {
                next_state = SU3_SIDE_LOAD_B;
                next_stream = 0;
                next_chunk = 0;
            } else {
                next_state = SU3_SIDE_IDLE;
                next_stream = 0;
                next_chunk = 0;
            }

            if (!send_word_probe(link, inst_load(op, elem, word_idx,
                                                 matrix[elem][word_idx]),
                                 next_state, next_stream, next_chunk)) {
                return false;
            }
        }
    }
    return true;
}

static bool run_case(spu_link_t *link, const su3_case_t *test) {
    uint8_t qr[SPU_LINK_QR_BYTES] = {0};
    uint8_t lane;
    uint64_t a;
    uint64_t b;
    uint64_t c;
    uint64_t d;
    bool valid;
    bool ok;

    printf("case elem=%u lane=%u\r\n", test->elem, test->lane);
    if (!send_word_probe(link, inst_start(test->elem),
                         SU3_SIDE_LOAD_A, 0, 0)) {
        return false;
    }
    if (!load_matrix(link, OP_SU3_LOAD_A, dense_a) ||
        !load_matrix(link, OP_SU3_LOAD_B, dense_b)) {
        return false;
    }
    if (!wait_sidecar_idle(link, 2000)) {
        return false;
    }
    if (!send_read_checked(link, inst_read(test->lane, test->elem))) {
        return false;
    }
    sleep_ms(1);

    spu_link_read_qr(link, qr);
    valid = (qr[0] & 1u) != 0;
    lane = qr[1] & 0x0fu;
    a = read_be64(&qr[2]);
    b = read_be64(&qr[10]);
    c = read_be64(&qr[18]);
    d = read_be64(&qr[26]);

    ok = valid && lane == test->lane &&
         a == test->exp_a && b == test->exp_b &&
         c == test->exp_c && d == test->exp_d;

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
    spu_link_set_timing(&link, SU3_LINK_CS_SETUP_US,
                        SU3_LINK_CMD_TURNAROUND_US,
                        SU3_LINK_CRC_HOLD_US,
                        SU3_LINK_CS_RECOVERY_US);

    while (true) {
        if (!stdio_usb_connected()) {
            sleep_ms(100);
            continue;
        }

        bool pass = true;

        printf("\r\n=== Wukong J11 SU3 smoke run %" PRIu32 " ===\r\n", run++);
        printf("pins miso=GP%d cs=GP%d sck=GP%d mosi=GP%d spi_baud=%u\r\n",
               SPU_SPI_MISO_PIN, SPU_SPI_CS_PIN, SPU_SPI_SCK_PIN,
               SPU_SPI_MOSI_PIN, (unsigned)SPI_BAUD_HZ);
        printf("timing cs_setup=%uus turnaround=%uus crc_hold=%uus recovery=%uus\r\n",
               (unsigned)SU3_LINK_CS_SETUP_US,
               (unsigned)SU3_LINK_CMD_TURNAROUND_US,
               (unsigned)SU3_LINK_CRC_HOLD_US,
               (unsigned)SU3_LINK_CS_RECOVERY_US);
        printf("status_checks=%u word_delay=%uus result_wait=%ums\r\n",
               (unsigned)SU3_SMOKE_USE_STATUS_CHECKS,
               (unsigned)SU3_UNCHECKED_WORD_DELAY_US,
               (unsigned)SU3_UNCHECKED_RESULT_WAIT_MS);
        print_status(&link, "before");

        for (size_t i = 0; i < sizeof(su3_cases) / sizeof(su3_cases[0]); i++) {
            if (!run_case(&link, &su3_cases[i])) {
                pass = false;
            }
        }

        printf("SU3_J11: %s\r\n", pass ? "PASS" : "FAIL");
        sleep_ms(1500);
    }
}
