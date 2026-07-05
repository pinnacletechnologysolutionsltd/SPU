// rp2350_rplu2_j11_smoke.c
// Target: Raspberry Pi Pico 2 / RP2350-Zero
// Role: Wukong J11 RPLU2 config-transport and consume-profile smoke test.
//
// Wiring:
//   SPI0 MISO GP0, CS GP1, SCK GP2, MOSI GP3 -> Wukong J11
//   J11-1 CS#, J11-2 SCK, J11-3 MOSI, J11-4 MISO
//
// Build with -DSPU_RP2350_ZERO_HEADER_SPI=ON.

#include "hardware/spi.h"
#include "hardware/gpio.h"
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

#ifndef RPLU2_LINK_CS_SETUP_US
#define RPLU2_LINK_CS_SETUP_US       1000
#endif
#ifndef RPLU2_LINK_CMD_TURNAROUND_US
#define RPLU2_LINK_CMD_TURNAROUND_US 1000
#endif
#ifndef RPLU2_LINK_CRC_HOLD_US
#define RPLU2_LINK_CRC_HOLD_US       1000
#endif
#ifndef RPLU2_LINK_CS_RECOVERY_US
#define RPLU2_LINK_CS_RECOVERY_US    1000
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

#define RPLU2_CONSUME_RECORDS 149u
#define RPLU2_EXPECTED_SUM    0x0AA480E7u
#define RPLU2_CONSUME_PASS    0xC02E0001u
#define RPLU2_QR_PROBE_WORD   0x1D01000A141E2800ull
#define RPLU2_QSUB_QR1_WORD   0x1D01000A141E2800ull
#define RPLU2_QSUB_QR2_WORD   0x1D02000102030400ull
#define RPLU2_QSUB_PROBE_WORD 0x1B03010000000200ull

#ifndef RPLU2_CHECK_EACH_WRITE
#define RPLU2_CHECK_EACH_WRITE 1
#endif

#ifndef RPLU2_BITBANG_SPI
#define RPLU2_BITBANG_SPI 1
#endif

#ifndef RPLU2_BB_HALF_PERIOD_US
#define RPLU2_BB_HALF_PERIOD_US 20
#endif

typedef struct {
    bool magic_ok;
    uint16_t count;
    uint8_t sel;
    uint8_t material;
    uint16_t addr;
    uint64_t data;
    uint32_t checksum;
    uint32_t rplu2_sum;
    uint32_t rplu2_status;
    uint32_t rplu2_num0;
    uint32_t rplu2_delta;
    uint32_t rplu2_row1;
    uint32_t rplu2_kappa;
    uint8_t raw[SPU_LINK_SENTINEL_BYTES];
} cfgtele_t;

typedef struct {
    bool valid;
    uint8_t lane;
    int32_t a;
    int32_t b;
    int32_t c;
    int32_t d;
    uint8_t raw[SPU_LINK_QR_BYTES];
} qrtele_t;

static uint16_t read_be16(const uint8_t *bytes) {
    return ((uint16_t)bytes[0] << 8) | bytes[1];
}

static uint32_t read_be32(const uint8_t *bytes) {
    return ((uint32_t)bytes[0] << 24) |
           ((uint32_t)bytes[1] << 16) |
           ((uint32_t)bytes[2] << 8) |
           bytes[3];
}

static uint64_t read_be64(const uint8_t *bytes) {
    uint64_t value = 0;

    for (size_t i = 0; i < 8; i++) {
        value = (value << 8) | bytes[i];
    }
    return value;
}

static void bus_select(spu_link_t *link) {
    gpio_put(link->cs_pin, 0);
    sleep_us(link->cs_setup_us);
}

static void bus_deselect(spu_link_t *link) {
    gpio_put(SPU_SPI_SCK_PIN, 0);
    gpio_put(link->cs_pin, 1);
    sleep_us(link->cs_recovery_us);
}

#if RPLU2_BITBANG_SPI
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
        sleep_us(RPLU2_BB_HALF_PERIOD_US);
        gpio_put(SPU_SPI_SCK_PIN, 1);
        sleep_us(RPLU2_BB_HALF_PERIOD_US);
        in = (uint8_t)((in << 1) | (gpio_get(SPU_SPI_MISO_PIN) & 0x1u));
        gpio_put(SPU_SPI_SCK_PIN, 0);
    }

    gpio_put(SPU_SPI_MOSI_PIN, 0);
    sleep_us(RPLU2_BB_HALF_PERIOD_US);
    return in;
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
#else
static void bitbang_spi_init(void) {
}

