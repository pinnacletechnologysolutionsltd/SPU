#ifndef SPU_SD_H
#define SPU_SD_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

bool spu_sd_init(void);
bool spu_sd_mounted(void);
int  spu_sd_read_blocks(uint32_t lba, uint8_t *buf, uint32_t count);
int  spu_sd_write_blocks(uint32_t lba, const uint8_t *buf, uint32_t count);

#ifdef __cplusplus
}
#endif

#endif
