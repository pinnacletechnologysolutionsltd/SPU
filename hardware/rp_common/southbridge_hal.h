/**
 * @file southbridge_hal.h
 * @brief Hardware Abstraction Layer for SPU-13 Southbridge
 *
 * This header defines a platform-agnostic interface for Southbridge operations.
 * All platform-specific implementations must expose these functions.
 *
 * Supported platforms:
 *  - RP2350 (reference, proven in silicon)
 *  - Teensy 4.1 / i.MX RT1062 (FlexIO, planned Q4 2026)
 *  - LPC55S69 (FlexIO, planned Q1 2027)
 *  - ESP32-S3 (WiFi gateway, planned Q2 2027)
 *
 * @date 2026-06-29
 * @author GitHub Copilot CLI
 */

#ifndef SOUTHBRIDGE_HAL_H
#define SOUTHBRIDGE_HAL_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Platform enumeration — set at compile time via -DSB_PLATFORM_XXX
 */
enum sb_platform_t {
    SB_PLATFORM_RP2350 = 0,
    SB_PLATFORM_TEENSY41 = 1,
    SB_PLATFORM_LPC55S69 = 2,
    SB_PLATFORM_ESP32S3 = 3,
};

/**
 * SPI Command Opcodes (from FPGA spu_spi_slave.v)
 */
#define SB_CMD_MANIFOLD_BURST   0xA0
#define SB_CMD_STATUS           0xAC
#define SB_CMD_INSTRUCTION      0xB1
#define SB_CMD_RPLU_CONFIG      0xA5
#define SB_CMD_SCALE            0xA1
#define SB_CMD_QR_READ          0xA2
#define SB_CMD_HEX_READ         0xA3
#define SB_CMD_SENTINEL_READ    0xA4
#define SB_CMD_TELEMETRY_STATUS 0xB0
#define SB_CMD_TGR1_LOAD        0xB2
#define SB_CMD_TGR1_STATUS      0xB3

/**
 * @brief Initialize SPI master interface
 * @param clock_hz Clock frequency in Hz (1MHz to 20MHz typical)
 * @return true if successful, false on error
 */
bool sb_spi_init(uint32_t clock_hz);

/**
 * @brief Assert SPI Chip Select (CS# low)
 */
void sb_spi_cs_assert(void);

/**
 * @brief Deassert SPI Chip Select (CS# high)
 */
void sb_spi_cs_deassert(void);

/**
 * @brief Transfer one byte over SPI
 * @param tx_byte Byte to transmit
 * @return Byte received from FPGA
 *
 * Note: This is a full-duplex operation. The implementation must ensure
 * proper timing to avoid setup/hold violations on FPGA side.
 */
uint8_t sb_spi_xfer_byte(uint8_t tx_byte);

/**
 * @brief Transfer block of data over SPI
 * @param tx_buf Buffer to transmit (NULL for don't-care)
 * @param rx_buf Buffer to receive into (NULL to discard)
 * @param len Number of bytes to transfer
 *
 * Note: If tx_buf is NULL, 0x00 is transmitted. If rx_buf is NULL, data is
 * received and discarded.
 */
void sb_spi_xfer_block(const uint8_t *tx_buf, uint8_t *rx_buf, size_t len);

/**
 * PIO-Equivalent State Machine Interface
 * Generates Piranha Pulse (61.44 kHz) and custom I/O waveforms
 */

/**
 * @brief Initialize PIO-equivalent state machine
 * @return true if successful
 *
 * Sets up the state machine(s) to generate cycle-accurate timing pulses.
 * Must be deterministic with <10 ns timing variation.
 */
bool sb_pio_init(void);

/**
 * @brief Send Piranha Pulse (61.44 kHz, 50% duty cycle)
 * @param width_cycles Number of 61.44 kHz cycles to emit (typically 8, 13, or 21)
 *
 * This function must:
 *  1. Be cycle-accurate (deterministic latency <10 ns)
 *  2. Not be preempted by OS (disable interrupts if needed)
 *  3. Emit exactly the requested number of pulses
 *  4. Return only after the last pulse has completed
 */
void sb_pio_send_pulse(uint16_t width_cycles);

/**
 * @brief Configure Quadray vector on I/O pins (optional, platform-dependent)
 * @param q0 First axis component
 * @param q1 Second axis component
 * @param q2 Third axis component
 * @param q3 Fourth axis component
 *
 * Platform implementations may stub this if GPIO output isn't needed.
 */
void sb_pio_config_quadray(uint32_t q0, uint32_t q1, uint32_t q2, uint32_t q3);

/**
 * UART Telemetry Interface
 * Used for high-level telemetry, debug console, and status reporting
 */

/**
 * @brief Initialize UART for telemetry
 * @param baud Baud rate (typically 115200)
 * @return true if successful
 */
bool sb_uart_init(uint32_t baud);

/**
 * @brief Transmit one character
 * @param c Character to send
 */
void sb_uart_putc(uint8_t c);

/**
 * @brief Receive one character (blocking)
 * @return Character received
 */
uint8_t sb_uart_getc_blocking(void);

/**
 * @brief Receive one character (non-blocking)
 * @param c Pointer to destination byte
 * @return true if data available, false if empty
 */
bool sb_uart_getc_nonblocking(uint8_t *c);

/**
 * Utility Functions (platform-agnostic helpers)
 */

/**
 * @brief Query which platform is running
 * @return enum sb_platform_t
 */
enum sb_platform_t sb_get_platform(void);

/**
 * @brief Get platform clock frequency
 * @return Clock frequency in Hz
 */
uint32_t sb_get_clock_hz(void);

/**
 * @brief Get platform name (for debug output)
 * @return Null-terminated string (e.g., "RP2350", "Teensy 4.1")
 */
const char *sb_get_platform_name(void);

/**
 * @brief Millisecond-accurate delay (best-effort)
 * @param ms Milliseconds to delay
 *
 * Note: This is NOT cycle-accurate. Use sb_pio_send_pulse() for
 * deterministic timing.
 */
void sb_delay_ms(uint32_t ms);

/**
 * Platform-specific initialization hook
 * Called by sb_init() after all HAL functions are bound.
 */
void sb_platform_init_hook(void);

/**
 * Main initialization — call this once at startup
 * Returns true if all subsystems initialized successfully
 */
bool sb_init(uint32_t spi_clock_hz, uint32_t uart_baud);

#ifdef __cplusplus
}
#endif

#endif // SOUTHBRIDGE_HAL_H
