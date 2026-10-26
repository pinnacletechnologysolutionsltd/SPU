#include "spu_storage.h"

#include "ff.h"
#include "spu_link.h"
#include "spu_sd.h"
#include <stdio.h>
#include <string.h>

#define MANIFEST_NAME  "manifest.txt"
#define PACK_EXT       ".tbl"
#define LINE_MAX       128
#define PACK_DIR       "/"

static FATFS fs;
static bool fs_mounted = false;

static int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static const char *skip_spaces(const char *p) {
    while (*p == ' ' || *p == '\t') {
        p++;
    }
    return p;
}

static bool parse_dec_token(const char **cursor, unsigned *out) {
    const char *p = skip_spaces(*cursor);
    unsigned value = 0;

    if (*p < '0' || *p > '9') {
        return false;
    }

    while (*p >= '0' && *p <= '9') {
        value = (value * 10u) + (unsigned)(*p - '0');
        p++;
    }

    *cursor = p;
    *out = value;
    return true;
}

static bool parse_hex64_token(const char **cursor, uint64_t *out) {
    const char *p = skip_spaces(*cursor);
    uint64_t value = 0;

    if (p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) {
        p += 2;
    }

    for (int i = 0; i < 16; i++) {
        int d = hex_digit(*p);
        if (d < 0) {
            return false;
        }
        value = (value << 4) | (uint64_t)d;
        p++;
    }

    p = skip_spaces(p);
    if (*p != '\0' && *p != '#') {
        return false;
    }

    *cursor = p;
    *out = value;
    return true;
}

static bool parse_rplu_line(const char *line, uint64_t *header, uint64_t *data) {
    // Format: <sel> <material> <addr> <data64_hex>
    unsigned sel, material, addr;
    uint64_t val = 0;
    const char *p = skip_spaces(line);

    if (*p == '\0' || *p == '#') {
        return false;
    }

    if (!parse_dec_token(&p, &sel) ||
        !parse_dec_token(&p, &material) ||
        !parse_dec_token(&p, &addr) ||
        !parse_hex64_token(&p, &val)) {
        return false;
    }

    if (sel > 7 || material > 15 || addr > 1023) {
        return false;
    }

    *header = spu_rplu_header((uint8_t)sel, (uint8_t)material, (uint16_t)addr);
    *data = val;
    return true;
}

bool spu_storage_init(void) {
    if (fs_mounted) return true;

    if (!spu_sd_init()) {
        return false;
    }

    FRESULT res = f_mount(&fs, "", 1);
    if (res != FR_OK) {
        return false;
    }

    fs_mounted = true;
    return true;
}

bool spu_storage_mounted(void) {
    return fs_mounted;
}

static bool read_line(FIL *file, char *line, size_t max) {
    if (max < 2) return false;
    size_t pos = 0;
    bool read_any = false;

    while (pos < max - 1) {
        UINT br;
        char c;
        FRESULT res = f_read(file, &c, 1, &br);
        if (res != FR_OK || br == 0) break;
        read_any = true;
        if (c == '\n') {
            if (pos > 0 && line[pos - 1] == '\r') pos--;
            break;
        }
        line[pos++] = c;
    }
    line[pos] = '\0';
    return read_any;
}

int spu_storage_hydrate_from_sd(spu_link_t *link, const char *pack_name) {
    if (!fs_mounted) return -1;

    FIL file;
    char name[64];
    char line[LINE_MAX];

    if (pack_name) {
        snprintf(name, sizeof(name), "%s%s", PACK_DIR, pack_name);
    } else {
        FRESULT res = f_open(&file, PACK_DIR MANIFEST_NAME, FA_READ);
        if (res != FR_OK) return -2;

        bool found = false;
        while (read_line(&file, line, sizeof(line))) {
            const char *trimmed = skip_spaces(line);
            if (trimmed[0] != '#' && trimmed[0] != '\0') {
                snprintf(name, sizeof(name), "%s%s", PACK_DIR, trimmed);
                found = true;
                break;
            }
        }
        f_close(&file);
        if (!found) return -2;
    }

    FRESULT res = f_open(&file, name, FA_READ);
    if (res != FR_OK) return -3;

    printf("SPU STORAGE: loading %s\r\n", name);

    int count = 0;
    int skipped = 0;
    while (read_line(&file, line, sizeof(line))) {
        const char *trimmed = skip_spaces(line);
        if (trimmed[0] == '#' || trimmed[0] == '\0') continue;

        uint64_t header, data;
        if (parse_rplu_line(trimmed, &header, &data)) {
            spu_link_write_rplu_cfg(link, header, data);
            count++;
        } else {
            skipped++;
        }
    }
    f_close(&file);
    printf("SPU STORAGE: %d records loaded, %d skipped\r\n", count, skipped);
    return count;
}
