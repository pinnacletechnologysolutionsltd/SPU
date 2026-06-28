#include "spu_link.h"

#include "hardware/gpio.h"
#include "pico/stdlib.h"

static void spu_link_select(spu_link_t *link) {
    gpio_put(link->cs_pin, 0);
}

static void spu_link_deselect(spu_link_t *link) {
    gpio_put(link->cs_pin, 1);
}

void spu_link_init(spu_link_t *link, spi_inst_t *spi, uint cs_pin) {
    link->spi = spi;
    link->cs_pin = cs_pin;

    gpio_init(cs_pin);
    gpio_set_dir(cs_pin, GPIO_OUT);
    gpio_put(cs_pin, 1);
}

void spu_link_read_manifold(spu_link_t *link,
                            uint8_t out[SPU_LINK_MANIFOLD_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_MANIFOLD;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_MANIFOLD_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_status_raw(spu_link_t *link, uint8_t out[4]) {
    uint8_t cmd = SPU_CMD_READ_STATUS;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
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

void spu_link_read_scale_table(spu_link_t *link,
                               uint8_t out[SPU_LINK_SCALE_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_SCALE;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_SCALE_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_qr(spu_link_t *link,
                      uint8_t out[SPU_LINK_QR_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_QR;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_QR_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_hex(spu_link_t *link,
                       uint8_t out[SPU_LINK_HEX_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_HEX;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_HEX_BYTES);
    spu_link_deselect(link);
}

void spu_link_read_sentinel(spu_link_t *link,
                            uint8_t out[SPU_LINK_SENTINEL_BYTES]) {
    uint8_t cmd = SPU_CMD_READ_SENTINEL;

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_read_blocking(link->spi, 0x00, out, SPU_LINK_SENTINEL_BYTES);
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
    uint8_t cmd = SPU_CMD_WRITE_CHORD;

    spu_link_wait_artery_ready(link);

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_write_blocking(link->spi, chord, SPU_LINK_CHORD_BYTES);
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

    spu_u64_to_be(header, header_bytes);
    spu_u64_to_be(data, data_bytes);

    spu_link_select(link);
    spi_write_blocking(link->spi, &cmd, 1);
    spi_write_blocking(link->spi, header_bytes, sizeof(header_bytes));
    spi_write_blocking(link->spi, data_bytes, sizeof(data_bytes));
    spu_link_deselect(link);
}
