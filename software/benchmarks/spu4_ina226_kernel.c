#include "spu4_ina226_kernel.h"
#include <limits.h>

/* Exact signed round-to-nearest, ties-even. Denominator strictly positive.
 * Input ranges are int32 samples and derived sums; INT64_MIN cannot occur. */
static int64_t magnitude(int64_t x) { return x < 0 ? -x : x; }
static int32_t even_ratio(int64_t n, int64_t d) {
    int64_t a = magnitude(n), q = a / d, r = a % d;
    q += (2*r > d) | ((2*r == d) & (q & 1));
    return (int32_t)(n < 0 ? -q : q);
}

void edge_features(const int32_t s[32], int32_t f[4]) {
    int64_t sum = 0, delta = 0, deviation = 0;
    int32_t low = s[0], high = s[0];
    for (unsigned i = 0; i < 32; ++i) {
        sum += s[i];
        low = s[i] < low ? s[i] : low;
        high = s[i] > high ? s[i] : high;
    }
    for (unsigned i = 0; i < 31; ++i)
        delta += magnitude((int64_t)s[i+1] - s[i]);
    for (unsigned i = 0; i < 32; ++i)
        deviation += magnitude(32*(int64_t)s[i] - sum);
    f[0] = even_ratio(sum, 32000);
    f[1] = even_ratio((int64_t)high-low, 1000);
    f[2] = even_ratio(delta, 31000);
    f[3] = even_ratio(deviation, 1024000);
}

void edge_scale(const int32_t f[4], const int32_t low[4],
                const int32_t high[4], uint16_t out[4]) {
    for (unsigned i = 0; i < 4; ++i) {
        int32_t x = f[i] < low[i] ? low[i] : f[i];
        x = x > high[i] ? high[i] : x;
        out[i] = (uint16_t)even_ratio(((int64_t)x-low[i])*30000,
                                     (int64_t)high[i]-low[i]);
    }
}

edge_result edge_classify(const uint16_t f[4], const uint16_t w[4][4]) {
    edge_result best = {UINT32_MAX, 0};
    for (unsigned n = 0; n < 4; ++n) {
        uint32_t distance = 0;
        for (unsigned i = 0; i < 4; ++i) {
            int32_t d = (int32_t)f[i] - w[n][i];
            distance += (uint32_t)((int64_t)d*d);
        }
        uint32_t take = distance < best.distance;
        uint32_t mask = 0u - take;
        best.distance = (distance & mask) | (best.distance & ~mask);
        best.node = (uint8_t)((n & mask) | (best.node & ~mask));
    }
    return best;
}
