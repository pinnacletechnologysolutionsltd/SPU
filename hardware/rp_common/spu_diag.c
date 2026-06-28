#include "spu_diag.h"

#include "hardware/gpio.h"
#include "hardware/spi.h"
#include "ff.h"
#include "pico/stdlib.h"
#include "spu_storage.h"
#include <ctype.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef SPU_SD_CS_PIN
#define SPU_SD_CS_PIN 13
#endif
#ifndef SPU_SD_SCK_PIN
#define SPU_SD_SCK_PIN 10
#endif
#ifndef SPU_SD_MOSI_PIN
#define SPU_SD_MOSI_PIN 11
#endif
#ifndef SPU_SD_MISO_PIN
#define SPU_SD_MISO_PIN 12
#endif
#ifndef SPU_SD_SPI_PORT
#define SPU_SD_SPI_PORT spi1
#endif

#define SPU_STR2(x) #x
#define SPU_STR(x) SPU_STR2(x)

static char *skip_ws(char *s) {
    while (*s != '\0' && isspace((unsigned char)*s)) {
        s++;
    }
    return s;
}

static char *next_token(char **cursor) {
    char *tok = skip_ws(*cursor);

    if (*tok == '\0') {
        *cursor = tok;
        return NULL;
    }

    char *end = tok;
    while (*end != '\0' && !isspace((unsigned char)*end)) {
        end++;
    }
    if (*end != '\0') {
        *end = '\0';
        end++;
    }
    *cursor = end;
    return tok;
}

static bool parse_u32_token(char **cursor, uint32_t *out) {
    char *tok = next_token(cursor);
    char *end = NULL;

    if (tok == NULL) {
        return false;
    }

    unsigned long value = strtoul(tok, &end, 0);
    if (end == tok || *end != '\0') {
        return false;
    }

    *out = (uint32_t)value;
    return true;
}

static bool parse_u64_token(char **cursor, uint64_t *out) {
    char *tok = next_token(cursor);
    char *end = NULL;

    if (tok == NULL) {
        return false;
    }

    unsigned long long value = strtoull(tok, &end, 0);
    if (end == tok || *end != '\0') {
        return false;
    }

    *out = (uint64_t)value;
    return true;
}

static int hex_value(char c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }
    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }
    return -1;
}

static bool parse_hex_bytes(const char *s, uint8_t *out, size_t out_len) {
    size_t count = 0;
    int high = -1;

    while (*s != '\0') {
        int v = hex_value(*s);

        if (v >= 0) {
            if (high < 0) {
                high = v;
            } else {
                if (count >= out_len) {
                    return false;
                }
                out[count++] = (uint8_t)((high << 4) | v);
                high = -1;
            }
        } else if (!isspace((unsigned char)*s) && *s != ':' && *s != '_' && *s != '-') {
            return false;
        }
        s++;
    }

    return high < 0 && count == out_len;
}

static void print_bytes(const uint8_t *bytes, size_t len) {
    for (size_t i = 0; i < len; i++) {
        printf("%02X", bytes[i]);
        if (i + 1 < len) {
            putchar(' ');
        }
    }
    printf("\r\n");
}

static uint64_t read_be64(const uint8_t *bytes) {
    uint64_t value = 0;

    for (size_t i = 0; i < 8; i++) {
        value = (value << 8) | bytes[i];
    }
    return value;
}

static uint32_t read_be32(const uint8_t *bytes) {
    return ((uint32_t)bytes[0] << 24) |
           ((uint32_t)bytes[1] << 16) |
           ((uint32_t)bytes[2] << 8) |
           (uint32_t)bytes[3];
}

static uint16_t read_be16(const uint8_t *bytes) {
    return ((uint16_t)bytes[0] << 8) | (uint16_t)bytes[1];
}

static void cmd_help(void) {
    printf("SPU diag commands:\r\n");
    printf("  help\r\n");
    printf("  ping\r\n");
    printf("  status\r\n");
    printf("  scale\r\n");
    printf("  manifold\r\n");
    printf("  qr\r\n");
    printf("  hex\r\n");
    printf("  cfgtele\r\n");
    printf("  chord <16 hex digits>\r\n");
    printf("  rplu <sel> <material> <addr> <data64>\r\n");
    printf("  hydrate\r\n");
    printf("  sdprobe\r\n");
    printf("  sdcmd\r\n");
    printf("  sddrive <cs> <sck> <mosi>\r\n");
    printf("  sdinit\r\n");
    printf("  sdcat [path]\r\n");
    printf("  sdhydrate [pack]\r\n");
}

