#include "spu_sd.h"

#include "hardware/gpio.h"
#include "hardware/spi.h"
#include "pico/stdlib.h"
#include <string.h>

#ifndef SPU_SD_SPI_PORT
#define SPU_SD_SPI_PORT spi1
#endif
#ifndef SPU_SD_BAUD_HZ
#define SPU_SD_BAUD_HZ 8000000
#endif
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

#define SD_SPI       SPU_SD_SPI_PORT
#define SD_BAUD_HZ   SPU_SD_BAUD_HZ
#define SD_CS_PIN    SPU_SD_CS_PIN
#define SD_SCK_PIN   SPU_SD_SCK_PIN
#define SD_MOSI_PIN  SPU_SD_MOSI_PIN
#define SD_MISO_PIN  SPU_SD_MISO_PIN

#define SD_CMD_TIMEOUT  500
#define SD_INIT_RETRIES 10

#define CMD0   0
#define CMD1   1
#define CMD8   8
#define CMD9   9
#define CMD10  10
#define CMD12  12
#define CMD16  16
#define CMD17  17
#define CMD18  18
#define CMD24  24
#define CMD25  25
#define CMD32  32
#define CMD33  33
#define CMD55  55
#define CMD58  58
#define ACMD41 41

#define SD_R1_IDLE      0x01
#define SD_R1_READY     0x00
#define SD_R1_ILLEGAL   0x04
#define SD_TOKEN_START  0xFE
#define SD_TOKEN_START_MULTI 0xFC
#define SD_TOKEN_STOP   0xFD
#define SD_DATA_RESPONSE_MASK  0x1F
#define SD_DATA_ACCEPTED 0x05

typedef enum {
    SD_TYPE_NONE = 0,
    SD_TYPE_V1,
    SD_TYPE_V2,
    SD_TYPE_V2HC
} sd_type_t;

static sd_type_t sd_type = SD_TYPE_NONE;
static bool sd_mounted = false;

static void sd_cs_low(void)  { gpio_put(SD_CS_PIN, 0); }
static void sd_cs_high(void) { gpio_put(SD_CS_PIN, 1); }

static uint8_t sd_spi_xfer(uint8_t val) {
    uint8_t rx;
    spi_write_read_blocking(SD_SPI, &val, &rx, 1);
    return rx;
}

static void sd_spi_read(uint8_t *buf, size_t len) {
    for (size_t i = 0; i < len; i++) {
        buf[i] = sd_spi_xfer(0xFF);
    }
}

static uint8_t sd_wait_ready(int timeout_ms) {
    absolute_time_t deadline = make_timeout_time_ms(timeout_ms);
    uint8_t r;
    do {
        r = sd_spi_xfer(0xFF);
    } while (r != 0xFF && absolute_time_diff_us(get_absolute_time(), deadline) > 0);
    return r;
}

static void sd_send_cmd(uint8_t cmd, uint32_t arg, uint8_t crc) {
    sd_spi_xfer(0xFF);
    sd_spi_xfer(0x40 | (cmd & 0x3F));
    sd_spi_xfer((uint8_t)(arg >> 24));
    sd_spi_xfer((uint8_t)(arg >> 16));
    sd_spi_xfer((uint8_t)(arg >> 8));
    sd_spi_xfer((uint8_t)arg);
    sd_spi_xfer(crc);
}

static uint8_t sd_read_r1(void) {
    uint8_t r;
    for (int i = 0; i < SD_CMD_TIMEOUT; i++) {
        r = sd_spi_xfer(0xFF);
        if (!(r & 0x80)) return r;
    }
    return 0xFF;
}

static uint8_t sd_cmd(uint8_t cmd, uint32_t arg) {
    sd_cs_low();
    sd_wait_ready(SD_CMD_TIMEOUT);
    sd_send_cmd(cmd, arg, cmd == CMD0 ? 0x95 : (cmd == CMD8 ? 0x87 : 0x01));
    uint8_t r1 = sd_read_r1();
    if (r1 == 0xFF) sd_cs_high();
    return r1;
}

static uint8_t sd_acmd(uint8_t cmd, uint32_t arg) {
    sd_cmd(CMD55, 0);
    return sd_cmd(cmd, arg);
}

static bool sd_read_data_token(uint8_t *buf, size_t len) {
    absolute_time_t deadline = make_timeout_time_ms(200);
    uint8_t token;
    do {
        token = sd_spi_xfer(0xFF);
    } while (token == 0xFF && absolute_time_diff_us(get_absolute_time(), deadline) > 0);

    if (token != SD_TOKEN_START) return false;

    sd_spi_read(buf, len);
    sd_spi_xfer(0xFF); // CRC high
    sd_spi_xfer(0xFF); // CRC low
    return true;
}

