#include "spu_link.h"

#include <string.h>
#include "hardware/gpio.h"
#include "pico/stdlib.h"

#ifndef SPU_LINK_CS_SETUP_US
#define SPU_LINK_CS_SETUP_US 1000
#endif

#ifndef SPU_LINK_CMD_TURNAROUND_US
#define SPU_LINK_CMD_TURNAROUND_US 1000
#endif

#ifndef SPU_LINK_CRC_HOLD_US
#define SPU_LINK_CRC_HOLD_US 1000
#endif

#ifndef SPU_LINK_CS_RECOVERY_US
#define SPU_LINK_CS_RECOVERY_US 1000
#endif

// ── CRC-8-CCITT: x⁸ + x² + x + 1 (polynomial 0x07) ──────────────
uint8_t spu_crc8_byte(uint8_t crc, uint8_t byte) {
    for (int b = 0; b < 8; b++) {
        if (((crc >> 7) & 1u) != ((byte >> (7 - b)) & 1u)) {
            crc = (crc << 1) ^ 0x07;
        } else {
            crc = crc << 1;
        }
    }
    return crc;
}

uint8_t spu_crc8_bytes(uint8_t crc, const uint8_t *data, uint len) {
    for (uint i = 0; i < len; i++) {
        crc = spu_crc8_byte(crc, data[i]);
    }
    return crc;
}

static void spu_link_select(spu_link_t *link) {
    gpio_put(link->cs_pin, 0);
    sleep_us(link->cs_setup_us);
}

static void spu_link_deselect(spu_link_t *link) {
    gpio_put(link->cs_pin, 1);
    sleep_us(link->cs_recovery_us);
}

static void spu_link_read_turnaround(spu_link_t *link) {
    sleep_us(link->cmd_turnaround_us);
}

void spu_link_init(spu_link_t *link, spi_inst_t *spi, uint cs_pin) {
    link->spi = spi;
    link->cs_pin = cs_pin;

    gpio_init(cs_pin);
    gpio_set_dir(cs_pin, GPIO_OUT);
    gpio_put(cs_pin, 1);

    link->cs_setup_us = SPU_LINK_CS_SETUP_US;
    link->cmd_turnaround_us = SPU_LINK_CMD_TURNAROUND_US;
    link->crc_hold_us = SPU_LINK_CRC_HOLD_US;
    link->cs_recovery_us = SPU_LINK_CS_RECOVERY_US;
}

void spu_link_set_timing(spu_link_t *link, uint32_t cs_setup_us,
                         uint32_t cmd_turnaround_us, uint32_t crc_hold_us,
                         uint32_t cs_recovery_us) {
    link->cs_setup_us = cs_setup_us;
    link->cmd_turnaround_us = cmd_turnaround_us;
    link->crc_hold_us = crc_hold_us;
    link->cs_recovery_us = cs_recovery_us;
}

