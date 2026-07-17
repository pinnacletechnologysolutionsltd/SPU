#ifndef SPU_LINK_H
#define SPU_LINK_H

#include "hardware/spi.h"
#include "pico/types.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SPU_LINK_AXES             13
#define SPU_LINK_BYTES_PER_AXIS    8
#define SPU_LINK_FRAME_BYTES      (SPU_LINK_AXES * SPU_LINK_BYTES_PER_AXIS)
#define SPU_LINK_SPU4_AXES         4
#define SPU_LINK_MANIFOLD_BYTES   (SPU_LINK_SPU4_AXES * SPU_LINK_BYTES_PER_AXIS)
#define SPU_LINK_SCALE_BYTES       9
#define SPU_LINK_CHORD_BYTES       8
#define SPU_LINK_QR_BYTES          34
#define SPU_LINK_HEX_BYTES         5
#define SPU_LINK_SENTINEL_BYTES    64
#define SPU_LINK_TGR_STATUS_BYTES  16
#define SPU_LINK_SOM1_FRAME_BYTES  52
#define SPU_LINK_TGR_MAX_BYTES    508

typedef enum {
    SPU_CMD_READ_SOM1      = 0x02,
    SPU_CMD_READ_MANIFOLD  = 0xA0,
    SPU_CMD_READ_STATUS    = 0xAC,
    SPU_CMD_READ_SCALE     = 0xAD,
    SPU_CMD_READ_QR        = 0xAE,
    SPU_CMD_READ_HEX       = 0xAF,
    SPU_CMD_READ_SENTINEL  = 0xB0,
    SPU_CMD_WRITE_CHORD    = 0xB1,
    SPU_CMD_WRITE_TGR1     = 0xB2,
    SPU_CMD_READ_TGR_STATUS= 0xB3,
    SPU_CMD_WRITE_RPLU_CFG = 0xA5
} spu_cmd_t;

typedef struct {
    spi_inst_t *spi;
    uint cs_pin;
    uint32_t cs_setup_us;
    uint32_t cmd_turnaround_us;
    uint32_t crc_hold_us;
    uint32_t cs_recovery_us;
} spu_link_t;

void spu_link_init(spu_link_t *link, spi_inst_t *spi, uint cs_pin);
void spu_link_set_timing(spu_link_t *link, uint32_t cs_setup_us,
                         uint32_t cmd_turnaround_us, uint32_t crc_hold_us,
                         uint32_t cs_recovery_us);

void spu_link_read_manifold(spu_link_t *link,
                            uint8_t out[SPU_LINK_MANIFOLD_BYTES]);
void spu_link_read_status_raw(spu_link_t *link, uint8_t out[4]);
void spu_link_read_status(spu_link_t *link, uint16_t *dissonance,
                          uint8_t *flags);
void spu_link_read_status_full(spu_link_t *link, uint16_t *dissonance,
                               uint8_t *flags, bool *crc_error);
void spu_link_read_scale_table(spu_link_t *link,
                               uint8_t out[SPU_LINK_SCALE_BYTES]);
void spu_link_read_qr(spu_link_t *link,
                      uint8_t out[SPU_LINK_QR_BYTES]);
void spu_link_read_hex(spu_link_t *link,
                       uint8_t out[SPU_LINK_HEX_BYTES]);
void spu_link_read_sentinel(spu_link_t *link,
                            uint8_t out[SPU_LINK_SENTINEL_BYTES]);
void spu_link_read_tgr_status(spu_link_t *link,
                              uint8_t out[SPU_LINK_TGR_STATUS_BYTES]);
void spu_link_read_som1(spu_link_t *link,
                        uint8_t out[SPU_LINK_SOM1_FRAME_BYTES]);

bool spu_link_fifo_full(spu_link_t *link);
void spu_link_wait_artery_ready(spu_link_t *link);
void spu_link_write_chord(spu_link_t *link,
                          const uint8_t chord[SPU_LINK_CHORD_BYTES]);
void spu_link_write_chord_nowait(spu_link_t *link,
                                 const uint8_t chord[SPU_LINK_CHORD_BYTES]);

void spu_u64_to_be(uint64_t v, uint8_t out[8]);
uint64_t spu_rplu_header(uint8_t sel, uint8_t material, uint16_t addr);
void spu_link_write_rplu_cfg(spu_link_t *link, uint64_t header,
                             uint64_t data);
bool spu_link_write_tgr1(spu_link_t *link, uint32_t vector_id,
                         const uint8_t *table, uint16_t table_len);

// CRC-8-CCITT: x⁸ + x² + x + 1 (polynomial 0x07)
uint8_t spu_crc8_byte(uint8_t crc, uint8_t byte);
uint8_t spu_crc8_bytes(uint8_t crc, const uint8_t *data, uint len);

#ifdef __cplusplus
}
#endif

#endif // SPU_LINK_H
