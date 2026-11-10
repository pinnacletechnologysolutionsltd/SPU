// GEN1-RESET-EDGE-1 Stage 0 reset-pulse generator (Raspberry Pi Pico 2).
// GP2 -> 4.7k -> NPN base; collector on KEY0 (or the bench stand-in). GP2 HIGH = reset asserted.
// GP2 is only ever driven by the PIO program and is never touched by CPU code after init.
// Default build (NPN pod): push-pull, idles LOW. GEN1_DIRECT_OD build (GP2 straight to KEY0): output
// latch fixed LOW, only the direction toggles (assert = drive LOW, idle = high-Z); it never drives HIGH.
// USB-CDC commands (one per line):
//   SEQ <wa_ns> <gap_ns> <wb_ns> <n> <period_ms>   n timed sequences; wb_ns 0 = no pulse B
//   HOLD <ms>                                      assert continuously for ms (meter check, <= 20000)
//   STATUS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "gen1_reset_pulse.pio.h"

#ifndef GEN1_DIRECT_OD
#define GEN1_DIRECT_OD 0
#endif
#define PULSE_PIN 2
#define MAX_NS    20000000000ULL   // 20 s; keeps every count far inside 32 bits at 150 MHz

static PIO pio = pio0;
static uint sm;
static uint32_t f_sys;

static uint64_t to_cycles(uint64_t ns) { return (ns * f_sys + 500000000ULL) / 1000000000ULL; }
static uint64_t to_ns(uint64_t cyc) { return (cyc * 1000000000ULL + f_sys / 2) / f_sys; }

#if GEN1_DIRECT_OD
#define SEQ_PROGRAM gen1_reset_seq_od_program
#define SEQ_CONFIG  gen1_reset_seq_od_program_get_default_config
#define IDLE_DIR    0u                                               // high-Z
#else
#define SEQ_PROGRAM gen1_reset_seq_program
#define SEQ_CONFIG  gen1_reset_seq_program_get_default_config
#define IDLE_DIR    (1u << PULSE_PIN)                                // driven LOW
#endif

static void pulse_init(void) {
    uint off = pio_add_program(pio, &SEQ_PROGRAM);
    sm = pio_claim_unused_sm(pio, true);
    pio_sm_config c = SEQ_CONFIG(off);
    sm_config_set_set_pins(&c, PULSE_PIN, 1);
    sm_config_set_clkdiv(&c, 1.0f);
    pio_sm_init(pio, sm, off, &c);                                   // SM stays disabled here
    pio_sm_set_pins_with_mask(pio, sm, 0, 1u << PULSE_PIN);          // output latch LOW first
    pio_sm_set_pindirs_with_mask(pio, sm, IDLE_DIR, 1u << PULSE_PIN);
    pio_gpio_init(pio, PULSE_PIN);                                   // then mux to PIO (sets IE, clears ISO)
    gpio_set_input_enabled(PULSE_PIN, false);                        // RP2350-E9: keep input buffer off
#if GEN1_DIRECT_OD
    gpio_disable_pulls(PULSE_PIN);                                   // leave the KEY0 net to R37 alone
#endif
    pio_interrupt_clear(pio, 0);
    pio_sm_set_enabled(pio, sm, true);
}

// Run one sequence; returns false on a 30 s completion timeout.
static bool run_seq(uint32_t wa, uint32_t gap, uint32_t wb) {
    pio_interrupt_clear(pio, 0);
    pio_sm_put_blocking(pio, sm, wa);
    pio_sm_put_blocking(pio, sm, gap);
    pio_sm_put_blocking(pio, sm, wb);
    absolute_time_t limit = make_timeout_time_ms(30000);
    while (!pio_interrupt_get(pio, 0))
        if (absolute_time_diff_us(get_absolute_time(), limit) < 0) return false;
    pio_interrupt_clear(pio, 0);
    return true;
}

static void cmd_seq(uint64_t wa_ns, uint64_t gap_ns, uint64_t wb_ns, uint32_t n, uint32_t period_ms) {
    uint64_t ca = to_cycles(wa_ns), cg = to_cycles(gap_ns), cb = to_cycles(wb_ns);
    if (wa_ns > MAX_NS || gap_ns > MAX_NS || wb_ns > MAX_NS || ca < 3 || cg < 5 || (wb_ns && cb < 3)
        || n < 1 || n > 100) { printf("ERR range\n"); return; }
    uint64_t total_ns = wa_ns + gap_ns + wb_ns;
    if (total_ns > 25000000000ULL || period_ms > 60000) { printf("ERR range\n"); return; }
    if ((uint64_t)period_ms * 1000000ULL < total_ns + 3000000ULL) { printf("ERR period\n"); return; }
    uint32_t wa = (uint32_t)(ca - 2), gap = (uint32_t)(cg - 4), wb = wb_ns ? (uint32_t)(cb - 2) : 0;
    printf("SEQ f_sys=%lu a_ns=%llu gap_ns=%llu b_ns=%llu n=%lu period_ms=%lu\n",
           (unsigned long)f_sys, to_ns(wa + 2ULL), to_ns(gap + 4ULL), wb ? to_ns(wb + 2ULL) : 0ULL,
           (unsigned long)n, (unsigned long)period_ms);
    absolute_time_t t0 = make_timeout_time_ms(100);
    for (uint32_t k = 0; k < n; k++) {
        sleep_until(delayed_by_ms(t0, k * period_ms));
        uint64_t t_us = time_us_64();
        if (!run_seq(wa, gap, wb)) { printf("ERR timeout k=%lu\n", (unsigned long)k); return; }
        printf("TRIAL %lu t_us=%llu\n", (unsigned long)k, t_us);
    }
    printf("DONE\n");
}

int main(void) {
    stdio_init_all();
    f_sys = clock_get_hz(clk_sys);
    pulse_init();
    char line[96]; size_t len = 0;
    for (;;) {
        int ch = getchar_timeout_us(100000);
        if (ch == PICO_ERROR_TIMEOUT) continue;
        if (ch != '\n' && ch != '\r') { if (len < sizeof line - 1) line[len++] = (char)ch; continue; }
        line[len] = 0; len = 0;
        unsigned long long a, g, b; unsigned long n, p, ms;
        if (sscanf(line, "SEQ %llu %llu %llu %lu %lu", &a, &g, &b, &n, &p) == 5) cmd_seq(a, g, b, n, p);
        else if (sscanf(line, "HOLD %lu", &ms) == 1) {
            if (ms < 1 || ms > 20000) printf("ERR range\n");
            else { printf("HOLD %lu ms\n", ms); cmd_seq(ms * 1000000ULL, 1000, 0, 1, ms + 10); }
        } else if (!strncmp(line, "STATUS", 6))
            printf("STATUS gen1_reset_pulse mode=%s pin=GP%d f_sys=%lu idle\n",
                   GEN1_DIRECT_OD ? "direct-od" : "npn-pushpull", PULSE_PIN, (unsigned long)f_sys);
        else if (line[0]) printf("ERR unknown\n");
    }
}