static void bus_write_bytes(const uint8_t *bytes, size_t count) {
    spi_write_blocking(SPI_PORT, bytes, count);
}

static void bus_read_bytes(uint8_t *out, size_t count) {
    spi_read_blocking(SPI_PORT, 0x00, out, count);
}
#endif

static void bus_read_command(spu_link_t *link, uint8_t cmd,
                             uint8_t *out, size_t out_len) {
    bus_select(link);
    bus_write_bytes(&cmd, 1);
    sleep_us(link->cmd_turnaround_us);
    bus_read_bytes(out, out_len);
    bus_deselect(link);
}

static void bus_write_rplu_cfg(spu_link_t *link, uint64_t header,
                               uint64_t data) {
    uint8_t cmd = SPU_CMD_WRITE_RPLU_CFG;
    uint8_t header_bytes[8];
    uint8_t data_bytes[8];
    uint8_t crc;

    spu_u64_to_be(header, header_bytes);
    spu_u64_to_be(data, data_bytes);
    crc = spu_crc8_byte(0x00, cmd);
    crc = spu_crc8_bytes(crc, header_bytes, sizeof(header_bytes));
    crc = spu_crc8_bytes(crc, data_bytes, sizeof(data_bytes));

    bus_select(link);
    bus_write_bytes(&cmd, 1);
    bus_write_bytes(header_bytes, sizeof(header_bytes));
    bus_write_bytes(data_bytes, sizeof(data_bytes));
    bus_write_bytes(&crc, 1);
    sleep_us(link->crc_hold_us);
    bus_deselect(link);
}

static void bus_write_instruction(spu_link_t *link, uint64_t word) {
    uint8_t cmd = SPU_CMD_WRITE_CHORD;
    uint8_t word_bytes[8];
    uint8_t crc;

    spu_u64_to_be(word, word_bytes);
    crc = spu_crc8_byte(0x00, cmd);
    crc = spu_crc8_bytes(crc, word_bytes, sizeof(word_bytes));

    bus_select(link);
    bus_write_bytes(&cmd, 1);
    bus_write_bytes(word_bytes, sizeof(word_bytes));
    bus_write_bytes(&crc, 1);
    sleep_us(link->crc_hold_us);
    bus_deselect(link);
}

static cfgtele_t read_cfgtele(spu_link_t *link) {
    cfgtele_t tele = {0};

    bus_read_command(link, SPU_CMD_READ_SENTINEL, tele.raw,
                     SPU_LINK_SENTINEL_BYTES);
    tele.magic_ok = read_be32(&tele.raw[0]) == 0x53505543u;
    if (!tele.magic_ok) {
        return tele;
    }

    tele.count = read_be16(&tele.raw[4]);
    tele.sel = tele.raw[6] & 0x07u;
    tele.material = tele.raw[7];
    tele.addr = read_be16(&tele.raw[8]) & 0x03FFu;
    tele.data = read_be64(&tele.raw[10]);
    tele.checksum = read_be32(&tele.raw[18]);
    tele.rplu2_sum = read_be32(&tele.raw[22]);
    tele.rplu2_status = read_be32(&tele.raw[26]);
    tele.rplu2_num0 = read_be32(&tele.raw[30]);
    tele.rplu2_delta = read_be32(&tele.raw[34]);
    tele.rplu2_row1 = read_be32(&tele.raw[38]);
    tele.rplu2_kappa = read_be32(&tele.raw[42]);
    return tele;
}

static qrtele_t read_qrtele(spu_link_t *link) {
    qrtele_t tele = {0};

    bus_read_command(link, SPU_CMD_READ_QR, tele.raw, SPU_LINK_QR_BYTES);
    tele.valid = (tele.raw[0] & 0x01u) != 0u;
    tele.lane = tele.raw[1] & 0x0Fu;
    tele.a = (int32_t)read_be32(&tele.raw[6]);
    tele.b = (int32_t)read_be32(&tele.raw[14]);
    tele.c = (int32_t)read_be32(&tele.raw[22]);
    tele.d = (int32_t)read_be32(&tele.raw[30]);
    return tele;
}

