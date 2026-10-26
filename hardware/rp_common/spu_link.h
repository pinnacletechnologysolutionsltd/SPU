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
#define SPU_LINK_PADE_TRACE_HEAD_BYTES 33
#define SPU_LINK_PADE_TRACE_OPERAND_BYTES 32
#define SPU_LINK_PADE_TRACE_RESULT_BYTES 16
#define SPU_LINK_SOM1_FRAME_BYTES  52
#define SPU_LINK_TGR_MAX_BYTES    508

// Safe SCK ceilings for spu_spi_slave, which samples SCK with the fabric clock
// and so bounds SCK at clk_fast / 6 (measured: hardware/tests/common/
// spu_spi_slave_ratio_tb.v -- ratio 5 fails at 2 of 4 phase offsets).
//
// Wukong A7-100T board clock is 50 MHz, confirmed on hardware 2026-07-31 via
// tools/uart_baud_probe.py. A7_FREQ is a nextpnr timing constraint and does not
// divide the clock; A7_CLK_DIV_LOG2 does. The two spin classes differ by 64x,
// so there is no single safe rate -- pick by the spin you are talking to.
#define SPU_CORE_SPIN_SCK_CEILING_HZ      130000    // clk_fast 781.25 kHz (/64)
#define SPU_CORELESS_SPIN_SCK_CEILING_HZ 8300000    // clk_fast 50 MHz (raw)

// Tang Primer 25K clocks its southbridge at 50 MHz on the standard spin, so it
// shares the coreless ceiling above; TENSEGRITYLINK runs 25 MHz -> ~4.16 MHz.
#define SPU_TANG_SCK_CEILING_HZ          8300000    // 50 MHz southbridge clock
#define SPU_TANG_LINK_SCK_CEILING_HZ     4160000    // 25 MHz (TENSEGRITYLINK)

// Designs that bypass spu_spi_slave entirely have NO such ceiling -- e.g.
// spu_a7_j11_loopback_top.v clocks on posedge spi_sck directly and drives MISO
// combinationally, so nothing samples SCK with a fabric clock. Pass 0.

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
    SPU_CMD_READ_PADE_TRACE_HEAD = 0xB4,
    SPU_CMD_READ_PADE_TRACE_OPERANDS = 0xB5,
    SPU_CMD_READ_PADE_TRACE_RESULT = 0xB6,
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

// Report the SPI rate actually achieved by spi_init(), which is NOT always the
// rate requested: the PL022 divides clk_peri by CPSDVSR * (1 + SCR) with
// CPSDVSR even, so attainable rates are quantized. Every firmware in this tree
// historically discarded spi_init()'s return value, which meant a rate that
// quantized upward past the slave's ceiling would look identical to one that
// did not.
//
// That ceiling is a ratio, not a constant: spu_spi_slave samples SCK with the
// fabric clock, so SCK must be <= clk_fast / 6 (measured by
// hardware/tests/common/spu_spi_slave_ratio_tb.v). On a divided A7 core spin
// clk_fast is 781.25 kHz, giving a 130 kHz ceiling; on coreless spins it is
// 50 MHz, giving 8.3 MHz. See docs/SOUTHBRIDGE_SPI_PROTOCOL.md.
//
// Pass the achieved rate (spi_init's return) and what you asked for. Prints
// both, and warns when they differ or when the achieved rate exceeds
// core_spin_ceiling_hz. Pass 0 for the ceiling to skip that check.
void spu_link_report_baud(uint actual_hz, uint requested_hz,
                          uint core_spin_ceiling_hz);

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
