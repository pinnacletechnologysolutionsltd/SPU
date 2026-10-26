/* Host harness: reads one command per stdin line, prints one result line. Integers only. */
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bmu.h"
#include "bmu_rtl.h"

static int rd(long long *v) { return scanf("%lld", v) == 1; }

static int rd32(int32_t *o)
{
    long long v;
    if (!rd(&v) || v < INT32_MIN || v > INT32_MAX) return 0;
    *o = (int32_t)v;
    return 1;
}

static int rd_surd(som_surd *s) { return rd32(&s->p) && rd32(&s->q); }

int main(void)
{
    char cmd[16];
    while (scanf("%15s", cmd) == 1) {
        if (!strcmp(cmd, "CMP")) {                       /* CMP ap aq bp bq */
            som_wide a, b;
            long long v[4];
            int k;
            for (k = 0; k < 4; k++) if (!rd(&v[k])) return 2;
            a.p = v[0]; a.q = v[1]; b.p = v[2]; b.q = v[3];
            printf("CMP %d %d\n", som_wide_lt(a, b), som_wide_le(a, b));
        } else if (!strcmp(cmd, "BOX")) {                /* BOX A B D */
            long long a, b, d;
            if (!rd(&a) || !rd(&b) || !rd(&d)) return 2;
            printf("BOX %d\n", a < 0 || b < 0 || d < 0 ? 0 : som_rtl_box_safe((uint32_t)a, (uint32_t)b, (uint32_t)d));
        } else if (!strcmp(cmd, "BMU")) {                /* BMU n {id label w[4]}xn r[4] x[4] thr */
            long long n, id, lab;
            som_node nodes[16];
            som_map map = {0};
            som_surd x[4], thr;
            som_result res;
            som_rtl_report rep;
            som_status st, rst;
            int k, j;
            if (!rd(&n) || n < 0 || n > 16) return 2;
            for (k = 0; k < n; k++) {
                if (!rd(&id) || !rd(&lab) || id < 0 || id > 255 || lab < 0 || lab > 255) return 2;
                nodes[k].id = (uint8_t)id; nodes[k].label = (uint8_t)lab;
                for (j = 0; j < 4; j++) if (!rd_surd(&nodes[k].w[j])) return 2;
            }
            for (j = 0; j < 4; j++) if (!rd_surd(&map.r[j])) return 2;
            for (j = 0; j < 4; j++) if (!rd_surd(&x[j])) return 2;
            if (!rd_surd(&thr)) return 2;
            map.node_count = (uint32_t)n; map.nodes = nodes;
            st = som_bmu(&map, x, &thr, &res);
            printf("BMU %d %d %d %d %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 " %" PRId64 " %d %d",
                   (int)st, res.best_id, res.second_id, res.label, res.best.p, res.best.q, res.second.p,
                   res.second.q, res.gap.p, res.gap.q, res.has_second, res.ambiguous);
            rst = som_bmu_rtl_safe(&map, x, &thr, &res, &rep);
            printf(" RTL %d %d %d %d\n", (int)rst, (int)rep.reason, rep.node, rep.feature);
        } else {
            return 2;
        }
    }
    return 0;
}
