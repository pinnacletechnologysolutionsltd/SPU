cmake_minimum_required(VERSION 3.13)

# Target: Raspberry Pi Pico (RP2040) — visualiser & debug bridge
set(PICO_BOARD pico)

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

add_executable(rp2040_flash_pmod
    rp2040_flash_pmod.c
)

target_link_libraries(rp2040_flash_pmod
    pico_stdlib
    hardware_spi
)

# USB CDC command channel; SPI pins are wired to the flash PMOD.
pico_enable_stdio_usb(rp2040_flash_pmod 1)
pico_enable_stdio_uart(rp2040_flash_pmod 0)

pico_add_extra_outputs(rp2040_flash_pmod)
