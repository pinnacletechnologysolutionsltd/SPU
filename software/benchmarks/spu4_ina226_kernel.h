#ifndef SPU4_INA226_KERNEL_H
#define SPU4_INA226_KERNEL_H
#include <stdint.h>
/* Approved Q=0 profile only; four nodes/features, inputs/weights 0..30000. */
typedef struct { uint32_t distance; uint8_t node; } edge_result;
void edge_features(const int32_t samples[32], int32_t features[4]);
void edge_scale(const int32_t features[4], const int32_t low[4],
                const int32_t high[4], uint16_t scaled[4]);
edge_result edge_classify(const uint16_t features[4], const uint16_t weights[4][4]);
#endif
