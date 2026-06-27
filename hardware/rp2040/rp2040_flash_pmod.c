// rp2040_flash_pmod.c -- USB CDC SPI flash programmer for W25Q PMODs.
//
// Default bench wiring uses the easy front-edge Pico pins:
//   RP2040 GP4 -> PMOD DO / MISO
//   RP2040 GP5 -> PMOD CS
//   RP2040 GP2 -> PMOD SLK / SCK
//   RP2040 GP3 -> PMOD D1 / MOSI
//   RP2040 3V3  -> PMOD VCC
//   RP2040 GND  -> PMOD GND
//
// The flash breakout must pull /WP and /HOLD high. Most 6-pin W25Q PMODs do.

#include "pico/stdlib.h"
#include "hardware/spi.h"
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef FLASH_SPI_MISO_PIN
#define FLASH_SPI_MISO_PIN 4
#endif
#ifndef FLASH_SPI_CS_PIN
#define FLASH_SPI_CS_PIN   5
#endif
#ifndef FLASH_SPI_SCK_PIN
#define FLASH_SPI_SCK_PIN  2
#endif
#ifndef FLASH_SPI_MOSI_PIN
#define FLASH_SPI_MOSI_PIN 3
#endif

#define FLASH_SPI       spi0
#define FLASH_BAUD_HZ   100000u
#define MAX_IO_BYTES    4096u

#define CMD_WREN        0x06u
#define CMD_RDSR        0x05u
#define CMD_READ        0x03u
#define CMD_PP          0x02u
#define CMD_SE          0x20u
#define CMD_BE64        0xD8u
#define CMD_CE          0xC7u
#define CMD_JEDEC       0x9Fu
#define CMD_RDPD        0xABu
#define CMD_RSTEN       0x66u
#define CMD_RST         0x99u

static uint8_t io_buf[MAX_IO_BYTES];

static void cs_low(void) {
    gpio_put(FLASH_SPI_CS_PIN, 0);
}

static void cs_high(void) {
    gpio_put(FLASH_SPI_CS_PIN, 1);
}

static uint8_t spi_xfer(uint8_t tx) {
    uint8_t rx = 0;
    spi_write_read_blocking(FLASH_SPI, &tx, &rx, 1);
    return rx;
}

static void spi_addr24(uint32_t addr) {
    spi_xfer((uint8_t)(addr >> 16));
    spi_xfer((uint8_t)(addr >> 8));
    spi_xfer((uint8_t)addr);
}

static uint8_t flash_rdsr(void) {
    uint8_t status;
    cs_low();
    spi_xfer(CMD_RDSR);
    status = spi_xfer(0xFF);
    cs_high();
    return status;
}

static void flash_wren(void) {
    cs_low();
    spi_xfer(CMD_WREN);
    cs_high();
}

static bool flash_wren_checked(void) {
    flash_wren();
    sleep_us(10);
    return (flash_rdsr() & 0x02u) != 0;
}

static bool flash_wait_ready(uint32_t timeout_ms) {
    absolute_time_t deadline = make_timeout_time_ms(timeout_ms);
    while (!time_reached(deadline)) {
        if ((flash_rdsr() & 0x01u) == 0)
            return true;
        sleep_ms(1);
    }
    return false;
}

static void flash_jedec(uint8_t id[3]) {
    cs_high();
    sleep_us(50);
    cs_low();
    spi_xfer(CMD_RDPD);
    cs_high();
    sleep_us(50);

    cs_low();
    spi_xfer(CMD_JEDEC);
    id[0] = spi_xfer(0xFF);
    id[1] = spi_xfer(0xFF);
    id[2] = spi_xfer(0xFF);
    cs_high();
}

static void flash_soft_reset(void) {
    cs_high();
    sleep_us(50);
    cs_low();
    spi_xfer(CMD_RSTEN);
    cs_high();
    sleep_us(50);
    cs_low();
    spi_xfer(CMD_RST);
    cs_high();
    sleep_ms(1);
}

static void flash_read(uint32_t addr, uint8_t *buf, uint32_t len) {
    cs_low();
    spi_xfer(CMD_READ);
    spi_addr24(addr);
    for (uint32_t i = 0; i < len; i++)
        buf[i] = spi_xfer(0xFF);
    cs_high();
}

