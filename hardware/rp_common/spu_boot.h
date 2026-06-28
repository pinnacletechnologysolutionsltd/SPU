#ifndef SPU_BOOT_H
#define SPU_BOOT_H

#include "spu_link.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SPU_BOOT_DEFAULT_LOCK_LFI      0xF000u
#define SPU_BOOT_DEFAULT_TIMEOUT_MS    1000u
#define SPU_BOOT_TURBULENCE_FLAG_MASK  0x04u

typedef struct {
    uint16_t lock_lfi;
    uint32_t timeout_ms;
    bool verbose;
} spu_boot_options_t;

void spu_boot_hydrate_defaults(spu_link_t *link);
void spu_boot_hydrate_defaults_cb(spu_link_t *link, void *ctx);
bool spu_boot_symmetry_breath(spu_link_t *link,
                              const spu_boot_options_t *options);

#ifdef __cplusplus
}
#endif

#endif // SPU_BOOT_H
