// rp2350_spu_arithmetic_test.c
// Target: Raspberry Pi Pico 2 (RP2350)
// Role: Drive SPU-13 arithmetic/ROTC tests via SPI and verify QR commit results.
//
// Wiring:
//   SPI0 MISO GP0, CS GP1, SCK GP2, MOSI GP3 -> FPGA SPI slave
//   (Matches the RP2350-Zero header-friendly pinout)
//
// Build:
//   cmake -S hardware/rp2350 -B build/rp2350_arithmetic -G Ninja \
//     -DPICO_SDK_PATH=$PICO_SDK_PATH -DSPU_RP2350_ZERO_HEADER_SPI=ON
//   ninja -C build/rp2350_arithmetic rp2350_spu_arithmetic_test
//
// Connection: USB CDC at 115200 baud.

#include "hardware/spi.h"
#include "pico/stdio_usb.h"
#include "pico/stdlib.h"
#include "spu_link.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

// ── Pin configuration ────────────────────────────────────────────────────
#define SPI_PORT     spi0
#ifndef SPI_BAUD_HZ
#define SPI_BAUD_HZ  25000
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

#define SPU_SPI_MISO_PIN_ALIAS  SPU_SPI_MISO_PIN
#define SPU_SPI_CS_PIN_ALIAS    SPU_SPI_CS_PIN
#define SPU_SPI_SCK_PIN_ALIAS   SPU_SPI_SCK_PIN
#define SPU_SPI_MOSI_PIN_ALIAS  SPU_SPI_MOSI_PIN

#define SPI_MISO_PIN SPU_SPI_MISO_PIN
#define SPI_CS_PIN   SPU_SPI_CS_PIN
#define SPI_SCK_PIN  SPU_SPI_SCK_PIN
#define SPI_MOSI_PIN SPU_SPI_MOSI_PIN

// ── Test case definitions ─────────────────────────────────────────────────
#define INST_QLDI(lane, a, b, c, d) \
    ((((uint64_t)0x1D) << 56) | (((uint64_t)(uint8_t)(lane)) << 48) | \
     (((uint64_t)(uint8_t)(a)) << 32) | (((uint64_t)(uint8_t)(b)) << 24) | \
     (((uint64_t)(uint8_t)(c)) << 16) | (((uint64_t)(uint8_t)(d)) << 8))

#define INST_QSUB(dst, lhs, rhs) \
    ((((uint64_t)0x1B) << 56) | (((uint64_t)(uint8_t)(dst)) << 48) | \
     (((uint64_t)(uint8_t)(lhs)) << 40) | (((uint64_t)(uint8_t)(rhs)) << 8))

#define INST_ROTC(dst, src, angle) \
    ((((uint64_t)0x1C) << 56) | (((uint64_t)(uint8_t)(dst)) << 48) | \
     (((uint64_t)(uint8_t)(src)) << 40) | (((uint64_t)(uint8_t)(angle)) << 24))

typedef struct {
    const char *name;
    uint8_t     num_words;
    uint64_t    words[10];
    uint8_t     expected_lane;
    int32_t     expected_A_real, expected_A_surd;
    int32_t     expected_B_real, expected_B_surd;
    int32_t     expected_C_real, expected_C_surd;
    int32_t     expected_D_real, expected_D_surd;
} arithmetic_test_case_t;

