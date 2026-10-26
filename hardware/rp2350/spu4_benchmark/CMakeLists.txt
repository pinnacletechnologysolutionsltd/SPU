cmake_minimum_required(VERSION 3.13)
set(PICO_BOARD pico2)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(spu4_benchmark C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
get_filename_component(SPU_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)
add_custom_command(OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/bench_data.h
    COMMAND ${Python3_EXECUTABLE} ${SPU_ROOT}/tools/gen_spu4_benchmark_header.py
            --output ${CMAKE_CURRENT_BINARY_DIR}/bench_data.h
    DEPENDS ${SPU_ROOT}/tools/gen_spu4_benchmark_header.py
            ${SPU_ROOT}/docs/bench_captures/2026-09-08_spu4_ina226_freeze.json)
add_executable(spu4_baseline baseline.c ${CMAKE_CURRENT_BINARY_DIR}/bench_data.h
    ${SPU_ROOT}/software/benchmarks/spu4_ina226_kernel.c)
target_include_directories(spu4_baseline PRIVATE ${CMAKE_CURRENT_BINARY_DIR}
    ${SPU_ROOT}/software/benchmarks)
target_compile_options(spu4_baseline PRIVATE -O3 -Wall -Wextra -fstack-usage)
target_link_libraries(spu4_baseline pico_stdlib hardware_clocks)
# SRAM execution: leave the original MicroPython flash/filesystem intact.
pico_set_binary_type(spu4_baseline no_flash)
pico_enable_stdio_usb(spu4_baseline 1)
pico_enable_stdio_uart(spu4_baseline 0)
pico_add_extra_outputs(spu4_baseline)