static void cmd_status(spu_diag_t *diag) {
    uint8_t raw[4] = {0};
    uint16_t lfi;
    uint8_t flags;
    bool fifo_full;
    bool ratio_valid;
    int8_t ratio_signed;

    spu_link_read_status_raw(diag->link, raw);
    lfi = ((uint16_t)raw[0] << 8) | raw[1];
    flags = raw[2];
    fifo_full = ((flags >> 3) & 0x1) != 0;
    ratio_valid = ((flags >> 4) & 0x1) != 0;
    uint8_t ratio_raw = (flags >> 5) & 0x7;
    ratio_signed = (ratio_raw & 0x4) ? (int8_t)(ratio_raw - 8) : (int8_t)ratio_raw;

    printf("OK status raw=");
    print_bytes(raw, sizeof(raw));
    printf("   lfi=0x%04X flags=0x%02X mode=0x%02X fifo_full=%u ratio_valid=%u ratio=%d\r\n",
           lfi, flags, raw[3], fifo_full ? 1u : 0u,
           ratio_valid ? 1u : 0u, ratio_signed);
}

static void cmd_scale(spu_diag_t *diag) {
    uint8_t scale[SPU_LINK_SCALE_BYTES] = {0};

    spu_link_read_scale_table(diag->link, scale);
    printf("OK scale ");
    print_bytes(scale, sizeof(scale));
}

static void cmd_manifold(spu_diag_t *diag) {
    uint8_t manifold[SPU_LINK_MANIFOLD_BYTES] = {0};

    spu_link_read_manifold(diag->link, manifold);
    printf("OK manifold ");
    print_bytes(manifold, sizeof(manifold));
}

static void cmd_qr(spu_diag_t *diag) {
    uint8_t qr[SPU_LINK_QR_BYTES] = {0};

    spu_link_read_qr(diag->link, qr);
    printf("OK qr valid=%u lane=%u"
           " A=0x%016" PRIX64 " B=0x%016" PRIX64
           " C=0x%016" PRIX64 " D=0x%016" PRIX64 "\r\n",
           qr[0] & 1u, qr[1] & 0xFu,
           read_be64(&qr[2]), read_be64(&qr[10]),
           read_be64(&qr[18]), read_be64(&qr[26]));
}

static void cmd_hex(spu_diag_t *diag) {
    uint8_t hex[SPU_LINK_HEX_BYTES] = {0};
    int16_t q;
    int16_t r;

    spu_link_read_hex(diag->link, hex);
    q = (int16_t)(((uint16_t)hex[1] << 8) | hex[2]);
    r = (int16_t)(((uint16_t)hex[3] << 8) | hex[4]);
    printf("OK hex valid=%u q=%d r=%d raw=%02X %02X %02X %02X %02X\r\n",
           hex[0] & 1u, q, r, hex[0], hex[1], hex[2], hex[3], hex[4]);
}

static void cmd_cfgtele(spu_diag_t *diag) {
    uint8_t tele[SPU_LINK_SENTINEL_BYTES] = {0};

    spu_link_read_sentinel(diag->link, tele);

    uint32_t magic = read_be32(&tele[0]);
    if (magic != 0x53505543u) {
        printf("OK cfgtele raw ");
        print_bytes(tele, sizeof(tele));
        return;
    }

    uint16_t count = read_be16(&tele[4]);
    uint8_t sel = tele[6] & 0x7u;
    uint8_t material = tele[7];
    uint16_t addr = read_be16(&tele[8]) & 0x03FFu;
    uint64_t data = read_be64(&tele[10]);
    uint32_t checksum = read_be32(&tele[18]);

    printf("OK cfgtele magic=SPUC count=%u last_sel=%u last_material=%u"
           " last_addr=%u last_data=0x%016" PRIX64
           " checksum=0x%08" PRIX32 "\r\n",
           count, sel, material, addr, data, checksum);
}

