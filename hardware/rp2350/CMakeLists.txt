cmake_minimum_required(VERSION 3.13)

# Target: Raspberry Pi Pico 2 (RP2350)
set(PICO_BOARD pico2)

include(pico_sdk_import.cmake)

project(spu_rp2350 C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

add_executable(rp2350_spu_interface
    rp2350_spu_interface.c
)

target_link_libraries(rp2350_spu_interface
    pico_stdlib
    hardware_spi
    hardware_uart
    pico_multicore
)

pico_add_extra_outputs(rp2350_spu_interface)