static cfgtele_t read_cfgtele_retry(spu_link_t *link, uint8_t attempts,
                                    uint32_t delay_ms) {
    cfgtele_t tele = {0};

    for (uint8_t i = 0; i < attempts; i++) {
        tele = read_cfgtele(link);
        if (tele.magic_ok) {
            return tele;
        }
        sleep_ms(delay_ms);
    }
    return tele;
}

static void print_raw_prefix(const cfgtele_t *tele) {
    printf("raw");
    for (size_t i = 0; i < 16; i++) {
        printf(" %02X", tele->raw[i]);
    }
    printf("\r\n");
}

static void print_cfgtele(const char *tag, const cfgtele_t *tele) {
    if (!tele->magic_ok) {
        printf("%s cfgtele magic=BAD ", tag);
        print_raw_prefix(tele);
        return;
    }

    printf("%s cfgtele count=%u last_sel=%u last_material=%u"
           " last_addr=%u last_data=0x%016" PRIX64
           " checksum=0x%08" PRIX32
           " rplu2_sum=0x%08" PRIX32
           " rplu2_status=0x%08" PRIX32
           " rplu2_num0=0x%08" PRIX32
           " rplu2_delta=0x%08" PRIX32
           " rplu2_row1=0x%08" PRIX32
           " rplu2_kappa=0x%08" PRIX32 "\r\n",
           tag, tele->count, tele->sel, tele->material, tele->addr,
           tele->data, tele->checksum, tele->rplu2_sum,
           tele->rplu2_status, tele->rplu2_num0, tele->rplu2_delta,
           tele->rplu2_row1, tele->rplu2_kappa);
}

static void read_status_raw(spu_link_t *link, uint8_t raw[4]) {
    bus_read_command(link, SPU_CMD_READ_STATUS, raw, 4);
}

static bool status_crc_error(const uint8_t raw[4]) {
    return ((raw[3] >> 1) & 0x1u) != 0u;
}

static void print_status(spu_link_t *link, const char *tag) {
    uint8_t raw[4] = {0};

    read_status_raw(link, raw);
    printf("%s status raw=%02X %02X %02X %02X crc_error=%u\r\n",
           tag, raw[0], raw[1], raw[2], raw[3],
           status_crc_error(raw) ? 1u : 0u);
}

static void print_qrtele(const char *tag, const qrtele_t *tele) {
    printf("%s qr valid=%u lane=%u A=%" PRId32 " B=%" PRId32
           " C=%" PRId32 " D=%" PRId32 "\r\n",
           tag, tele->valid ? 1u : 0u, tele->lane,
           tele->a, tele->b, tele->c, tele->d);
}

static void write_cfg(spu_link_t *link, uint8_t sel, uint8_t material,
                      uint16_t addr, uint64_t data) {
    uint64_t header = spu_rplu_header(sel, material, addr);

    bus_write_rplu_cfg(link, header, data);
}

static bool write_cfg_checked(spu_link_t *link, uint16_t record,
                              uint8_t sel, uint8_t material,
                              uint16_t addr, uint64_t data) {
    uint8_t status[4] = {0};

    write_cfg(link, sel, material, addr, data);

#if RPLU2_CHECK_EACH_WRITE
    read_status_raw(link, status);
    if (status_crc_error(status)) {
        printf("  crc_error rec=%u sel=%u material=%u addr=%u"
               " data=0x%016" PRIX64
               " status=%02X %02X %02X %02X\r\n",
               record, sel, material, addr, data,
               status[0], status[1], status[2], status[3]);
        return false;
    }
#else
    (void)record;
#endif

    return true;
}

static void write_coeff_pair(spu_link_t *link, uint8_t sel, uint8_t idx,
                             uint16_t *records, uint32_t c0, uint32_t c1,
                             uint32_t c2, uint32_t c3) {
    uint64_t low = ((uint64_t)c1 << 32) | c0;
    uint64_t high = ((uint64_t)c3 << 32) | c2;

    write_cfg_checked(link, ++(*records), sel, 0, idx, low);
    write_cfg_checked(link, ++(*records), sel, 0, 0x8u | idx, high);
}

