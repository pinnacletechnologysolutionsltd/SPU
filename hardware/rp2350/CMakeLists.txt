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
)

pico_add_extra_outputs(rp2350_spu_interface)

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