static bool flash_erase4k(uint32_t addr) {
    if (!flash_wren_checked())
        return false;
    cs_low();
    spi_xfer(CMD_SE);
    spi_addr24(addr);
    cs_high();
    return flash_wait_ready(5000);
}

static bool flash_erase64k(uint32_t addr) {
    if (!flash_wren_checked())
        return false;
    cs_low();
    spi_xfer(CMD_BE64);
    spi_addr24(addr);
    cs_high();
    return flash_wait_ready(15000);
}

static bool flash_chip_erase(void) {
    if (!flash_wren_checked())
        return false;
    cs_low();
    spi_xfer(CMD_CE);
    cs_high();
    return flash_wait_ready(120000);
}

static bool flash_page_program(uint32_t addr, const uint8_t *buf, uint32_t len) {
    if (len == 0 || len > 256 || ((addr & 0xFFu) + len) > 256)
        return false;

    if (!flash_wren_checked())
        return false;
    cs_low();
    spi_xfer(CMD_PP);
    spi_addr24(addr);
    spi_write_blocking(FLASH_SPI, buf, len);
    cs_high();
    return flash_wait_ready(1000);
}

static bool flash_write(uint32_t addr, const uint8_t *buf, uint32_t len) {
    uint32_t off = 0;
    while (off < len) {
        uint32_t page_room = 256u - ((addr + off) & 0xFFu);
        uint32_t chunk = len - off;
        if (chunk > page_room)
            chunk = page_room;
        if (!flash_page_program(addr + off, buf + off, chunk))
            return false;
        off += chunk;
    }
    return true;
}

