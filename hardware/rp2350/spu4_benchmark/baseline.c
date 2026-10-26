// GPIO-free parity/kernel preflight, not the complete sensor-stream benchmark.
// R runs 120 frozen windows. No UART pins, sensor pins or flash pins configured.
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "hardware/structs/systick.h"
#include "bench_data.h"

typedef struct { uint32_t pre, kernel, total; edge_result result; uint8_t label, ok; } record;
static record records[120];
static inline uint32_t cycles(void) {
    __asm volatile ("" ::: "memory");
    return systick_hw->cvr;
}
static uint32_t elapsed(uint32_t a, uint32_t b) { return (a-b)&0xffffff; }

static void run(void) {
    uint32_t empty_start = cycles(), empty_end = cycles();
    uint64_t start_us = time_us_64();
    for (unsigned i=0; i<120; ++i) {
        bench_model model = models[cases[i].fold];
        int32_t samples[32], features[4];
        uint16_t scaled[4];
        memcpy(samples, cases[i].raw, sizeof(samples));
        uint64_t guard = time_us_64();
        uint32_t a=cycles();
        edge_features(samples, features);
        edge_scale(features, model.low, model.high, scaled);
        uint32_t b=cycles();
        edge_result result=edge_classify(scaled, model.w);
        uint32_t c=cycles();
        uint8_t label=model.labels[result.node];
        uint32_t d=cycles();
        // Reject possible 24-bit counter wrap ambiguity (>111 ms at 150 MHz).
        bool ok = time_us_64()-guard < 100000 &&
                  !memcmp(features, cases[i].features, sizeof(features)) &&
                  !memcmp(scaled, cases[i].scaled, sizeof(scaled)) &&
                  result.node==cases[i].node && result.distance==cases[i].distance &&
                  label==cases[i].label;
        records[i]=(record){elapsed(a,b),elapsed(b,c),elapsed(a,d),result,label,ok};
    }
    uint64_t batch_us=time_us_64()-start_us;
    printf("BEGIN,freeze=%s,hz=%lu,empty_cycles=%lu,batch_us=%llu\n",FREEZE_SHA,
           (unsigned long)clock_get_hz(clk_sys),(unsigned long)elapsed(empty_start,empty_end),
           (unsigned long long)batch_us);
    unsigned passed=0;
    for (unsigned i=0;i<120;++i) {
        record r=records[i]; passed+=r.ok;
        printf("CASE,%u,%lu,%lu,%lu,%u,%lu,%u,%u\n",i,
            (unsigned long)r.pre,(unsigned long)r.kernel,(unsigned long)r.total,
            r.result.node,(unsigned long)r.result.distance,r.label,r.ok);
    }
    printf("END,%u,120\n",passed);
}

int main(void) {
    set_sys_clock_khz(150000,true);
    stdio_init_all();
    systick_hw->csr=0;
    systick_hw->rvr=0xffffff;
    systick_hw->cvr=0;
    systick_hw->csr=5; // processor clock, enabled, no interrupt
    while (true) {
        int ch=getchar_timeout_us(10000);
        if (ch=='R') run();
    }
}