static void cmd_chord(spu_diag_t *diag, char *args) {
    uint8_t chord[SPU_LINK_CHORD_BYTES] = {0};

    if (!parse_hex_bytes(args, chord, sizeof(chord))) {
        printf("ERR usage: chord <16 hex digits>\r\n");
        return;
    }

    spu_link_write_chord(diag->link, chord);
    printf("OK chord ");
    print_bytes(chord, sizeof(chord));
}

static void cmd_rplu(spu_diag_t *diag, char *args) {
    uint32_t sel;
    uint32_t material;
    uint32_t addr;
    uint64_t data;

    if (!parse_u32_token(&args, &sel) ||
        !parse_u32_token(&args, &material) ||
        !parse_u32_token(&args, &addr) ||
        !parse_u64_token(&args, &data)) {
        printf("ERR usage: rplu <sel> <material> <addr> <data64>\r\n");
        return;
    }

    uint64_t header = spu_rplu_header((uint8_t)sel, (uint8_t)material,
                                      (uint16_t)addr);
    spu_link_write_rplu_cfg(diag->link, header, data);
    printf("OK rplu header=0x%016" PRIX64 " data=0x%016" PRIX64 "\r\n",
           header, data);
}

static void cmd_sdprobe(void) {
    gpio_init(SPU_SD_CS_PIN);
    gpio_set_dir(SPU_SD_CS_PIN, GPIO_OUT);
    gpio_put(SPU_SD_CS_PIN, 1);

    gpio_init(SPU_SD_SCK_PIN);
    gpio_set_dir(SPU_SD_SCK_PIN, GPIO_OUT);
    gpio_put(SPU_SD_SCK_PIN, 0);

    gpio_init(SPU_SD_MOSI_PIN);
    gpio_set_dir(SPU_SD_MOSI_PIN, GPIO_OUT);
    gpio_put(SPU_SD_MOSI_PIN, 1);

    gpio_init(SPU_SD_MISO_PIN);
    gpio_set_dir(SPU_SD_MISO_PIN, GPIO_IN);

    gpio_disable_pulls(SPU_SD_MISO_PIN);
    sleep_us(100);
    uint32_t miso_float = gpio_get(SPU_SD_MISO_PIN);

    gpio_pull_up(SPU_SD_MISO_PIN);
    sleep_us(100);
    uint32_t miso_pullup = gpio_get(SPU_SD_MISO_PIN);

    gpio_pull_down(SPU_SD_MISO_PIN);
    sleep_us(100);
    uint32_t miso_pulldown = gpio_get(SPU_SD_MISO_PIN);

    gpio_disable_pulls(SPU_SD_MISO_PIN);

    printf("OK sdprobe spi=%s cs=GP%d sck=GP%d mosi=GP%d miso=GP%d"
           " miso_float=%u miso_pullup=%u miso_pulldown=%u\r\n",
           SPU_STR(SPU_SD_SPI_PORT), SPU_SD_CS_PIN, SPU_SD_SCK_PIN,
           SPU_SD_MOSI_PIN, SPU_SD_MISO_PIN, miso_float, miso_pullup,
           miso_pulldown);
}

static uint8_t sd_diag_xfer(uint8_t v) {
    uint8_t rx = 0;

    spi_write_read_blocking(SPU_SD_SPI_PORT, &v, &rx, 1);
    return rx;
}

static uint8_t sd_diag_r1(void) {
    uint8_t r = 0xFF;

    for (int i = 0; i < 16; i++) {
        r = sd_diag_xfer(0xFF);
        if ((r & 0x80) == 0) {
            break;
        }
    }
    return r;
}

static void sd_diag_send_cmd(uint8_t cmd, uint32_t arg, uint8_t crc) {
    sd_diag_xfer(0xFF);
    sd_diag_xfer(0x40 | (cmd & 0x3F));
    sd_diag_xfer((uint8_t)(arg >> 24));
    sd_diag_xfer((uint8_t)(arg >> 16));
    sd_diag_xfer((uint8_t)(arg >> 8));
    sd_diag_xfer((uint8_t)arg);
    sd_diag_xfer(crc);
}

