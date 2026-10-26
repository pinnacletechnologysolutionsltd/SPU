# SPU-FABRIC-0 Phase 1A Timeout Repair

**Date:** 2026-10-15  
**Status:** OWNER-AUTHORIZED — ONE REPAIR ATTEMPT  
**Parent:** `contract_spu_fabric_0_phase1a_2026-10-15.md`  
**Timed-out attempt:** `build/spu_fabric/fabric_0_tracefreeze_01/result.json`

## Diagnosis

The authorized 55-second attempt terminated with `TIMEOUT`, exit status 124.
The result marker records a timeout but no per-stage progress, so it does not
establish the exact point reached. Source inspection identifies repeated work
as the primary runtime defect: each of the three profiles regenerated all
288,132 D4 rows and reran formula, specialized-oracle, norm, and involution
checks. The writer then canonicalized and compressed each full trace at gzip
level 9 and decompressed, parsed, re-canonicalized, and rehashed it for
readback. The same source workload was therefore validated three times.

This is a trace-preparation implementation inefficiency. It is not evidence of
a D4 arithmetic disagreement. The expired attempt published no fixtures or
manifest; its output paths remain absent.

## Repair

1. Generate and independently validate each source stream once into private,
   canonical JSONL spool files beneath fixture staging.
2. Build all three arrival profiles by replaying those validated source rows.
   Preserve the exact source order, offered-cycle rules, complete counts, and
   independent-oracle checks from the parent Phase 1A contract.
3. Use deterministic gzip level 1 (`mtime=0`, empty embedded filename). Record
   the compression settings and source-spool counts in manifest schema v2.
4. Record elapsed time by generator stage and include the active stage in
   failure and timeout evidence.
5. Retain D4 invalid-result semantics: invalid status is checked, result bits
   remain undefined, and those bits are excluded from expected digests.

## Execution boundary

The owner authorized one repaired rerun on 2026-10-15. Apply the prior frozen
per-attempt timeout to this single additional slot:

| Limit | Authorization |
|---|---:|
| Maximum attempts | 1 |
| Per-attempt timeout | 55 seconds |
| Cumulative budget | 55 seconds |
| Automatic retries | None |
| Evidence directory | `build/spu_fabric/fabric_0_tracefreeze_02/` |

Preserve the timed-out attempt and original source lock. Before launch, verify
the three final fixture paths and the new evidence directory are absent, then
verify `spu_strategy/spu_fabric_0_phase1a_repair_sources_2026-10-15.sha256`.
Execute exactly once:

```bash
timeout 55s python3 -B tools/prepare_spu_fabric_0_traces.py --evidence-dir build/spu_fabric/fabric_0_tracefreeze_02
```

This authorization covers repaired Phase 1A trace preparation only. It does
not authorize retries, timeout extension, Phase 1B, RTL, synthesis,
placement/routing, or hardware work.