static uint32_t crc32_update(uint32_t crc, const uint8_t *buf, uint32_t len) {
    crc = ~crc;
    for (uint32_t i = 0; i < len; i++) {
        crc ^= buf[i];
        for (int bit = 0; bit < 8; bit++)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

static bool parse_u32(char **cursor, uint32_t *out) {
    char *p = *cursor;
    while (*p && isspace((unsigned char)*p))
        p++;
    if (*p == '\0')
        return false;

    char *end = p;
    unsigned long v = strtoul(p, &end, 0);
    if (end == p)
        return false;
    *cursor = end;
    *out = (uint32_t)v;
    return true;
}

static bool read_line(char *buf, size_t cap) {
    size_t n = 0;
    while (n + 1 < cap) {
        int c = getchar_timeout_us(100000);
        if (c == PICO_ERROR_TIMEOUT)
            continue;
        if (c == '\r')
            continue;
        if (c == '\n') {
            buf[n] = '\0';
            return true;
        }
        buf[n++] = (char)c;
    }
    buf[cap - 1] = '\0';
    return true;
}

static bool read_exact(uint8_t *buf, uint32_t len, uint32_t timeout_ms) {
    absolute_time_t deadline = make_timeout_time_ms(timeout_ms);
    uint32_t n = 0;
    while (n < len && !time_reached(deadline)) {
        int c = getchar_timeout_us(1000);
        if (c == PICO_ERROR_TIMEOUT)
            continue;
        buf[n++] = (uint8_t)c;
    }
    return n == len;
}

static void print_help(void) {
    printf("OK HELP commands: PING PINS DIAG DRIVE cs sck mosi WAKE RESET JEDEC RDSR READ addr len ERASE4K addr ERASE64K addr CHIPERASE WRITE addr len crc32\n");
}

static void restore_spi_pins(void) {
    gpio_set_function(FLASH_SPI_MISO_PIN, GPIO_FUNC_SPI);
    gpio_set_function(FLASH_SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(FLASH_SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_init(FLASH_SPI_CS_PIN);
    gpio_set_dir(FLASH_SPI_CS_PIN, GPIO_OUT);
    cs_high();
}

static void print_pin_diag(void) {
    gpio_set_function(FLASH_SPI_MISO_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(FLASH_SPI_MISO_PIN, GPIO_IN);
    gpio_set_function(FLASH_SPI_SCK_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(FLASH_SPI_SCK_PIN, GPIO_OUT);
    gpio_put(FLASH_SPI_SCK_PIN, 0);
    gpio_set_function(FLASH_SPI_MOSI_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(FLASH_SPI_MOSI_PIN, GPIO_OUT);
    gpio_put(FLASH_SPI_MOSI_PIN, 0);
    gpio_set_function(FLASH_SPI_CS_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(FLASH_SPI_CS_PIN, GPIO_OUT);
    gpio_put(FLASH_SPI_CS_PIN, 1);

    gpio_disable_pulls(FLASH_SPI_MISO_PIN);
    sleep_ms(2);
    int miso_float = gpio_get(FLASH_SPI_MISO_PIN);
    gpio_pull_up(FLASH_SPI_MISO_PIN);
    sleep_ms(2);
    int miso_pullup = gpio_get(FLASH_SPI_MISO_PIN);
    gpio_pull_down(FLASH_SPI_MISO_PIN);
    sleep_ms(2);
    int miso_pulldown = gpio_get(FLASH_SPI_MISO_PIN);
    gpio_disable_pulls(FLASH_SPI_MISO_PIN);

    printf("OK DIAG pins MISO=GP%d CS=GP%d SCK=GP%d MOSI=GP%d miso_float=%d miso_pullup=%d miso_pulldown=%d\n",
           FLASH_SPI_MISO_PIN, FLASH_SPI_CS_PIN, FLASH_SPI_SCK_PIN,
           FLASH_SPI_MOSI_PIN, miso_float, miso_pullup, miso_pulldown);

    restore_spi_pins();
}

static void drive_pins(uint32_t cs, uint32_t sck, uint32_t mosi) {
    gpio_set_function(FLASH_SPI_MISO_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(FLASH_SPI_MISO_PIN, GPIO_IN);
    gpio_set_function(FLASH_SPI_CS_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(FLASH_SPI_CS_PIN, GPIO_OUT);
    gpio_set_function(FLASH_SPI_SCK_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(FLASH_SPI_SCK_PIN, GPIO_OUT);
    gpio_set_function(FLASH_SPI_MOSI_PIN, GPIO_FUNC_SIO);
    gpio_set_dir(FLASH_SPI_MOSI_PIN, GPIO_OUT);

    gpio_put(FLASH_SPI_CS_PIN, cs ? 1 : 0);
    gpio_put(FLASH_SPI_SCK_PIN, sck ? 1 : 0);
    gpio_put(FLASH_SPI_MOSI_PIN, mosi ? 1 : 0);

    printf("OK DRIVE CS=%lu SCK=%lu MOSI=%lu MISO=%d\n",
           (unsigned long)(cs ? 1 : 0), (unsigned long)(sck ? 1 : 0),
           (unsigned long)(mosi ? 1 : 0), gpio_get(FLASH_SPI_MISO_PIN));
}

static void handle_command(char *line) {
    char *cmd = line;
    while (*cmd && isspace((unsigned char)*cmd))
        cmd++;
    for (char *p = cmd; *p && !isspace((unsigned char)*p); p++)
        *p = (char)toupper((unsigned char)*p);

    if (strncmp(cmd, "PING", 4) == 0) {
        printf("OK PONG\n");
    } else if (strncmp(cmd, "PINS", 4) == 0) {
        printf("OK PINS MISO=GP%d CS=GP%d SCK=GP%d MOSI=GP%d baud=%lu\n",
               FLASH_SPI_MISO_PIN, FLASH_SPI_CS_PIN, FLASH_SPI_SCK_PIN,
               FLASH_SPI_MOSI_PIN, (unsigned long)FLASH_BAUD_HZ);
    } else if (strncmp(cmd, "DIAG", 4) == 0) {
        print_pin_diag();
    } else if (strncmp(cmd, "DRIVE", 5) == 0) {
        char *p = cmd + 5;
        uint32_t cs, sck, mosi;
        if (!parse_u32(&p, &cs) || !parse_u32(&p, &sck) || !parse_u32(&p, &mosi)) {
            printf("ERR BAD_DRIVE_ARGS\n");
            return;
        }
        drive_pins(cs, sck, mosi);
    } else if (strncmp(cmd, "WAKE", 4) == 0) {
        cs_low();
        spi_xfer(CMD_RDPD);
        cs_high();
        sleep_ms(1);
        printf("OK WAKE\n");
    } else if (strncmp(cmd, "RESET", 5) == 0) {
        flash_soft_reset();
        printf("OK RESET\n");
    } else if (strncmp(cmd, "HELP", 4) == 0) {
        print_help();
    } else if (strncmp(cmd, "JEDEC", 5) == 0 || strncmp(cmd, "ID", 2) == 0) {
        uint8_t id[3];
        flash_jedec(id);
        printf("OK JEDEC %02X%02X%02X\n", id[0], id[1], id[2]);
    } else if (strncmp(cmd, "RDSR", 4) == 0) {
        printf("OK RDSR %02X\n", flash_rdsr());
    } else if (strncmp(cmd, "WREN", 4) == 0) {
        bool ok = flash_wren_checked();
        printf("%s WREN RDSR=%02X\n", ok ? "OK" : "ERR", flash_rdsr());
    } else if (strncmp(cmd, "READ", 4) == 0) {
        char *p = cmd + 4;
        uint32_t addr, len;
        if (!parse_u32(&p, &addr) || !parse_u32(&p, &len) || len > MAX_IO_BYTES) {
            printf("ERR BAD_READ_ARGS\n");
            return;
        }
        flash_read(addr, io_buf, len);
        printf("DATA %lu\n", (unsigned long)len);
        stdio_flush();
        for (uint32_t i = 0; i < len; i++)
            putchar_raw(io_buf[i]);
        stdio_flush();
        printf("OK READ\n");
    } else if (strncmp(cmd, "ERASE4K", 7) == 0) {
        char *p = cmd + 7;
        uint32_t addr;
        if (!parse_u32(&p, &addr) || (addr & 0xFFFu) != 0) {
            printf("ERR BAD_ERASE4K_ARGS\n");
            return;
        }
        printf("%s ERASE4K\n", flash_erase4k(addr) ? "OK" : "ERR");
    } else if (strncmp(cmd, "ERASE64K", 8) == 0) {
        char *p = cmd + 8;
        uint32_t addr;
        if (!parse_u32(&p, &addr) || (addr & 0xFFFFu) != 0) {
            printf("ERR BAD_ERASE64K_ARGS\n");
            return;
        }
        printf("%s ERASE64K\n", flash_erase64k(addr) ? "OK" : "ERR");
    } else if (strncmp(cmd, "CHIPERASE", 9) == 0) {
        printf("%s CHIPERASE\n", flash_chip_erase() ? "OK" : "ERR");
    } else if (strncmp(cmd, "WRITE", 5) == 0) {
        char *p = cmd + 5;
        uint32_t addr, len, expected_crc;
        if (!parse_u32(&p, &addr) || !parse_u32(&p, &len) ||
            !parse_u32(&p, &expected_crc) || len > MAX_IO_BYTES) {
            printf("ERR BAD_WRITE_ARGS\n");
            return;
        }

        printf("READY\n");
        stdio_flush();
        if (!read_exact(io_buf, len, 10000)) {
            printf("ERR WRITE_TIMEOUT\n");
            return;
        }
        uint32_t actual_crc = crc32_update(0, io_buf, len);
        if (actual_crc != expected_crc) {
            printf("ERR CRC expected=%08lX actual=%08lX\n",
                   (unsigned long)expected_crc, (unsigned long)actual_crc);
            return;
        }
        printf("%s WRITE\n", flash_write(addr, io_buf, len) ? "OK" : "ERR");
    } else if (*cmd != '\0') {
        printf("ERR UNKNOWN_CMD\n");
    }
}

int main(void) {
    stdio_init_all();
    sleep_ms(2000);

    spi_init(FLASH_SPI, FLASH_BAUD_HZ);
    spi_set_format(FLASH_SPI, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    restore_spi_pins();

    printf("\nRP2040_FLASH_PMOD ready\n");
    printf("SPI pins: MISO=GP%d CS=GP%d SCK=GP%d MOSI=GP%d baud=%lu\n",
           FLASH_SPI_MISO_PIN, FLASH_SPI_CS_PIN, FLASH_SPI_SCK_PIN,
           FLASH_SPI_MOSI_PIN, (unsigned long)FLASH_BAUD_HZ);
    print_help();

    char line[128];
    while (true) {
        if (read_line(line, sizeof(line)))
            handle_command(line);
    }
}
