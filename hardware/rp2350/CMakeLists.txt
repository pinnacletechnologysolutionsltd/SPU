cmake_minimum_required(VERSION 3.13)

# Target: Raspberry Pi Pico 2 (RP2350)
set(PICO_BOARD pico2)

if(NOT DEFINED PICO_SDK_PATH AND DEFINED ENV{PICO_SDK_PATH})
    set(PICO_SDK_PATH "$ENV{PICO_SDK_PATH}")
endif()

if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/pico_sdk_import.cmake")
    include("${CMAKE_CURRENT_LIST_DIR}/pico_sdk_import.cmake")
elseif(DEFINED PICO_SDK_PATH AND EXISTS "${PICO_SDK_PATH}/external/pico_sdk_import.cmake")
    include("${PICO_SDK_PATH}/external/pico_sdk_import.cmake")
else()
    message(FATAL_ERROR "Set PICO_SDK_PATH to a Raspberry Pi Pico SDK checkout")
endif()

project(spu_rp2350 C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

option(SPU_ENABLE_PIRANHA "Enable RP2350 Piranha heartbeat PIO output" OFF)
option(SPU_ENABLE_WHISPER "Enable RP2350 Whisper PWI telemetry output" OFF)
option(SPU_RP2350_ZERO_HEADER_SPI
    "Use RP2350-Zero header-friendly SPI0 pinset: GP0 MISO, GP1 CS, GP2 SCK, GP3 MOSI"
    OFF)
option(SPU_RP2350_ZERO_G25_SPI
    "Use RP2350-Zero G-25 edge SPI0 pinset: GP20 MISO, GP21 CS, GP22 SCK, GP23 MOSI"
    OFF)
set(SPU_SD_SPI_PORT "spi1" CACHE STRING "SPI instance used for SPI-mode microSD")
set(SPU_SD_SCK_PIN "10" CACHE STRING "SPI-mode microSD SCK pin")
set(SPU_SD_MOSI_PIN "11" CACHE STRING "SPI-mode microSD MOSI/CMD pin")
set(SPU_SD_MISO_PIN "12" CACHE STRING "SPI-mode microSD MISO/DAT0 pin")
set(SPU_SD_CS_PIN "13" CACHE STRING "SPI-mode microSD CS/DAT3 pin")
set(SPU_SD_BAUD_HZ "8000000" CACHE STRING "SPI-mode microSD post-init baud rate")

set(SPU_SPI_PIN_DEFS "")
if(SPU_RP2350_ZERO_HEADER_SPI AND SPU_RP2350_ZERO_G25_SPI)
    message(FATAL_ERROR "Choose only one RP2350-Zero SPI pinset option")
elseif(SPU_RP2350_ZERO_HEADER_SPI)
    list(APPEND SPU_SPI_PIN_DEFS
        SPU_SPI_MISO_PIN=0
        SPU_SPI_CS_PIN=1
        SPU_SPI_SCK_PIN=2
        SPU_SPI_MOSI_PIN=3
    )
elseif(SPU_RP2350_ZERO_G25_SPI)
    list(APPEND SPU_SPI_PIN_DEFS
        SPU_SPI_MISO_PIN=20
        SPU_SPI_CS_PIN=21
        SPU_SPI_SCK_PIN=22
        SPU_SPI_MOSI_PIN=23
    )
endif()

set(FATFS_SOURCE_DIR "${PICO_SDK_PATH}/lib/tinyusb/lib/fatfs/source")
if(NOT EXISTS "${FATFS_SOURCE_DIR}/ff.c")
    message(FATAL_ERROR "FatFS source not found at ${FATFS_SOURCE_DIR}")
endif()

add_library(spu_rp_common
    ${FATFS_SOURCE_DIR}/ff.c
    ${FATFS_SOURCE_DIR}/ffsystem.c
    ${FATFS_SOURCE_DIR}/ffunicode.c
    ../rp_common/diskio.c
    ../rp_common/spu_boot.c
    ../rp_common/spu_diag.c
    ../rp_common/spu_link.c
    ../rp_common/spu_sd.c
    ../rp_common/spu_storage.c
                )

target_include_directories(spu_rp_common PUBLIC
    ${CMAKE_CURRENT_LIST_DIR}/../rp_common
    ${FATFS_SOURCE_DIR}
)

target_link_libraries(spu_rp_common PUBLIC
    pico_stdlib
    hardware_gpio
    hardware_spi
)

target_compile_definitions(spu_rp_common PUBLIC
    SPU_SD_SPI_PORT=${SPU_SD_SPI_PORT}
    SPU_SD_SCK_PIN=${SPU_SD_SCK_PIN}
    SPU_SD_MOSI_PIN=${SPU_SD_MOSI_PIN}
    SPU_SD_MISO_PIN=${SPU_SD_MISO_PIN}
    SPU_SD_CS_PIN=${SPU_SD_CS_PIN}
    SPU_SD_BAUD_HZ=${SPU_SD_BAUD_HZ}
)

add_executable(rp2350_spu_interface
    rp2350_spu_interface.c
)

# Generate PIO header from spu_bio_resonance.pio
pico_generate_pio_header(rp2350_spu_interface
    ${CMAKE_CURRENT_LIST_DIR}/../../software/common/pio/spu_bio_resonance.pio
)

target_link_libraries(rp2350_spu_interface
    pico_stdlib
    hardware_spi
    hardware_uart
    hardware_pio
    pico_multicore
    spu_rp_common
)

target_compile_definitions(rp2350_spu_interface PRIVATE
    SPU_ENABLE_PIRANHA=$<BOOL:${SPU_ENABLE_PIRANHA}>
    SPU_ENABLE_WHISPER=$<BOOL:${SPU_ENABLE_WHISPER}>
    ${SPU_SPI_PIN_DEFS}
)

pico_add_extra_outputs(rp2350_spu_interface)

pico_enable_stdio_usb(rp2350_spu_interface 1)
pico_enable_stdio_uart(rp2350_spu_interface 0)

# Minimal bring-up bridge for the proven Tang 25K RPLU full-probe top.
# PC USB CDC -> RP2350 UART1 TX GP4 -> FPGA periph_rx/B3 at 115200 baud.
add_executable(rp2350_uart_injector
    rp2350_uart_injector.c
)

target_link_libraries(rp2350_uart_injector
    pico_stdlib
    hardware_uart
)

pico_enable_stdio_usb(rp2350_uart_injector 1)
pico_enable_stdio_uart(rp2350_uart_injector 0)
pico_add_extra_outputs(rp2350_uart_injector)

# Interactive USB CDC console for FPGA SPI bring-up.
add_executable(rp2350_spu_diag
    rp2350_spu_diag.c
)

target_link_libraries(rp2350_spu_diag
    pico_stdlib
    hardware_spi
    spu_rp_common
)

set(SPU_DIAG_SPI_BAUD_HZ "" CACHE STRING
    "Override rp2350_spu_diag's SPI clock (default 2 MHz in-source). Needed \
below clk_fast on divided A7 core spins -- see AGENTS.md boot_ready notes.")
set(SPU_DIAG_SPI_BAUD_DEFS "")
if(SPU_DIAG_SPI_BAUD_HZ)
    list(APPEND SPU_DIAG_SPI_BAUD_DEFS SPI_BAUD_HZ=${SPU_DIAG_SPI_BAUD_HZ})
endif()

target_compile_definitions(rp2350_spu_diag PRIVATE
    ${SPU_SPI_PIN_DEFS}
    ${SPU_DIAG_SPI_BAUD_DEFS}
)

pico_enable_stdio_usb(rp2350_spu_diag 1)
pico_enable_stdio_uart(rp2350_spu_diag 0)
pico_add_extra_outputs(rp2350_spu_diag)

# Standalone SD/FAT32 smoke test. No FPGA connection required.
add_executable(spu_sd_test
    ../rp_common/spu_sd_test.c
)

target_link_libraries(spu_sd_test
    pico_stdlib
    hardware_spi
    spu_rp_common
)

pico_enable_stdio_usb(spu_sd_test 1)
pico_enable_stdio_uart(spu_sd_test 0)
pico_add_extra_outputs(spu_sd_test)

# Standalone SPI link test (exercises all Whisper Bridge commands)
add_executable(spu_link_test
    ../rp_common/spu_link_test.c
)

target_link_libraries(spu_link_test
    pico_stdlib
    hardware_spi
    spu_rp_common
)

target_compile_definitions(spu_link_test PRIVATE
    ${SPU_SPI_PIN_DEFS}
)

pico_enable_stdio_usb(spu_link_test 1)
pico_enable_stdio_uart(spu_link_test 0)
pico_add_extra_outputs(spu_link_test)

# RPLU2 arithmetic test driver — QLDI + QSUB via SPI
add_executable(rp2350_spu_arithmetic_test
    rp2350_spu_arithmetic_test.c
)

target_link_libraries(rp2350_spu_arithmetic_test
    pico_stdlib
    hardware_spi
    spu_rp_common
)

target_compile_definitions(rp2350_spu_arithmetic_test PRIVATE
    ${SPU_SPI_PIN_DEFS}
)

pico_enable_stdio_usb(rp2350_spu_arithmetic_test 1)
pico_enable_stdio_uart(rp2350_spu_arithmetic_test 0)
pico_add_extra_outputs(rp2350_spu_arithmetic_test)

# IROTC icosahedral test driver — LOAD2X/IROTC/SCALE2 via SPI (spec v0.2)
add_executable(rp2350_spu_irotc_test
    rp2350_spu_irotc_test.c
)

target_link_libraries(rp2350_spu_irotc_test
    pico_stdlib
    hardware_spi
    spu_rp_common
)

target_compile_definitions(rp2350_spu_irotc_test PRIVATE
    ${SPU_SPI_PIN_DEFS}
)

pico_enable_stdio_usb(rp2350_spu_irotc_test 1)
pico_enable_stdio_uart(rp2350_spu_irotc_test 0)
pico_add_extra_outputs(rp2350_spu_irotc_test)

# Repeating Wukong J11 Lucas sidecar smoke test. This avoids the interactive
# CDC write path while proving PSCALE/PCHIRAL/PMUL/PINV over SPI.
add_executable(rp2350_lucas_j11_smoke
    rp2350_lucas_j11_smoke.c
)

target_link_libraries(rp2350_lucas_j11_smoke
    pico_stdlib
    hardware_spi
    spu_rp_common
)

target_compile_definitions(rp2350_lucas_j11_smoke PRIVATE
    ${SPU_SPI_PIN_DEFS}
)

pico_enable_stdio_usb(rp2350_lucas_j11_smoke 1)
pico_enable_stdio_uart(rp2350_lucas_j11_smoke 0)
pico_add_extra_outputs(rp2350_lucas_j11_smoke)

# Repeating Wukong J11 SU3 sidecar smoke test. The FPGA SU3 bring-up spin
# uses a divided clk_fast, so the smoke test keeps SPI conservative by default.
add_executable(rp2350_su3_j11_smoke
    rp2350_su3_j11_smoke.c
)

target_link_libraries(rp2350_su3_j11_smoke
    pico_stdlib
    hardware_spi
    spu_rp_common
)

target_compile_definitions(rp2350_su3_j11_smoke PRIVATE
    ${SPU_SPI_PIN_DEFS}
)

pico_enable_stdio_usb(rp2350_su3_j11_smoke 1)
pico_enable_stdio_uart(rp2350_su3_j11_smoke 0)
pico_add_extra_outputs(rp2350_su3_j11_smoke)

# Wukong J11 RPLU2 config-transport smoke test. Hydrates the 149-record
# consume-probe profile and verifies the Artix SPUC telemetry frame.
add_executable(rp2350_rplu2_j11_smoke
    rp2350_rplu2_j11_smoke.c
)

target_link_libraries(rp2350_rplu2_j11_smoke
    pico_stdlib
    hardware_spi
    spu_rp_common
)

target_compile_definitions(rp2350_rplu2_j11_smoke PRIVATE
    ${SPU_SPI_PIN_DEFS}
)

pico_enable_stdio_usb(rp2350_rplu2_j11_smoke 1)
pico_enable_stdio_uart(rp2350_rplu2_j11_smoke 0)
pico_add_extra_outputs(rp2350_rplu2_j11_smoke)

# Wukong J11 RPLU2 Padé sidecar smoke test. This is the low-route-pressure
# Artix-7 proof spin: hydrate a direct Padé fixture, start opcode 0x2A,
# and verify QR commit lane 4 reports A31 value (2,0,0,0).
add_executable(rp2350_rplu2_pade_j11_smoke
    rp2350_rplu2_pade_j11_smoke.c
)

target_link_libraries(rp2350_rplu2_pade_j11_smoke
    pico_stdlib
    hardware_spi
    spu_rp_common
)

target_compile_definitions(rp2350_rplu2_pade_j11_smoke PRIVATE
    ${SPU_SPI_PIN_DEFS}
)

pico_enable_stdio_usb(rp2350_rplu2_pade_j11_smoke 1)
pico_enable_stdio_uart(rp2350_rplu2_pade_j11_smoke 0)
pico_add_extra_outputs(rp2350_rplu2_pade_j11_smoke)

# Wukong J11 electrical loopback smoke test. Talks raw SPI bytes to
# spu_a7_j11_loopback_top.v (no southbridge protocol -- that design
# bypasses spu_spi_slave.v entirely), verifying the bottom-row pin remap
# (J4/G4/B4/B5) carries a real bit-accurate signal in both directions.
add_executable(rp2350_j11_loopback_smoke
    rp2350_j11_loopback_smoke.c
)

target_link_libraries(rp2350_j11_loopback_smoke
    pico_stdlib
    hardware_spi
)

target_compile_definitions(rp2350_j11_loopback_smoke PRIVATE
    ${SPU_SPI_PIN_DEFS}
)

pico_enable_stdio_usb(rp2350_j11_loopback_smoke 1)
pico_enable_stdio_uart(rp2350_j11_loopback_smoke 0)
pico_add_extra_outputs(rp2350_j11_loopback_smoke)
