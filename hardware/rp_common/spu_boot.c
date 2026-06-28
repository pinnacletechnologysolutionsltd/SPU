#include "spu_boot.h"

#include "pico/stdlib.h"
#include "rplu_default_tables.h"
#include <stdio.h>

void spu_boot_hydrate_defaults(spu_link_t *link) {
    for (int i = 0; i < 3; i++) {
        uint64_t header = spu_rplu_header(0, 0, (uint16_t)i);
        spu_link_write_rplu_cfg(link, header, (uint64_t)RPLU_PARAMS_CARBON[i]);
        sleep_us(50);
    }

    for (int i = 0; i < 3; i++) {
        uint64_t header = spu_rplu_header(0, 1, (uint16_t)i);
        spu_link_write_rplu_cfg(link, header, (uint64_t)RPLU_PARAMS_IRON[i]);
        sleep_us(50);
    }

    for (int i = 0; i < 5; i++) {
        uint64_t header = spu_rplu_header(1, 0, (uint16_t)i);
        spu_link_write_rplu_cfg(link, header, PADE_NUM_Q32[i]);
        sleep_us(50);
    }

    for (int i = 0; i < 5; i++) {
        uint64_t header = spu_rplu_header(2, 0, (uint16_t)i);
        spu_link_write_rplu_cfg(link, header, PADE_DEN_Q32[i]);
        sleep_us(50);
    }
}

void spu_boot_hydrate_defaults_cb(spu_link_t *link, void *ctx) {
    (void)ctx;
    spu_boot_hydrate_defaults(link);
}

bool spu_boot_symmetry_breath(spu_link_t *link,
                              const spu_boot_options_t *options) {
    const uint16_t lock_lfi =
        options ? options->lock_lfi : SPU_BOOT_DEFAULT_LOCK_LFI;
    const uint32_t timeout_ms =
        options ? options->timeout_ms : SPU_BOOT_DEFAULT_TIMEOUT_MS;
    const bool verbose = options ? options->verbose : true;
    uint16_t lfi = 0;
    uint8_t flags = 0;
    uint32_t elapsed_ms = 0;

    if (verbose) {
        printf("SPU BOOT: Initiating Symmetry Breath...\n");
    }

    spu_link_read_status(link, &lfi, &flags);

    if (lfi < lock_lfi || (flags & SPU_BOOT_TURBULENCE_FLAG_MASK)) {
        if (verbose) {
            printf("SPU BOOT: Turbulence detected (LFI 0x%04X). "
                   "Injecting Golden Seed...\n", lfi);
        }

        uint8_t seed_chord[SPU_LINK_CHORD_BYTES] = {
            0x40, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01
        };
        spu_link_write_chord(link, seed_chord);

        while (lfi < lock_lfi && elapsed_ms < timeout_ms) {
            sleep_ms(10);
            elapsed_ms += 10;
            spu_link_read_status(link, &lfi, &flags);
            if (verbose && elapsed_ms % 100 == 0) {
                printf("SPU BOOT: Waiting for Janus lock... "
                       "(LFI 0x%04X)\n", lfi);
            }
        }
    }

    if (lfi >= lock_lfi) {
        if (verbose) {
            printf("SPU BOOT: Laminar Harmony reached (LFI 0x%04X). "
                   "Sovereign active.\n", lfi);
        }
        return true;
    }

    if (verbose) {
        printf("SPU BOOT: WARNING - Stability timeout. Proceeding in Turbulent mode.\n");
    }
    return false;
}