static const arithmetic_test_case_t arithmetic_tests[] = {
    { /* [0] QLDI QR0 = (3,0,0,0) */
        .name = "QLDI QR0 = (3,0,0,0)",
        .num_words = 1,
        .words = { INST_QLDI(0, 3, 0, 0, 0) },
        .expected_lane = 0,
        .expected_A_real = 3, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [1] QLDI QR1 = (1,0,0,0) */
        .name = "QLDI QR1 = (1,0,0,0)",
        .num_words = 1,
        .words = { INST_QLDI(1, 1, 0, 0, 0) },
        .expected_lane = 1,
        .expected_A_real = 1, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [2] QSUB QR2 = QR0 - QR1 = (2,0,0,0) */
        .name = "QSUB QR2 = QR0 - QR1 = (2,0,0,0)",
        .num_words = 3,
        .words = { INST_QLDI(0, 3, 0, 0, 0), INST_QLDI(1, 1, 0, 0, 0),
                   INST_QSUB(2, 0, 1) },
        .expected_lane = 2,
        .expected_A_real = 2, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [3] QSUB QR3 = QR1 - QR0 = (-2,0,0,0) */
        .name = "QSUB QR3 = QR1 - QR0 = (-2,0,0,0)",
        .num_words = 3,
        .words = { INST_QLDI(0, 3, 0, 0, 0), INST_QLDI(1, 1, 0, 0, 0),
                   INST_QSUB(3, 1, 0) },
        .expected_lane = 3,
        .expected_A_real = -2, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [4] QLDI QR4 = (-5,-3,7,-1) */
        .name = "QLDI QR4 = (-5,-3,7,-1)",
        .num_words = 1,
        .words = { INST_QLDI(4, -5, -3, 7, -1) },
        .expected_lane = 4,
        .expected_A_real = -5, .expected_A_surd = 0,
        .expected_B_real = -3, .expected_B_surd = 0,
        .expected_C_real = 7, .expected_C_surd = 0,
        .expected_D_real = -1, .expected_D_surd = 0,
    },
    { /* [5] QSUB QR5 = QR4 - QR4 = (0,0,0,0) */
        .name = "QSUB QR5 = QR4 - QR4 = (0,0,0,0)",
        .num_words = 2,
        .words = { INST_QLDI(4, -5, -3, 7, -1), INST_QSUB(5, 4, 4) },
        .expected_lane = 5,
        .expected_A_real = 0, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [6] ROTC angle 0: identity */
        .name = "ROTC angle 0 identity, checked by QSUB zero",
        .num_words = 4,
        .words = { INST_QLDI(0, 1, 2, 3, 4), INST_ROTC(6, 0, 0),
                   INST_QLDI(12, 1, 2, 3, 4), INST_QSUB(1, 6, 12) },
        .expected_lane = 1,
        .expected_A_real = 0, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [7] ROTC angle 1: thirds period-6 */
        .name = "ROTC angle 1 thirds period-6, checked by QSUB zero",
        .num_words = 4,
        .words = { INST_QLDI(0, 1, 2, 3, 4), INST_ROTC(7, 0, 1),
                   INST_QLDI(12, 1, 3, 2, 4), INST_QSUB(2, 7, 12) },
        .expected_lane = 2,
        .expected_A_real = 0, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [8] ROTC angle 2: P5 forward bypass */
        .name = "ROTC angle 2 P5 forward, checked by QSUB zero",
        .num_words = 4,
        .words = { INST_QLDI(0, 1, 2, 3, 4), INST_ROTC(8, 0, 2),
                   INST_QLDI(12, 1, 4, 2, 3), INST_QSUB(3, 8, 12) },
        .expected_lane = 3,
        .expected_A_real = 0, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [9] ROTC angle 3: thirds period-2 */
        .name = "ROTC angle 3 thirds period-2, checked by QSUB zero",
        .num_words = 4,
        .words = { INST_QLDI(0, 1, 2, 3, 4), INST_ROTC(9, 0, 3),
                   INST_QLDI(12, 1, 4, 3, 2), INST_QSUB(4, 9, 12) },
        .expected_lane = 4,
        .expected_A_real = 0, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [10] ROTC angle 4: thirds period-6 inverse */
        .name = "ROTC angle 4 thirds inverse, checked by QSUB zero",
        .num_words = 4,
        .words = { INST_QLDI(0, 1, 2, 3, 4), INST_ROTC(10, 0, 4),
                   INST_QLDI(12, 1, 2, 4, 3), INST_QSUB(5, 10, 12) },
        .expected_lane = 5,
        .expected_A_real = 0, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [11] ROTC angle 5: P5 inverse bypass */
        .name = "ROTC angle 5 P5 inverse, checked by QSUB zero",
        .num_words = 4,
        .words = { INST_QLDI(0, 1, 2, 3, 4), INST_ROTC(11, 0, 5),
                   INST_QLDI(12, 1, 3, 4, 2), INST_QSUB(6, 11, 12) },
        .expected_lane = 6,
        .expected_A_real = 0, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
    { /* [12] ROTC angle 1 six-step closure */
        .name = "ROTC angle 1 six-step closure, checked by QSUB zero",
        .num_words = 8,
        .words = { INST_QLDI(0, 1, 2, 3, 4), INST_ROTC(1, 0, 1),
                   INST_ROTC(2, 1, 1), INST_ROTC(3, 2, 1),
                   INST_ROTC(4, 3, 1), INST_ROTC(5, 4, 1),
                   INST_ROTC(6, 5, 1), INST_QSUB(7, 6, 0) },
        .expected_lane = 7,
        .expected_A_real = 0, .expected_A_surd = 0,
        .expected_B_real = 0, .expected_B_surd = 0,
        .expected_C_real = 0, .expected_C_surd = 0,
        .expected_D_real = 0, .expected_D_surd = 0,
    },
};

#define ARITHMETIC_TEST_COUNT  \
    (sizeof(arithmetic_tests) / sizeof(arithmetic_tests[0]))

// ── Helpers ────────────────────────────────────────────────────────────────

static int32_t be32_to_i32(const uint8_t *b) {
    uint32_t u = ((uint32_t)b[0] << 24) | ((uint32_t)b[1] << 16) |
                 ((uint32_t)b[2] << 8)  |  (uint32_t)b[3];
    return (int32_t)u;
}

static bool read_qr_commit(spu_link_t *link,
                           uint8_t *lane_out,
                           int32_t comp[8]);

static void send_instruction(spu_link_t *link, uint64_t word) {
    uint8_t chord[SPU_LINK_CHORD_BYTES];
    uint8_t status[4] = {0};

    spu_u64_to_be(word, chord);
    spu_link_write_chord(link, chord);
    // Allow time for the core to process the instruction.
    // QSUB is multi-cycle (reads QR file serially); 5 ms is Conservative.
    sleep_ms(5);
    spu_link_read_status_raw(link, status);
    printf("    word=%016" PRIX64 " status=%02X %02X %02X %02X\n",
           word, status[0], status[1], status[2], status[3]);
    if ((uint8_t)(word >> 56) == 0x1C) {
        uint8_t lane = 0;
        int32_t comp[8] = {0};
        bool valid = read_qr_commit(link, &lane, comp);
        printf("      rotc_commit valid=%u lane=%u A=(%d,%d) B=(%d,%d) C=(%d,%d) D=(%d,%d)\n",
               valid ? 1u : 0u, lane,
               (int)comp[0], (int)comp[1],
               (int)comp[2], (int)comp[3],
               (int)comp[4], (int)comp[5],
               (int)comp[6], (int)comp[7]);
    }
}

static bool read_qr_commit(spu_link_t *link,
                           uint8_t *lane_out,
                           int32_t comp[8]) {
    uint8_t qr[SPU_LINK_QR_BYTES];
    spu_link_read_qr(link, qr);

    uint8_t valid = qr[0] & 0x01;
    *lane_out = qr[1] & 0x0F;

    // 2-9: A, 10-17: B, 18-25: C, 26-33: D
    // Each is 8 bytes big-endian: bytes 0-3=surd coeff, 4-7=real
    comp[0] = be32_to_i32(&qr[6]);   // A real  (bytes 6-9 = bits [31:0])
    comp[1] = be32_to_i32(&qr[2]);   // A surd  (bytes 2-5 = bits [63:32])
    comp[2] = be32_to_i32(&qr[14]);  // B real
    comp[3] = be32_to_i32(&qr[10]);  // B surd
    comp[4] = be32_to_i32(&qr[22]);  // C real
    comp[5] = be32_to_i32(&qr[18]);  // C surd
    comp[6] = be32_to_i32(&qr[30]);  // D real
    comp[7] = be32_to_i32(&qr[26]);  // D surd

    return valid != 0;
}

static bool check_result(const arithmetic_test_case_t *test,
                          uint8_t actual_lane,
                          const int32_t actual[8]) {
    const int32_t *exp = &test->expected_A_real;
    bool ok = true;

    if (actual_lane != test->expected_lane) {
        printf("  FAIL: lane mismatch  expected=%u  actual=%u\n",
               test->expected_lane, actual_lane);
        ok = false;
    }

    // Compare A, B, C, D components
    const char *names[] = {"A", "B", "C", "D"};
    for (int i = 0; i < 4; i++) {
        int32_t er = exp[i * 2];
        int32_t es = exp[i * 2 + 1];
        int32_t ar = actual[i * 2];
        int32_t as = actual[i * 2 + 1];
        if (er != ar || es != as) {
            printf("  FAIL: %s mismatch  exp=(%d,%d)  got=(%d,%d)\n",
                   names[i], (int)er, (int)es, (int)ar, (int)as);
            ok = false;
        }
    }

    if (ok) {
        printf("  PASS\n");
    }
    return ok;
}

// ── Main ───────────────────────────────────────────────────────────────────

int main(void) {
    spu_link_t link;
    int passed = 0;
    int total  = 0;

    stdio_init_all();

    spi_init(SPI_PORT, SPI_BAUD_HZ);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MISO_PIN, GPIO_FUNC_SPI);
    spu_link_init(&link, SPI_PORT, SPI_CS_PIN);

    // Wait for USB CDC
    while (!stdio_usb_connected()) {
        sleep_ms(100);
    }

    printf("\n=== SPU-13 Arithmetic/ROTC Test Driver ===\n");
    printf("SPI baud: %u Hz\n", (unsigned)SPI_BAUD_HZ);
    printf("Tests: %u\n\n", (unsigned)ARITHMETIC_TEST_COUNT);

    for (unsigned i = 0; i < ARITHMETIC_TEST_COUNT; i++) {
        const arithmetic_test_case_t *test = &arithmetic_tests[i];
        total++;

        printf("[%u/%u] %s\n", i + 1, (unsigned)ARITHMETIC_TEST_COUNT,
               test->name);

        // Send all instruction words for this test
        for (unsigned j = 0; j < test->num_words; j++) {
            send_instruction(&link, test->words[j]);
        }

        // Read back QR commit
        uint8_t lane;
        int32_t comp[8];
        bool valid = read_qr_commit(&link, &lane, comp);

        if (!valid) {
            printf("  FAIL: QR commit not valid\n");
            continue;
        }

        // Print actual values for diagnostics
        printf("  lane=%u  A=(%d,%d) B=(%d,%d) C=(%d,%d) D=(%d,%d)\n",
               lane,
               (int)comp[0], (int)comp[1],
               (int)comp[2], (int)comp[3],
               (int)comp[4], (int)comp[5],
               (int)comp[6], (int)comp[7]);

        if (check_result(test, lane, comp)) {
            passed++;
        }
    }

    printf("\n=== Results: %d/%d PASSED ===\n", passed, total);

    if (passed == total) {
        printf("ARITHMETIC_BLAZE: PASS\n");
    } else {
        printf("ARITHMETIC_BLAZE: FAIL (%d failures)\n", total - passed);
    }

    while (1) {
        sleep_ms(1000);
    }
}
