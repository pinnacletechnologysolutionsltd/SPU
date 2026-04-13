#ifndef RP2350_SD_DRIVER_H
#define RP2350_SD_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

#define SD_BLOCK_SIZE 512

typedef enum {
    SD_OK = 0,
    SD_ERR_NO_CARD = -1,
    SD_ERR_IO = -2,
    SD_ERR_NOT_INIT = -3,
    SD_ERR_UNSUPPORTED = -4
} sd_status_t;

#ifdef __cplusplus
extern "C" {
#endif

// Initialize SDIO (preferred) or configure SPI fallback. Returns SD_OK on success.
int sdio_init(void);
void sdio_deinit(void);

// Presence detection
bool sdio_card_present(void);

// Blocking block I/O (512-byte blocks)
sd_status_t sdio_read_blocks(uint32_t lba, uint32_t count, void *buf);
sd_status_t sdio_write_blocks(uint32_t lba, uint32_t count, const void *buf);

// DMA-accelerated variants (optional; dma_chan is implementation-defined)
sd_status_t sdio_read_blocks_dma(uint32_t lba, uint32_t count, void *buf, int dma_chan);
sd_status_t sdio_write_blocks_dma(uint32_t lba, uint32_t count, const void *buf, int dma_chan);

// Filesystem mounting helpers (recommended: FatFS or LittleFS integration)
int sdio_mount_fs(void);
int sdio_unmount_fs(void);

#ifdef __cplusplus
}
#endif

#endif // RP2350_SD_DRIVER_H
