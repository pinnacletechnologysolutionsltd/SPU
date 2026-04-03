cmake_minimum_required(VERSION 3.13)

# Target: Raspberry Pi Pico (RP2040) — visualiser & debug bridge
set(PICO_BOARD pico)

include(pico_sdk_import.cmake)

project(rp2040_visualiser C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

add_executable(rp2040_visualiser
    rp2040_visualiser.c
)

target_link_libraries(rp2040_visualiser
    pico_stdlib
    hardware_uart
    m
)

# USB CDC for PC connection; no UART stdio (UART1 reserved for RP2350 frames)
pico_enable_stdio_usb(rp2040_visualiser 1)
pico_enable_stdio_uart(rp2040_visualiser 0)

pico_add_extra_outputs(rp2040_visualiser)
