#include "bmu.h"

/* Compile-time proofs of the width contract (C99: negative array size on failure). */
#define SOM_STATIC_ASSERT(name, cond) typedef char som_assert_##name[(cond) ? 1 : -1]
#define D_ ((unsigned long long)524287ULL / 2ULL)          /* 2^18 - 1 = 262143 */
#define R_ 131072ULL                                       /* max |coefficient| = 2^17 */
SOM_STATIC_ASSERT(d, D_ == 262143ULL);
SOM_STATIC_ASSERT(sp, 4ULL * D_ * D_ < (1ULL << 38));
SOM_STATIC_ASSERT(sq, 2ULL * D_ * D_ < (1ULL << 37));
SOM_STATIC_ASSERT(term_p, 10ULL * R_ * D_ * D_ < (1ULL << 57));
SOM_STATIC_ASSERT(term_q, 6ULL * R_ * D_ * D_ < (1ULL << 56));
SOM_STATIC_ASSERT(dist_p, 40ULL * R_ * D_ * D_ < (1ULL << 59));
SOM_STATIC_ASSERT(dist_q, 24ULL * R_ * D_ * D_ < (1ULL << 58));
SOM_STATIC_ASSERT(int64_room, 40ULL * R_ * D_ * D_ + 24ULL * R_ * D_ * D_ < (1ULL << 63));

typedef struct { uint64_t hi, lo; } u128;

static uint64_t abs_u64(int64_t v)
{
    return v < 0 ? (uint64_t)(-(v + 1)) + 1u : (uint64_t)v;        /* no overflow at INT64_MIN */
}

static u128 mul_u64(uint64_t a, uint64_t b)                        /* exact 64x64 -> 128 */
{
    uint64_t a0 = a & 0xffffffffu, a1 = a >> 32, b0 = b & 0xffffffffu, b1 = b >> 32;
    uint64_t p00 = a0 * b0, p01 = a0 * b1, p10 = a1 * b0, p11 = a1 * b1;
    uint64_t mid = (p00 >> 32) + (p01 & 0xffffffffu) + (p10 & 0xffffffffu);
    u128 r;
    r.lo = (p00 & 0xffffffffu) | (mid << 32);
    r.hi = p11 + (p01 >> 32) + (p10 >> 32) + (mid >> 32);
    return r;
}

static u128 add_u128(u128 a, u128 b)
{
    u128 r;
    r.lo = a.lo + b.lo;
    r.hi = a.hi + b.hi + (r.lo < a.lo ? 1u : 0u);
    return r;
}

static int cmp_u128(u128 a, u128 b)
{
    if (a.hi != b.hi) return a.hi < b.hi ? -1 : 1;
    if (a.lo != b.lo) return a.lo < b.lo ? -1 : 1;
    return 0;
}

/* da^2 vs 3 db^2 for |da| < 2^62, |db| < 2^61 (3 db^2 < 2^125: no 128-bit wrap). */
static int cmp_sq_vs_3sq(int64_t da, int64_t db)
{
    u128 a = mul_u64(abs_u64(da), abs_u64(da));
    u128 b = mul_u64(abs_u64(db), abs_u64(db));
    return cmp_u128(a, add_u128(add_u128(b, b), b));
}

int som_wide_lt(som_wide a, som_wide b)
{
    int64_t da = a.p - b.p, db = a.q - b.q;                        /* |.| < 2^62: no overflow */
    if (da == 0 && db == 0) return 0;
    if (da <= 0 && db <= 0) return 1;
    if (da >= 0 && db >= 0) return 0;
    if (da < 0) return cmp_sq_vs_3sq(da, db) > 0;                  /* da < 0 < db */
    return cmp_sq_vs_3sq(da, db) < 0;                              /* db < 0 < da */
}

int som_wide_le(som_wide a, som_wide b)
{
    return (a.p == b.p && a.q == b.q) || som_wide_lt(a, b);
}

som_wide som_distance(const som_node *n, const som_surd x[SOM_FEATURES], const som_surd r[SOM_FEATURES])
{
    som_wide t = {0, 0};
    int j;
    for (j = 0; j < SOM_FEATURES; j++) {
        int64_t dp = (int64_t)x[j].p - n->w[j].p, dq = (int64_t)x[j].q - n->w[j].q;
        int64_t sp = dp * dp + 3 * (dq * dq), sq = 2 * (dp * dq);
        t.p += (int64_t)r[j].p * sp + 3 * ((int64_t)r[j].q * sq);
        t.q += (int64_t)r[j].p * sq + (int64_t)r[j].q * sp;
    }
    return t;
}

static int in_range(int32_t c) { return c >= SOM_COEF_MIN && c <= SOM_COEF_MAX; }

static int map_ok(const som_map *m)
{
    uint32_t i, seen = 0;
    int j;
    for (j = 0; j < SOM_FEATURES; j++)
        if (!in_range(m->r[j].p) || !in_range(m->r[j].q)) return 0;
    for (i = 0; i < m->node_count; i++) {
        const som_node *n = &m->nodes[i];
        if (n->id >= SOM_NODES || (seen & (1u << n->id)) || n->label >= SOM_NODES) return 0;
        seen |= 1u << n->id;
        for (j = 0; j < SOM_FEATURES; j++)
            if (!in_range(n->w[j].p) || !in_range(n->w[j].q)) return 0;
    }
    return 1;
}

static int better(som_wide q, int32_t id, som_wide ref, int32_t ref_id, int has_ref)
{
    if (!has_ref) return 1;
    if (som_wide_lt(q, ref)) return 1;
    return q.p == ref.p && q.q == ref.q && id < ref_id;
}

som_status som_bmu(const som_map *map, const som_surd x[SOM_FEATURES], const som_surd *thr,
                   som_result *res)
{
    som_result out = {0};
    som_wide zero = {0, 0};
    uint32_t i;
    int j, have_best = 0, have_second = 0;
    int32_t best_label = 0;
    som_status st = SOM_OK;

    if (res) res[0] = out;
    if (!map || !x || !res) return SOM_INVALID_MAP;
    if (map->node_count == 0) return SOM_NO_NODES;
    if (map->node_count != SOM_NODES || !map->nodes || !map_ok(map)) return SOM_INVALID_MAP;
    for (j = 0; j < SOM_FEATURES; j++)
        if (!in_range(x[j].p) || !in_range(x[j].q)) st = SOM_OVERFLOW;
    if (st != SOM_OK) return st;

    out.best_id = out.second_id = -1;
    out.best = out.second = zero;
    for (i = 0; i < map->node_count; i++) {
        const som_node *n = &map->nodes[i];
        som_wide d = som_distance(n, x, map->r);
        if (better(d, n->id, out.best, out.best_id, have_best)) {
            if (have_best) { out.second_id = out.best_id; out.second = out.best; have_second = 1; }
            out.best_id = n->id; out.best = d; best_label = n->label; have_best = 1;
        } else if (better(d, n->id, out.second, out.second_id, have_second)) {
            out.second_id = n->id; out.second = d; have_second = 1;
        }
    }
    out.label = best_label;
    out.has_second = (uint8_t)have_second;
    if (have_second) { out.gap.p = out.second.p - out.best.p; out.gap.q = out.second.q - out.best.q; }
    {
        som_wide t;
        t.p = thr ? thr->p : 0;
        t.q = thr ? thr->q : 0;
        out.ambiguous = (uint8_t)(have_second && som_wide_le(out.gap, t));
    }
    res[0] = out;
    return SOM_OK;
}
