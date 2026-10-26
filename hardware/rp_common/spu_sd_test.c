#include "spu_sd.h"
#include "spu_storage.h"
#include "ff.h"
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include <stdio.h>
#include <string.h>

#define TEST_FILE_NAME "test.txt"
#define TEST_STRING    "Hello from RP2350 Southbridge!\n"

static int finish(int code) {
    printf("SD test halted with code %d.\n", code);
    fflush(stdout);
    while (true) {
        sleep_ms(1000);
    }
    return code;
}

int main() {
    stdio_init_all();
    while (!stdio_usb_connected()) {
        sleep_ms(100);
    }
    sleep_ms(200);
    printf("\n--- SPU SD Card Test ---\n");

    if (!spu_storage_init()) {
        printf("Error: Failed to initialize SD card or mount filesystem.\n");
        return finish(1);
    }
    printf("SD card and filesystem initialized successfully.\n");

    FIL fil;
    FRESULT fr;
    UINT bw, br;
    char read_buf[128];

    // 1. Create and write to a file
    printf("Creating and writing to %s...\n", TEST_FILE_NAME);
    fr = f_open(&fil, TEST_FILE_NAME, FA_CREATE_ALWAYS | FA_WRITE);
    if (fr != FR_OK) {
        printf("Error opening file for write: %d\n", fr);
        return finish(1);
    }
    fr = f_write(&fil, TEST_STRING, strlen(TEST_STRING), &bw);
    if (fr != FR_OK || bw != strlen(TEST_STRING)) {
        printf("Error writing to file: %d, bytes written: %u\n", fr, bw);
        f_close(&fil);
        return finish(1);
    }
    f_close(&fil);
    printf("Successfully wrote %u bytes to %s.\n", bw, TEST_FILE_NAME);

    // 2. Read from the file
    printf("Reading from %s...\n", TEST_FILE_NAME);
    fr = f_open(&fil, TEST_FILE_NAME, FA_READ);
    if (fr != FR_OK) {
        printf("Error opening file for read: %d\n", fr);
        return finish(1);
    }
    fr = f_read(&fil, read_buf, sizeof(read_buf) - 1, &br);
    if (fr != FR_OK) {
        printf("Error reading from file: %d\n", fr);
        f_close(&fil);
        return finish(1);
    }
    read_buf[br] = '\0'; // Null-terminate the read data
    f_close(&fil);
    printf("Successfully read %u bytes: '%s'\n", br, read_buf);
    if (strcmp(TEST_STRING, read_buf) == 0) {
        printf("Read data matches written data.\n");
    } else {
        printf("Error: Read data does NOT match written data!\n");
    }

    // 3. Delete the file
    printf("Deleting %s...\n", TEST_FILE_NAME);
    fr = f_unlink(TEST_FILE_NAME);
    if (fr != FR_OK) {
        printf("Error deleting file: %d\n", fr);
        return finish(1);
    }
    printf("Successfully deleted %s.\n", TEST_FILE_NAME);

    printf("--- SPU SD Card Test Complete ---\n");
    return finish(0);
}