static void cmd_sdcmd(void) {
    uint8_t r1_cmd0;
    uint8_t r1_cmd8;
    uint8_t r7[4];

    spi_init(SPU_SD_SPI_PORT, 400000);
    spi_set_format(SPU_SD_SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPU_SD_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SD_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SD_MISO_PIN, GPIO_FUNC_SPI);
    gpio_init(SPU_SD_CS_PIN);
    gpio_set_dir(SPU_SD_CS_PIN, GPIO_OUT);
    gpio_put(SPU_SD_CS_PIN, 1);

    for (int i = 0; i < 10; i++) {
        sd_diag_xfer(0xFF);
    }

    gpio_put(SPU_SD_CS_PIN, 0);
    sd_diag_send_cmd(0, 0, 0x95);
    r1_cmd0 = sd_diag_r1();
    gpio_put(SPU_SD_CS_PIN, 1);
    sd_diag_xfer(0xFF);

    gpio_put(SPU_SD_CS_PIN, 0);
    sd_diag_send_cmd(8, 0x1AA, 0x87);
    r1_cmd8 = sd_diag_r1();
    for (int i = 0; i < 4; i++) {
        r7[i] = sd_diag_xfer(0xFF);
    }
    gpio_put(SPU_SD_CS_PIN, 1);
    sd_diag_xfer(0xFF);

    printf("OK sdcmd cmd0_r1=0x%02X cmd8_r1=0x%02X r7=%02X %02X %02X %02X\r\n",
           r1_cmd0, r1_cmd8, r7[0], r7[1], r7[2], r7[3]);
}

static void cmd_sddrive(char *args) {
    uint32_t cs;
    uint32_t sck;
    uint32_t mosi;

    if (!parse_u32_token(&args, &cs) ||
        !parse_u32_token(&args, &sck) ||
        !parse_u32_token(&args, &mosi) ||
        cs > 1 || sck > 1 || mosi > 1) {
        printf("ERR usage: sddrive <cs> <sck> <mosi>\r\n");
        return;
    }

    gpio_init(SPU_SD_CS_PIN);
    gpio_set_dir(SPU_SD_CS_PIN, GPIO_OUT);
    gpio_put(SPU_SD_CS_PIN, cs);

    gpio_init(SPU_SD_SCK_PIN);
    gpio_set_dir(SPU_SD_SCK_PIN, GPIO_OUT);
    gpio_put(SPU_SD_SCK_PIN, sck);

    gpio_init(SPU_SD_MOSI_PIN);
    gpio_set_dir(SPU_SD_MOSI_PIN, GPIO_OUT);
    gpio_put(SPU_SD_MOSI_PIN, mosi);

    gpio_init(SPU_SD_MISO_PIN);
    gpio_set_dir(SPU_SD_MISO_PIN, GPIO_IN);
    gpio_disable_pulls(SPU_SD_MISO_PIN);
    sleep_us(100);

    printf("OK sddrive cs=GP%d:%u sck=GP%d:%u mosi=GP%d:%u miso=GP%d:%u\r\n",
           SPU_SD_CS_PIN, cs, SPU_SD_SCK_PIN, sck, SPU_SD_MOSI_PIN, mosi,
           SPU_SD_MISO_PIN, gpio_get(SPU_SD_MISO_PIN));
}

static void cmd_sdinit(void) {
    if (!spu_storage_init()) {
        printf("ERR no SD card\r\n");
    } else {
        printf("OK sdinit\r\n");
    }
}

static void cmd_sdcat(char *args) {
    char *path = next_token(&args);
    char name[64];
    FIL file;

    if (path == NULL || *path == '\0') {
        path = "/manifest.txt";
    }

    if (path[0] == '/') {
        snprintf(name, sizeof(name), "%s", path);
    } else {
        snprintf(name, sizeof(name), "/%s", path);
    }

    if (!spu_storage_init()) {
        printf("ERR no SD card\r\n");
        return;
    }

    FRESULT res = f_open(&file, name, FA_READ);
    if (res != FR_OK) {
        printf("ERR sdcat open %s res=%d\r\n", name, res);
        return;
    }

    FSIZE_t size = f_size(&file);
    printf("OK sdcat %s size=%lu\r\n", name, (unsigned long)size);

    size_t total = 0;
    while (total < 2048) {
        char buf[64];
        UINT br = 0;
        size_t want = sizeof(buf);
        if (want > 2048 - total) {
            want = 2048 - total;
        }

        res = f_read(&file, buf, (UINT)want, &br);
        if (res != FR_OK || br == 0) {
            break;
        }

        for (UINT i = 0; i < br; i++) {
            unsigned char c = (unsigned char)buf[i];
            if (c == '\n') {
                printf("\r\n");
            } else if (c == '\r') {
                continue;
            } else if (c == '\t' || (c >= 0x20 && c <= 0x7E)) {
                putchar((int)c);
            } else {
                printf("\\x%02X", c);
            }
        }
        total += br;
    }

    if ((FSIZE_t)total < size) {
        printf("\r\n... truncated ...\r\n");
    } else {
        printf("\r\n");
    }
    f_close(&file);
}

