#include "bmu_rtl.h"

#define TERM_MIN (-(int64_t)34359738368)      /* -2^35 */
#define TERM_MAX ((int64_t)34359738367)       /*  2^35 - 1 */
#define P_MAX ((int64_t)4294967295)           /*  2^32 - 1 */
#define Q32_MIN (-(int64_t)2147483648)
#define Q32_MAX ((int64_t)2147483647)

static int fits18(int64_t d) { return d >= -131072 && d <= 131071; }

static void fail(som_rtl_report *rep, som_rtl_reason why, int32_t node, int32_t feature)
{
    if (rep) { rep->reason = why; rep->node = node; rep->feature = feature; }
}

som_status som_bmu_rtl_safe(const som_map *map, const som_surd x[SOM_FEATURES], const som_surd *thr,
                            som_result *res, som_rtl_report *rep)
{
    som_status st = som_bmu(map, x, thr, res);
    uint32_t i;
    int j;
    fail(rep, RTL_OK, -1, -1);
    if (st != SOM_OK) return st;
    for (i = 0; i < map->node_count; i++) {
        const som_node *n = &map->nodes[i];
        int64_t tp = 0, tq = 0;
        for (j = 0; j < SOM_FEATURES; j++) {
            int64_t dp = (int64_t)x[j].p - n->w[j].p, dq = (int64_t)x[j].q - n->w[j].q;
            int64_t sp = dp * dp + 3 * (dq * dq), sq = 2 * (dp * dq);
            int64_t wp = (int64_t)map->r[j].p * sp + 3 * ((int64_t)map->r[j].q * sq);
            int64_t wq = (int64_t)map->r[j].p * sq + (int64_t)map->r[j].q * sp;
            if (!fits18(dp) || !fits18(dq)) { fail(rep, RTL_DIFF, n->id, j); res[0] = (som_result){0}; return SOM_RTL_UNSAFE; }
            if (wp < TERM_MIN || wp > TERM_MAX || wq < TERM_MIN || wq > TERM_MAX) {
                fail(rep, RTL_TERM, n->id, j); res[0] = (som_result){0}; return SOM_RTL_UNSAFE;
            }
            tp += wp; tq += wq;
        }
        if (tp < 0 || tp > P_MAX || tq < Q32_MIN || tq > Q32_MAX) {
            fail(rep, RTL_SUM, n->id, -1); res[0] = (som_result){0}; return SOM_RTL_UNSAFE;
        }
    }
    if (res->has_second && (res->gap.p < 0 || res->gap.p > P_MAX || res->gap.q < Q32_MIN || res->gap.q > Q32_MAX)) {
        fail(rep, RTL_GAP, -1, -1); res[0] = (som_result){0}; return SOM_RTL_UNSAFE;
    }
    if (thr && thr->p < 0) { fail(rep, RTL_THRESH, -1, -1); res[0] = (som_result){0}; return SOM_RTL_UNSAFE; }
    return SOM_OK;
}

int som_rtl_box_safe(uint32_t A, uint32_t B, uint32_t D)
{
    uint64_t d2, p, q;
    if (D > 131071u || A > 131072u || B > 131072u) return 0;
    d2 = (uint64_t)D * D;
    p = (16ULL * A + 24ULL * B) * d2;
    q = (8ULL * A + 16ULL * B) * d2;
    return p <= 4294967295ULL && q <= 2147483647ULL;
}

int som_rtl_weight_p_nonneg(som_surd r)
{
    int64_t p = r.p, q = r.q;
    return p >= 0 && p * p >= 3 * (q * q);
}