static void write_btu_row(spu_link_t *link, uint8_t row,
                          uint16_t *records, uint32_t c0, uint32_t c1,
                          uint32_t c2, uint32_t c3) {
    uint64_t low = ((uint64_t)c1 << 32) | c0;
    uint64_t high = ((uint64_t)c3 << 32) | c2;

    write_cfg_checked(link, ++(*records), 3, 0, row & 0x3Fu, low);
    write_cfg_checked(link, ++(*records), 3, 0, 0x40u | (row & 0x3Fu), high);
}

static uint16_t hydrate_consume_probe(spu_link_t *link) {
    uint16_t records = 0;

    for (uint8_t i = 0; i < 5; i++) {
        if (i == 0) {
            write_coeff_pair(link, 1, i, &records, 2, 0, 0, 0);
        } else {
            write_coeff_pair(link, 1, i, &records, 0, 0, 0, 0);
        }
    }

    for (uint8_t i = 0; i < 5; i++) {
        if (i == 0) {
            write_coeff_pair(link, 2, i, &records, 1, 0, 0, 0);
        } else {
            write_coeff_pair(link, 2, i, &records, 0, 0, 0, 0);
        }
    }

    for (uint8_t row = 0; row < 64; row++) {
        if (row == 1) {
            write_btu_row(link, row, &records, 1, 0, 0, 0);
        } else {
            write_btu_row(link, row, &records, 0, 0, 0, 0);
        }
    }

    write_cfg_checked(link, ++records, 6, 0, 0, 3);
    return records;
}

static bool cfgtele_pass(const cfgtele_t *tele) {
    return tele->magic_ok &&
           tele->count == RPLU2_CONSUME_RECORDS &&
           tele->sel == 6 &&
           tele->material == 0 &&
           tele->addr == 0 &&
           tele->data == 3 &&
           tele->rplu2_sum == RPLU2_EXPECTED_SUM &&
           tele->rplu2_status == RPLU2_CONSUME_PASS &&
           tele->rplu2_num0 == 2 &&
           tele->rplu2_delta == 0 &&
           tele->rplu2_row1 == 1 &&
           tele->rplu2_kappa == 3;
}

static bool qrtele_pass(const qrtele_t *tele, uint8_t lane,
                        int32_t a, int32_t b, int32_t c, int32_t d) {
    return tele->valid &&
           tele->lane == lane &&
           tele->a == a &&
           tele->b == b &&
           tele->c == c &&
           tele->d == d;
}

static bool run_qldi_probe(spu_link_t *link) {
    for (uint8_t attempt = 0; attempt < 2; attempt++) {
        uint8_t status[4] = {0};

        bus_write_instruction(link, RPLU2_QR_PROBE_WORD);
        sleep_ms(5);
        read_status_raw(link, status);

        qrtele_t qr = read_qrtele(link);
        bool ok = !status_crc_error(status) &&
                  qrtele_pass(&qr, 1, 10, 20, 30, 40);

        printf("qldi attempt=%u word=0x%016" PRIX64
               " status=%02X %02X %02X %02X crc_error=%u\r\n",
               attempt + 1u, (uint64_t)RPLU2_QR_PROBE_WORD,
               status[0], status[1], status[2], status[3],
               status_crc_error(status) ? 1u : 0u);
        print_qrtele("qldi", &qr);
        if (ok) {
            return true;
        }
        sleep_ms(5);
    }

    return false;
}

static bool write_inst_read_qr(spu_link_t *link, const char *tag,
                               uint8_t attempt, uint64_t word,
                               uint32_t delay_ms, qrtele_t *qr_out) {
    uint8_t status[4] = {0};

    bus_write_instruction(link, word);
    sleep_ms(delay_ms);
    read_status_raw(link, status);
    *qr_out = read_qrtele(link);

    printf("%s attempt=%u word=0x%016" PRIX64
           " status=%02X %02X %02X %02X crc_error=%u\r\n",
           tag, attempt + 1u, word,
           status[0], status[1], status[2], status[3],
           status_crc_error(status) ? 1u : 0u);
    print_qrtele(tag, qr_out);
    return !status_crc_error(status);
}