bool spu_sd_init(void) {
    if (sd_mounted) return true;

    spi_init(SD_SPI, 400000);
    spi_set_format(SD_SPI, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SD_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SD_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SD_MISO_PIN, GPIO_FUNC_SPI);
    gpio_init(SD_CS_PIN);
    gpio_set_dir(SD_CS_PIN, GPIO_OUT);
    gpio_put(SD_CS_PIN, 1);

    sd_type = SD_TYPE_NONE;
    sd_mounted = false;

    // Power-on: 80 dummy clocks with CS high
    sd_cs_high();
    for (int i = 0; i < 10; i++) sd_spi_xfer(0xFF);

    // CMD0: GO_IDLE
    for (int retry = 0; retry < SD_INIT_RETRIES; retry++) {
        uint8_t r1 = sd_cmd(CMD0, 0);
        if (r1 == SD_R1_IDLE) break;
        if (retry == SD_INIT_RETRIES - 1) return false;
        sleep_ms(10);
    }
    sd_cs_high();
    sd_spi_xfer(0xFF);

    // CMD8: Check v2 card
    uint8_t r1 = sd_cmd(CMD8, 0x1AA);
    bool is_v2 = (r1 == SD_R1_IDLE);
    if (is_v2) {
        uint8_t r7[4];
        sd_spi_read(r7, 4);
        sd_cs_high();
        sd_spi_xfer(0xFF);
        if (r7[2] != 0x01 || r7[3] != 0xAA) {
            is_v2 = false;
        }
    } else {
        sd_cs_high();
        sd_spi_xfer(0xFF);
    }

    // ACMD41: Init
    if (is_v2) {
        absolute_time_t deadline = make_timeout_time_ms(1000);
        do {
            r1 = sd_acmd(ACMD41, 0x40000000);
            if (r1 == 0xFF) { sd_cs_high(); return false; }
        } while (r1 == SD_R1_IDLE && absolute_time_diff_us(get_absolute_time(), deadline) > 0);
        sd_cs_high();
        sd_spi_xfer(0xFF);

        if (r1 != SD_R1_READY) return false;

        // CMD58: check OCR CCS bit
        r1 = sd_cmd(CMD58, 0);
        if (r1 != SD_R1_READY) { sd_cs_high(); return false; }
        uint8_t ocr[4];
        sd_spi_read(ocr, 4);
        sd_cs_high();
        sd_spi_xfer(0xFF);
        sd_type = (ocr[0] & 0x40) ? SD_TYPE_V2HC : SD_TYPE_V2;
    } else {
        absolute_time_t deadline = make_timeout_time_ms(1000);
        do {
            r1 = sd_acmd(ACMD41, 0);
            if (r1 == 0xFF) { sd_cs_high(); return false; }
        } while (r1 == SD_R1_IDLE && absolute_time_diff_us(get_absolute_time(), deadline) > 0);
        sd_cs_high();
        sd_spi_xfer(0xFF);

        if (r1 != SD_R1_READY) return false;
        sd_type = SD_TYPE_V1;
    }

    // Switch to high-speed SPI
    spi_set_baudrate(SD_SPI, SD_BAUD_HZ);

    // CMD16: 512-byte blocks
    r1 = sd_cmd(CMD16, 512);
    sd_cs_high();
    sd_spi_xfer(0xFF);
    if (r1 != SD_R1_READY) return false;

    sd_mounted = true;
    return true;
}

bool spu_sd_mounted(void) {
    return sd_mounted;
}

int spu_sd_read_blocks(uint32_t lba, uint8_t *buf, uint32_t count) {
    if (!sd_mounted || count == 0) return -1;

    uint32_t addr = (sd_type == SD_TYPE_V2HC) ? lba : (lba * 512);

    if (count == 1) {
        uint8_t r1 = sd_cmd(CMD17, addr);
        if (r1 != SD_R1_READY) return -2;
        if (!sd_read_data_token(buf, 512)) return -3;
        sd_cs_high();
        sd_spi_xfer(0xFF);
    } else {
        uint8_t r1 = sd_cmd(CMD18, addr);
        if (r1 != SD_R1_READY) return -2;
        for (uint32_t i = 0; i < count; i++) {
            if (!sd_read_data_token(buf + i * 512, 512)) {
                sd_cmd(CMD12, 0);
                sd_cs_high();
                return -3;
            }
        }
        sd_cmd(CMD12, 0);
        sd_cs_high();
        sd_spi_xfer(0xFF);
    }
    return 0;
}

static bool sd_write_data_token(const uint8_t *buf, uint8_t token) {
    sd_wait_ready(200);
    sd_spi_xfer(token);
    if (token == SD_TOKEN_STOP) return true;

    for (size_t i = 0; i < 512; i++) {
        sd_spi_xfer(buf[i]);
    }
    sd_spi_xfer(0xFF); // CRC
    sd_spi_xfer(0xFF); // CRC

    uint8_t resp = sd_spi_xfer(0xFF);
    if ((resp & SD_DATA_RESPONSE_MASK) != SD_DATA_ACCEPTED) return false;

    return true;
}

int spu_sd_write_blocks(uint32_t lba, const uint8_t *buf, uint32_t count) {
    if (!sd_mounted || count == 0) return -1;

    uint32_t addr = (sd_type == SD_TYPE_V2HC) ? lba : (lba * 512);

    if (count == 1) {
        uint8_t r1 = sd_cmd(CMD24, addr);
        if (r1 != SD_R1_READY) return -2;
        if (!sd_write_data_token(buf, SD_TOKEN_START)) return -3;
        sd_wait_ready(500);
        sd_cs_high();
        sd_spi_xfer(0xFF);
    } else {
        if (sd_acmd(ACMD41, 0) == 0xFF) return -2; // Just a dummy check, some cards need pre-erased
        uint8_t r1 = sd_cmd(CMD25, addr);
        if (r1 != SD_R1_READY) return -2;
        for (uint32_t i = 0; i < count; i++) {
            if (!sd_write_data_token(buf + i * 512, SD_TOKEN_START_MULTI)) {
                sd_write_data_token(NULL, SD_TOKEN_STOP);
                sd_cs_high();
                return -3;
            }
        }
        sd_write_data_token(NULL, SD_TOKEN_STOP);
        sd_wait_ready(500);
        sd_cs_high();
        sd_spi_xfer(0xFF);
    }
    return 0;
}
