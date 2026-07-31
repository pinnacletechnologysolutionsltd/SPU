// rp2350_spu_diag.c
// Target: Raspberry Pi Pico 2 (RP2350)
// Role: USB CDC diagnostic console for FPGA SPI bring-up.
//
// Wiring defaults:
//   SPI0 MISO GP16, CS GP17, SCK GP18, MOSI GP19 -> FPGA SPI slave
//   GND shared with FPGA board
//
// For Waveshare RP2350-Zero header-friendly wiring, build with:
//   -DSPU_RP2350_ZERO_HEADER_SPI=ON
// This remaps SPI0 to MISO GP0, CS GP1, SCK GP2, MOSI GP3.
//
// For the RP2350-Zero edge labeled G..25, build with:
//   -DSPU_RP2350_ZERO_G25_SPI=ON
// This remaps SPI0 to MISO GP20, CS GP21, SCK GP22, MOSI GP23.

#include "hardware/spi.h"
#include "pico/stdio_usb.h"
#include "pico/stdlib.h"
#include "spu_boot.h"
#include "spu_diag.h"
#include "spu_link.h"

#define SPI_PORT     spi0
#ifndef SPI_BAUD_HZ
// Safe against the slowest clk_fast on divided A7 core spins -- see AGENTS.md
// boot_ready notes for the Nyquist-violation bug this default exists to
// prevent. CMakeLists.txt's SPU_DIAG_SPI_BAUD_HZ cache var also defaults to
// this; override explicitly when a faster clk_fast is known.
//
// CAUTION (2026-07-31): spu_spi_slave_ratio_tb.v measures the safe bound as
// SCK <= clk_fast / 6. This 250 kHz default was chosen against an assumed
// 1.5625 MHz divided clk_fast (ratio 6.25, just inside). But that figure
// implies a 100 MHz oscillator, while the XDC period, surd_uart_tx's
// CLK_HZ(50_000_000), BAUD_DIV=434 and the 115200 host tools all say 50 MHz
// -- which puts the divided clock at 781.25 kHz and this default at ratio
// 3.1, OUTSIDE the measured bound. The two readings differ by exactly 2x and
// have not been reconciled on hardware. Value left unchanged because it is
// reported working; confirm the real clk_fast with a scope or counter before
// trusting it. See docs/SOUTHBRIDGE_SPI_PROTOCOL.md, "Per-spin ceiling".
#define SPI_BAUD_HZ  250000
#endif

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

#define SPI_MISO_PIN SPU_SPI_MISO_PIN
#define SPI_CS_PIN   SPU_SPI_CS_PIN
#define SPI_SCK_PIN  SPU_SPI_SCK_PIN
#define SPI_MOSI_PIN SPU_SPI_MOSI_PIN

int main(void) {
    spu_link_t link;
    spu_diag_t diag;

    stdio_init_all();

    spi_init(SPI_PORT, SPI_BAUD_HZ);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(SPI_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPI_MISO_PIN, GPIO_FUNC_SPI);
    spu_link_init(&link, SPI_PORT, SPI_CS_PIN);

    while (!stdio_usb_connected()) {
        sleep_ms(100);
    }

    spu_diag_init(&diag, &link, spu_boot_hydrate_defaults_cb, NULL);
    spu_diag_print_banner();

    while (true) {
        spu_diag_poll(&diag);
        tight_loop_contents();
    }
}