static bool run_qsub_probe(spu_link_t *link) {
    for (uint8_t attempt = 0; attempt < 2; attempt++) {
        qrtele_t q1 = {0};
        qrtele_t q2 = {0};
        qrtele_t qs1 = {0};
        qrtele_t qs2 = {0};
        bool crc_ok = true;

        crc_ok &= write_inst_read_qr(link, "qsub_q1", attempt,
                                     RPLU2_QSUB_QR1_WORD, 10, &q1);
        crc_ok &= write_inst_read_qr(link, "qsub_q2", attempt,
                                     RPLU2_QSUB_QR2_WORD, 10, &q2);
        crc_ok &= write_inst_read_qr(link, "qsub", attempt,
                                     RPLU2_QSUB_PROBE_WORD, 10, &qs1);
        sleep_ms(10);
        qs2 = read_qrtele(link);
        print_qrtele("qsub_reread", &qs2);

        bool ok = crc_ok &&
                  qrtele_pass(&q1, 1, 10, 20, 30, 40) &&
                  qrtele_pass(&q2, 2, 1, 2, 3, 4) &&
                  (qrtele_pass(&qs1, 3, 9, 18, 27, 36) ||
                   qrtele_pass(&qs2, 3, 9, 18, 27, 36));
        if (ok) {
            return true;
        }
        sleep_ms(5);
    }

    return false;
}

int main(void) {
    spu_link_t link;
    uint32_t run = 0;

    stdio_init_all();

    spu_link_init(&link, SPI_PORT, SPU_SPI_CS_PIN);
#if RPLU2_BITBANG_SPI
    bitbang_spi_init();
#else
    spi_init(SPI_PORT, SPI_BAUD_HZ);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPU_SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SPI_MISO_PIN, GPIO_FUNC_SPI);
#endif
    spu_link_set_timing(&link,
                        RPLU2_LINK_CS_SETUP_US,
                        RPLU2_LINK_CMD_TURNAROUND_US,
                        RPLU2_LINK_CRC_HOLD_US,
                        RPLU2_LINK_CS_RECOVERY_US);

    while (true) {
        if (!stdio_usb_connected()) {
            sleep_ms(100);
            continue;
        }

        printf("\r\n=== Wukong J11 RPLU2 smoke run %" PRIu32 " ===\r\n", run++);
        printf("pins miso=GP%d cs=GP%d sck=GP%d mosi=GP%d spi_baud=%u"
               " bus=%s timing=%u/%u/%u/%uus\r\n",
               SPU_SPI_MISO_PIN, SPU_SPI_CS_PIN, SPU_SPI_SCK_PIN,
               SPU_SPI_MOSI_PIN, (unsigned)SPI_BAUD_HZ,
#if RPLU2_BITBANG_SPI
               "bitbang",
#else
               "hwspi",
#endif
               (unsigned)RPLU2_LINK_CS_SETUP_US,
               (unsigned)RPLU2_LINK_CMD_TURNAROUND_US,
               (unsigned)RPLU2_LINK_CRC_HOLD_US,
               (unsigned)RPLU2_LINK_CS_RECOVERY_US);
        print_status(&link, "before");

        cfgtele_t before = read_cfgtele_retry(&link, 4, 20);
        print_cfgtele("before", &before);

        if (before.magic_ok && before.count == 0) {
            uint16_t sent = hydrate_consume_probe(&link);
            printf("hydrate_consume_probe sent=%u records\r\n", sent);
            sleep_ms(200);
        } else if (before.magic_ok && before.count == RPLU2_CONSUME_RECORDS) {
            printf("hydrate_consume_probe already present\r\n");
        } else {
            printf("hydrate_consume_probe skipped; reload FPGA for count=0 before hydration\r\n");
        }

        cfgtele_t after = read_cfgtele_retry(&link, 4, 20);
        print_status(&link, "after");
        print_cfgtele("after", &after);
        printf("RPLU2_J11: %s\r\n", cfgtele_pass(&after) ? "PASS" : "FAIL");
        printf("RPLU2CORE_QR: %s\r\n",
               run_qldi_probe(&link) ? "PASS" : "FAIL");
        printf("RPLU2CORE_QSUB: %s\r\n",
               run_qsub_probe(&link) ? "PASS" : "FAIL");
        sleep_ms(1500);
    }
}
