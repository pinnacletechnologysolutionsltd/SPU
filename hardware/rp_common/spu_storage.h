#ifndef SPU_STORAGE_H
#define SPU_STORAGE_H

#include "spu_link.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

bool spu_storage_init(void);
bool spu_storage_mounted(void);
int  spu_storage_hydrate_from_sd(spu_link_t *link, const char *pack_name);

#ifdef __cplusplus
}
#endif

#endif
