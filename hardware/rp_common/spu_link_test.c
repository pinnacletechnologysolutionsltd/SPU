#include "spu_link.h"
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include <stdio.h>
#include <string.h>

// ── Pin assignments (matching rp2350_spu_interface.c) ─────────────────────
#ifndef SPU_SPI_MISO_PIN
#define SPU_SPI_MISO_PIN 16
#endif
#ifndef SPU_SPI_CS_PIN
#define SPU_SPI_CS_PIN   17
#endif
#ifndef SPU_SPI_SCK_PIN
#define SPU_SPI_SCK_PIN  18
#endif
#ifndef SPU_SPI_MOSI_PIN
#define SPU_SPI_MOSI_PIN 19
#endif

#define SPI_PORT        spi0
#define SPI_BAUD_HZ     2000000   // 2 MHz

int main() {
    stdio_init_all();
    sleep_ms(2000);
    printf("\n--- SPU Link Whisper Bridge Test ---\n");
    printf("SPI: MISO=GP%d, CS=GP%d, SCK=GP%d, MOSI=GP%d\n",
           SPU_SPI_MISO_PIN, SPU_SPI_CS_PIN,
           SPU_SPI_SCK_PIN, SPU_SPI_MOSI_PIN);

    // Initialize SPI
    spi_init(SPI_PORT, SPI_BAUD_HZ);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPU_SPI_SCK_PIN,  GPIO_FUNC_SPI);
    gpio_set_function(SPU_SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_SPI_MISO_PIN, GPIO_FUNC_SPI);

    spu_link_t link;
    spu_link_init(&link, SPI_PORT, SPU_SPI_CS_PIN);
    printf("Link ready.\n");

    uint8_t  manifold[SPU_LINK_MANIFOLD_BYTES];
    uint16_t dissonance;
    uint8_t  flags;
    uint8_t  scale[SPU_LINK_SCALE_BYTES];
    uint8_t  qr[SPU_LINK_QR_BYTES];
    uint8_t  hex[SPU_LINK_HEX_BYTES];
    uint8_t  chord[SPU_LINK_CHORD_BYTES] = {0x40,0,0,0,0,0,0,0x01};

    uint64_t rplu_hdr = spu_rplu_header(0, 0, 0);
    uint64_t rplu_dat = 0x0001000000000001ULL;

    uint32_t iter = 0;
    while (true) {
        printf("\n--- Iter %u ---\n", iter++);

        spu_link_read_status(&link, &dissonance, &flags);
        printf("  STATUS  dissonance=0x%04X flags=0x%02X\n", dissonance, flags);

        spu_link_read_manifold(&link, manifold);
        printf("  MANIFOLD (4 axes): ");
        for (int i = 0; i < 32; i++) printf("%02X", manifold[i]);
        printf("\n");

        spu_link_read_scale_table(&link, scale);
        printf("  SCALE: ");
        for (int i = 0; i < 9; i++) printf("%02X ", scale[i]);
        printf("\n");

        spu_link_read_qr(&link, qr);
        printf("  QR commit: ");
        for (int i = 0; i < 34; i++) printf("%02X", qr[i]);

        spu_link_read_hex(&link, hex);
        printf("  HEX: q=0x%04X r=0x%04X\n",
               (uint16_t)hex[0]<<8|hex[1], (uint16_t)hex[2]<<8|hex[3]);

        // Write chord
        spu_link_wait_artery_ready(&link);
        printf("  CHORD → ");
        for (int i = 0; i < 8; i++) printf("%02X", chord[i]);
        printf("\n");
        spu_link_write_chord(&link, chord);

        // Write RPLU config
        spu_link_wait_artery_ready(&link);
        printf("  RPLU  → hdr=0x%016llX dat=0x%016llX\n", rplu_hdr, rplu_dat);
        spu_link_write_rplu_cfg(&link, rplu_hdr, rplu_dat);

        rplu_dat++;
        sleep_ms(500);
    }
    return 0;
}