void spu_link_read_manifold(spu_link_t *link,
                            uint8_t out[SPU_LINK_MANIFOLD_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_MANIFOLD;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spu_link_read_turnaround(link);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_MANIFOLD_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_status_raw(spu_link_t *link, uint8_t out[4]) {
    uint8_t cmd = SPU_CMD_READ_STATUS;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spu_link_read_turnaround(link);
    spi_read_blocking(link->spi, 0x00, out, 4);
    spu_link_deselect(link);
}

void spu_link_read_status(spu_link_t *link, uint16_t *dissonance,
                          uint8_t *flags) {
    uint8_t resp[4] = {0};

    spu_link_read_status_raw(link, resp);
    *dissonance = ((uint16_t)resp[0] << 8) | resp[1];
    *flags = resp[2];
}

void spu_link_read_status_full(spu_link_t *link, uint16_t *dissonance,
                               uint8_t *flags, bool *crc_error) {
    uint8_t resp[4] = {0};

    spu_link_read_status_raw(link, resp);
    *dissonance = ((uint16_t)resp[0] << 8) | resp[1];
    *flags = resp[2];
    *crc_error = (resp[3] >> 1) & 1;
}

void spu_link_read_scale_table(spu_link_t *link,
                               uint8_t out[SPU_LINK_SCALE_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_SCALE;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spu_link_read_turnaround(link);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_SCALE_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_qr(spu_link_t *link,
                      uint8_t out[SPU_LINK_QR_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_QR;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spu_link_read_turnaround(link);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_QR_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_hex(spu_link_t *link,
                       uint8_t out[SPU_LINK_HEX_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_HEX;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spu_link_read_turnaround(link);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_HEX_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_sentinel(spu_link_t *link,
                            uint8_t out[SPU_LINK_SENTINEL_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_SENTINEL;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spu_link_read_turnaround(link);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_SENTINEL_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_tgr_status(spu_link_t *link,
                              uint8_t out[SPU_LINK_TGR_STATUS_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_TGR_STATUS;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spu_link_read_turnaround(link);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_TGR_STATUS_BYTES);
    spu_link_deselect(link);
}

bool spu_link_fifo_full(spu_link_t *link) {
    uint16_t dissonance;
    uint8_t flags;

    spu_link_read_status(link, &dissonance, &flags);
    (void)dissonance;
    return ((flags >> 3) & 0x1) != 0;
}

void spu_link_wait_artery_ready(spu_link_t *link) {
    while (spu_link_fifo_full(link)) {
        sleep_us(10);
    }
}

void spu_link_write_chord(spu_link_t *link,
                          const uint8_t chord[SPU_LINK_CHORD_BYTES]) {
    spu_link_wait_artery_ready(link);
    spu_link_write_chord_nowait(link, chord);
}

void spu_link_write_chord_nowait(spu_link_t *link,
                                 const uint8_t chord[SPU_LINK_CHORD_BYTES]) {
    uint8_t cmd = SPU_CMD_WRITE_CHORD;
    uint8_t crc;

    // Compute CRC over command byte + payload
    crc = spu_crc8_byte(0x00, cmd);
    crc = spu_crc8_bytes(crc, chord, SPU_LINK_CHORD_BYTES);

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_write_blocking(link->spi, chord, SPU_LINK_CHORD_BYTES);
    spi_write_blocking(link->spi, &crc, 1);  // CRC-8 trailer
    sleep_us(link->crc_hold_us);
    spu_link_deselect(link);
}

void spu_u64_to_be(uint64_t v, uint8_t out[8]) {
    for (int i = 0; i < 8; i++) {
        out[i] = (uint8_t)((v >> (56 - 8 * i)) & 0xFFu);
    }
}

uint64_t spu_rplu_header(uint8_t sel, uint8_t material, uint16_t addr) {
    return ((uint64_t)SPU_CMD_WRITE_RPLU_CFG << 56) |
           ((uint64_t)(sel & 0x7) << 48) |
           ((uint64_t)(material & 0xF) << 44) |
           ((uint64_t)(addr & 0x3FF) << 34);
}

void spu_link_write_rplu_cfg(spu_link_t *link, uint64_t header,
                             uint64_t data) {
    uint8_t cmd = SPU_CMD_WRITE_RPLU_CFG;
    uint8_t header_bytes[8];
    uint8_t data_bytes[8];
    uint8_t crc;

    spu_u64_to_be(header, header_bytes);
    spu_u64_to_be(data, data_bytes);

    // CRC over command byte + header + data
    crc = spu_crc8_byte(0x00, cmd);
    crc = spu_crc8_bytes(crc, header_bytes, sizeof(header_bytes));
    crc = spu_crc8_bytes(crc, data_bytes, sizeof(data_bytes));

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_write_blocking(link->spi, header_bytes, sizeof(header_bytes));
    spi_write_blocking(link->spi, data_bytes, sizeof(data_bytes));
    spi_write_blocking(link->spi, &crc, 1);
    sleep_us(link->crc_hold_us);
    spu_link_deselect(link);
}

bool spu_link_write_tgr1(spu_link_t *link, uint32_t vector_id,
                         const uint8_t *table, uint16_t table_len) {
    uint8_t cmd = SPU_CMD_WRITE_TGR1;
    uint8_t prefix[6];
    uint8_t crc;

    if (table == NULL || table_len < 12 || table_len > SPU_LINK_TGR_MAX_BYTES) {
        return false;
    }

    prefix[0] = (uint8_t)(table_len >> 8);
    prefix[1] = (uint8_t)table_len;
    prefix[2] = (uint8_t)(vector_id >> 24);
    prefix[3] = (uint8_t)(vector_id >> 16);
    prefix[4] = (uint8_t)(vector_id >> 8);
    prefix[5] = (uint8_t)vector_id;

    crc = spu_crc8_byte(0x00, cmd);
    crc = spu_crc8_bytes(crc, prefix, sizeof(prefix));
    crc = spu_crc8_bytes(crc, table, table_len);

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_write_blocking(link->spi, prefix, sizeof(prefix));
    spi_write_blocking(link->spi, table, table_len);
    spi_write_blocking(link->spi, &crc, 1);
    sleep_us(link->crc_hold_us);
    spu_link_deselect(link);
    return true;
}