static void execute_line(spu_diag_t *diag) {
    char *cursor = diag->line;
    char *cmd = next_token(&cursor);

    if (cmd == NULL) {
        return;
    }

    if (strcmp(cmd, "help") == 0 || strcmp(cmd, "?") == 0) {
        cmd_help();
    } else if (strcmp(cmd, "ping") == 0) {
        printf("OK pong\r\n");
    } else if (strcmp(cmd, "status") == 0 || strcmp(cmd, "st") == 0) {
        cmd_status(diag);
    } else if (strcmp(cmd, "scale") == 0) {
        cmd_scale(diag);
    } else if (strcmp(cmd, "manifold") == 0 || strcmp(cmd, "mf") == 0) {
        cmd_manifold(diag);
    } else if (strcmp(cmd, "qr") == 0) {
        cmd_qr(diag);
    } else if (strcmp(cmd, "hex") == 0) {
        cmd_hex(diag);
    } else if (strcmp(cmd, "cfgtele") == 0) {
        cmd_cfgtele(diag);
    } else if (strcmp(cmd, "chord") == 0) {
        cmd_chord(diag, cursor);
    } else if (strcmp(cmd, "rplu") == 0) {
        cmd_rplu(diag, cursor);
    } else if (strcmp(cmd, "hydrate") == 0) {
        if (diag->hydrate == NULL) {
            printf("ERR hydrate unavailable\r\n");
        } else {
            diag->hydrate(diag->link, diag->hydrate_ctx);
            printf("OK hydrate\r\n");
        }
    } else if (strcmp(cmd, "sdprobe") == 0) {
        cmd_sdprobe();
    } else if (strcmp(cmd, "sdcmd") == 0) {
        cmd_sdcmd();
    } else if (strcmp(cmd, "sddrive") == 0) {
        cmd_sddrive(cursor);
    } else if (strcmp(cmd, "sdinit") == 0) {
        cmd_sdinit();
    } else if (strcmp(cmd, "sdcat") == 0) {
        cmd_sdcat(cursor);
    } else if (strcmp(cmd, "sdhydrate") == 0) {
        char *pack = next_token(&cursor);
        if (!spu_storage_init()) {
            printf("ERR no SD card\r\n");
        } else {
            int n = spu_storage_hydrate_from_sd(diag->link, pack);
            if (n < 0) {
                printf("ERR pack not found\r\n");
            } else {
                printf("OK sdhydrate %d records\r\n", n);
            }
        }
    } else {
        printf("ERR unknown command: %s\r\n", cmd);
    }
}

void spu_diag_init(spu_diag_t *diag, spu_link_t *link,
                   spu_diag_hydrate_fn hydrate, void *hydrate_ctx) {
    memset(diag, 0, sizeof(*diag));
    diag->link = link;
    diag->hydrate = hydrate;
    diag->hydrate_ctx = hydrate_ctx;
}

void spu_diag_print_banner(void) {
    printf("\r\nSPU RP diagnostic console ready\r\n");
    printf("Type 'help' for commands.\r\n> ");
}

void spu_diag_poll(spu_diag_t *diag) {
    int ch;

    while ((ch = getchar_timeout_us(0)) != PICO_ERROR_TIMEOUT) {
        if (ch == '\r' || ch == '\n') {
            putchar('\r');
            putchar('\n');
            diag->line[diag->len] = '\0';
            execute_line(diag);
            diag->len = 0;
            printf("> ");
        } else if (ch == '\b' || ch == 0x7F) {
            if (diag->len > 0) {
                diag->len--;
                printf("\b \b");
            }
        } else if (isprint((unsigned char)ch)) {
            if (diag->len + 1 < sizeof(diag->line)) {
                diag->line[diag->len++] = (char)ch;
                putchar(ch);
            } else {
                printf("\r\nERR line too long\r\n> ");
                diag->len = 0;
            }
        }
    }
}
