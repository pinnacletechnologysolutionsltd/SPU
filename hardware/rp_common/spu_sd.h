#ifndef SPU_SD_H
#define SPU_SD_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    SPU_SD_ERR_NONE = 0,
    SPU_SD_ERR_CMD0,
    SPU_SD_ERR_ACMD41,
    SPU_SD_ERR_CMD58,
    SPU_SD_ERR_CMD16,
} spu_sd_error_t;

bool spu_sd_init(void);
bool spu_sd_mounted(void);
spu_sd_error_t spu_sd_last_error(void);
uint8_t spu_sd_last_r1(void);
const char *spu_sd_error_name(spu_sd_error_t error);
int  spu_sd_read_blocks(uint32_t lba, uint8_t *buf, uint32_t count);
int  spu_sd_write_blocks(uint32_t lba, const uint8_t *buf, uint32_t count);

#ifdef __cplusplus
}
#endif

#endif
