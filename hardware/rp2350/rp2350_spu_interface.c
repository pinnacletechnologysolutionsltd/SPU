// rp2350_spu_interface.c
// The RP2350 "Laminar Controller" firmware
// Responsible for power sequencing, Multicore Sync, and SPI/PIO bridging to SPU-4 clusters.
// Also streams 104-byte Whisper frames to RP2040 visualiser over UART1.

#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/uart.h"
#include "pico/multicore.h"
#include <string.h>

#define SPU_CS_PIN   17
#define SPU_SCK_PIN  18
#define SPU_MOSI_PIN 19
#define SPU_MISO_PIN 16

// UART1 → RP2040 visualiser (GP4 TX, 921600 baud, 104-byte Whisper frames)
#define VIS_UART      uart1
#define VIS_UART_TX   4
#define VIS_BAUD      921600

#define AXES          13
#define FRAME_BYTES   (AXES * 8)  // 104

// Shared manifold state written by Core 1, read by Core 0 for transmission.
// Simple double-buffer: Core 1 writes to back, Core 0 reads from front.
static volatile uint8_t manifold_front[FRAME_BYTES];
static volatile uint8_t manifold_back[FRAME_BYTES];
static volatile bool    frame_ready = false;

// Core 1 Entry: High-speed SPI polling + manifold frame assembly
void core1_snap_monitor() {
    uint16_t local_dissonance = 0;
    bool local_snap = false;

    while (true) {
        get_spu_metrics(&local_dissonance, &local_snap);

        // Pack dissonance into a minimal Whisper frame:
        // Axis 0 rational = dissonance value; axis 0 surd = snap_lock flag.
        // Remaining axes zeroed until full manifold bus is wired.
        memset((void*)manifold_back, 0, FRAME_BYTES);
        manifold_back[0] = (local_dissonance >> 8) & 0xFF;
        manifold_back[1] =  local_dissonance & 0xFF;
        manifold_back[4] = local_snap ? 0x10 : 0x00; // Q12 surd: 0.0039 or 0

        frame_ready = true;

        sleep_ms(1);
    }
}

// Interrogation function
void get_spu_metrics(uint16_t *dissonance, bool *snap_lock) {
    uint8_t buffer[3];
    gpio_put(SPU_CS_PIN, 0); // Select the Nano
    
    // Command 0xAC: "Request 15-Sigma Status"
    uint8_t cmd = 0xAC;
    spi_write_blocking(spi0, &cmd, 1);
    spi_read_blocking(spi0, buffer, 3);
    
    gpio_put(SPU_CS_PIN, 1);
    
    *dissonance = (buffer[0] << 8) | buffer[1];
    *snap_lock = (buffer[2] & 0x01);
}

int main() {
    stdio_init_all();

    // UART1 → RP2040 visualiser
    uart_init(VIS_UART, VIS_BAUD);
    gpio_set_function(VIS_UART_TX, GPIO_FUNC_UART);

    // SPI0 → SPU-4 Nano Satellites
    spi_init(spi0, 1000 * 1000);
    gpio_set_function(SPU_SCK_PIN,  GPIO_FUNC_SPI);
    gpio_set_function(SPU_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(SPU_MISO_PIN, GPIO_FUNC_SPI);

    gpio_init(SPU_CS_PIN);
    gpio_set_dir(SPU_CS_PIN, GPIO_OUT);
    gpio_put(SPU_CS_PIN, 1);

    multicore_launch_core1(core1_snap_monitor);

    while (true) {
        if (frame_ready) {
            // Swap buffers and transmit over UART1 to RP2040
            memcpy((void*)manifold_front, (void*)manifold_back, FRAME_BYTES);
            frame_ready = false;
            uart_write_blocking(VIS_UART, (const uint8_t*)manifold_front, FRAME_BYTES);
        }
        sleep_ms(1);
    }

    return 0;
}
