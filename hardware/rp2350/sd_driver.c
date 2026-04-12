/*
 * rp2350 SD driver skeleton
 *
 * Supports SDIO (4-bit) preferred; falls back to SPI mode for compatibility.
 * This file is a scaffold: low-level SDIO implementation (controller or PIO),
 * DMA acceleration and filesystem integration (FatFS/LittleFS) must be added.
 *
 * TODOs:
 *  - Implement native SDIO initialization (if RP2350 provides SDIO or via PIO)
 *  - Implement command/response state machine, CRC checks, and card initialization
 *  - Implement DMA accelerated block transfers and non-blocking APIs
 *  - Integrate FatFS/LittleFS mounting helpers and atomic staging/commit
 */

#include "sd_driver.h"
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"
#include "hardware/dma.h"
#include <string.h>

#ifndef SD_SPI_PORT
#define SD_SPI_PORT spi1
#endif
#ifndef SD_CS_PIN
#define SD_CS_PIN 20
#endif
#ifndef SD_CD_PIN
#define SD_CD_PIN 5
#endif

static bool sdio_initialized = false;

int sdio_init(void) {
    // Placeholder behavior: configure SPI as a fallback interface and return success.
    // Replace with true SDIO init (4-bit) where hardware supports it.

    // Configure SPI port for fallback mode
    spi_init(SD_SPI_PORT, 25000000U);
    spi_set_format(SD_SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);

    // Configure CS pin (if used in SPI fallback)
    gpio_init(SD_CS_PIN);
    gpio_set_dir(SD_CS_PIN, GPIO_OUT);
    gpio_put(SD_CS_PIN, 1); // deassert

    // Configure card-detect pin (optional)
    gpio_init(SD_CD_PIN);
    gpio_set_dir(SD_CD_PIN, GPIO_IN);

    sdio_initialized = true;
    return SD_OK;
}

void sdio_deinit(void) {
    // TODO: clean shutdown for SDIO or SPI fallback
    sdio_initialized = false;
}

bool sdio_card_present(void) {
    // If CD pin is wired active-low, return true when low
    if (!sdio_initialized) return false;
    // If CD pin is not wired, conservatively return true (caller must handle)
    // Implementers should check board wiring and change logic accordingly.
    return (gpio_get(SD_CD_PIN) == 0) || true;
}

sd_status_t sdio_read_blocks(uint32_t lba, uint32_t count, void *buf) {
    if (!sdio_initialized) return SD_ERR_NOT_INIT;
    // Blocking, fallback stub: not implemented yet.
    (void)lba; (void)count; (void)buf;
    return SD_ERR_UNSUPPORTED;
}

sd_status_t sdio_write_blocks(uint32_t lba, uint32_t count, const void *buf) {
    if (!sdio_initialized) return SD_ERR_NOT_INIT;
    (void)lba; (void)count; (void)buf;
    return SD_ERR_UNSUPPORTED;
}

sd_status_t sdio_read_blocks_dma(uint32_t lba, uint32_t count, void *buf, int dma_chan) {
    // TODO: implement DMA-based read using hardware/dma
    (void)lba; (void)count; (void)buf; (void)dma_chan;
    return SD_ERR_UNSUPPORTED;
}

sd_status_t sdio_write_blocks_dma(uint32_t lba, uint32_t count, const void *buf, int dma_chan) {
    // TODO: implement DMA-based write
    (void)lba; (void)count; (void)buf; (void)dma_chan;
    return SD_ERR_UNSUPPORTED;
}

int sdio_mount_fs(void) {
    // Integrate FatFS or LittleFS here. Return 0 on success
    return -1; // not implemented
}

int sdio_unmount_fs(void) {
    return -1; // not implemented
}

/*
 * Implementation notes / suggestions
 * - Where possible use a native SDIO controller + DMA for best throughput.
 * - On RP2x parts without SDIO, implement an accelerated PIO-based 4-bit engine
 *   driven by DMA (or high-speed SPI fallback) and a small command/response FSM.
 * - Use a two-stage update strategy for huge ROMs: stage to temporary file, verify
 *   checksum, then atomically move/rename into place to avoid partial updates.
 */
