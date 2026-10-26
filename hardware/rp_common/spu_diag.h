#ifndef SPU_DIAG_H
#define SPU_DIAG_H

#include "spu_link.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SPU_DIAG_LINE_MAX 128

typedef void (*spu_diag_hydrate_fn)(spu_link_t *link, void *ctx);

typedef struct {
    spu_link_t *link;
    spu_diag_hydrate_fn hydrate;
    void *hydrate_ctx;
    char line[SPU_DIAG_LINE_MAX];
    size_t len;
} spu_diag_t;

void spu_diag_init(spu_diag_t *diag, spu_link_t *link,
                   spu_diag_hydrate_fn hydrate, void *hydrate_ctx);
void spu_diag_print_banner(void);
void spu_diag_poll(spu_diag_t *diag);

#ifdef __cplusplus
}
#endif

#endif // SPU_DIAG_H
