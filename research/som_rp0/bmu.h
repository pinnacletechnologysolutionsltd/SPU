/* SOM-RP0a: oracle-exact portable C99 BMU over the complete SOM v1 signed-18-bit domain.
 * No float, no allocation, no signed overflow, no shifts of negative values.
 *
 * Width contract (derived; checked by compile-time assertions in bmu.c).
 *   x, w, r coefficients c:  -2^17 <= c <= 2^17-1                 (18-bit signed, int32 storage)
 *   Delta = x - w:           |Delta| <= D = 2^18-1                (19-bit signed)
 *   s_p = Dp^2 + 3 Dq^2:     0 <= s_p <= 4 D^2   < 2^38
 *   s_q = 2 Dp Dq:           |s_q| <= 2 D^2      < 2^37
 *   term_p = rp s_p + 3 rq s_q: |.| <= 10 * 2^17 * D^2 < 2^57   (term_q: <= 6 * 2^17 * D^2 < 2^56)
 *   distance P (4 terms):    |P| <= 40 * 2^17 * D^2 < 2^59,  |Q| <= 24 * 2^17 * D^2 < 2^58  (int64)
 *   gap = second - best:     |gap_p| < 2^60, |gap_q| < 2^59        (int64)
 *   ordering: da, db = coefficient differences, |da| < 2^60, |db| < 2^59, and the test needs
 *   da^2 against 3 db^2 (< 2^120 and < 3*2^118): 128-bit unsigned compare, built from
 *   32x32->64 partial products (no __int128).
 * Out-of-domain inputs are refused, never wrapped: map coefficient/shape errors -> INVALID_MAP,
 * feature coefficient outside the 18-bit range -> OVERFLOW. On any non-OK status *res is zeroed.
 */
#ifndef SOM_BMU_H
#define SOM_BMU_H
#include <stdint.h>

#define SOM_FEATURES 4
#define SOM_NODES 7
#define SOM_COEF_MIN (-131072)
#define SOM_COEF_MAX 131071

typedef struct { int32_t p, q; } som_surd;    /* p + q*sqrt(3), 18-bit coefficients */
typedef struct { int64_t p, q; } som_wide;    /* distances and gaps */
typedef struct { uint8_t id; uint8_t label; som_surd w[SOM_FEATURES]; } som_node;
typedef struct { uint32_t node_count; const som_node *nodes; som_surd r[SOM_FEATURES]; } som_map;

typedef enum { SOM_OK = 0, SOM_OVERFLOW = 1, SOM_INVALID_MAP = 2, SOM_NO_NODES = 3,
               SOM_RTL_UNSAFE = 4 /* only from bmu_rtl.c */ } som_status;

typedef struct {
    int32_t best_id, second_id, label;
    som_wide best, second, gap;
    uint8_t has_second, ambiguous;
} som_result;

/* Exact order on p + q*sqrt(3), integer-only; arguments need |p| < 2^61, |q| < 2^60. */
int som_wide_lt(som_wide a, som_wide b);
int som_wide_le(som_wide a, som_wide b);

/* thr: ambiguity threshold (NULL = zero): ambiguous iff has_second and gap <= thr. */
som_status som_bmu(const som_map *map, const som_surd x[SOM_FEATURES], const som_surd *thr,
                   som_result *res);
/* Weighted distance sum_j r_j (x_j - w_j)^2 for one node, inputs already validated. */
som_wide som_distance(const som_node *n, const som_surd x[SOM_FEATURES], const som_surd r[SOM_FEATURES]);
#endif
