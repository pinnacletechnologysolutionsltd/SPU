/* RTL-safe classification for the CURRENT spu_som_bmu.v (not repaired). Derived separately from
 * bmu.c's exact bounds, from the RTL text: rs_weighted_quadrance (18-bit diff argument, 36-bit signed
 * ring arithmetic), the 64-bit sums truncated to q_accum_p[31:0] (UNSIGNED) / q_accum_q[31:0] (signed)
 * with overflow flag, the 33-bit comparator, and the 32-bit modular gap fields.
 *
 * The RTL reproduces the exact C result iff, for EVERY node (not only the winner):
 *   1. DIFF   : each Delta coefficient (x - w) is in [-2^17, 2^17-1]  (else the 18-bit argument wraps);
 *   2. TERM   : each exact weighted term term_p, term_q is in [-2^35, 2^35-1]. All 36-bit operations are
 *               ring operations, so intermediate s_p, s_q may wrap harmlessly; only the final term matters;
 *   3. SUM    : exact P total in [0, 2^32-1] (unsigned field, flag on negative) and exact Q total in
 *               [-2^31, 2^31-1];
 * and for the reported gap fields (32-bit modular, P unsigned, Q signed):
 *   4. GAP    : exact gap_p in [0, 2^32-1] and gap_q in [-2^31, 2^31-1];
 *   5. THRESH : the ambiguity threshold has p >= 0 (cluster_reduce zero-extends P).
 * Conditions are exact-value predicates, so they are sufficient for equality; they are not claimed
 * necessary (opposite wraps can cancel).
 */
#ifndef SOM_BMU_RTL_H
#define SOM_BMU_RTL_H
#include "bmu.h"

typedef enum { RTL_OK = 0, RTL_DIFF = 1, RTL_TERM = 2, RTL_SUM = 3, RTL_GAP = 4, RTL_THRESH = 5 } som_rtl_reason;
typedef struct { som_rtl_reason reason; int32_t node, feature; } som_rtl_report;

/* Exact classification, then SOM_OK only when the RTL reproduces it; otherwise SOM_RTL_UNSAFE with
 * *res zeroed (the RTL's wrong value is not computed). Other statuses pass through from som_bmu. */
som_status som_bmu_rtl_safe(const som_map *map, const som_surd x[SOM_FEATURES], const som_surd *thr,
                            som_result *res, som_rtl_report *rep);

/* Map-level sufficient certificate for distances (not gap fields): all inputs with |x - w| <= D
 * (D <= 2^17-1) and weight magnitudes |r_p| <= A, |r_q| <= B give no DIFF/TERM/SUM failure,
 * provided weights_p_nonneg(r) holds for every feature:
 *   P <= (16A+24B)D^2 <= 2^32-1,   |Q| <= (8A+16B)D^2 <= 2^31-1. */
int som_rtl_box_safe(uint32_t A, uint32_t B, uint32_t D);
/* r_p >= 0 and r_p^2 >= 3 r_q^2  =>  r*Delta^2 has P >= 0 for every Delta (PSD form). */
int som_rtl_weight_p_nonneg(som_surd r);
#endif
