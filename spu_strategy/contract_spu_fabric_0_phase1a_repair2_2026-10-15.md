# SPU-FABRIC-0 Phase 1A Readback Cost Repair

**Date:** 2026-10-15  
**Status:** OWNER-AUTHORIZED — ONE REPAIR-2 ATTEMPT  
**Parent:** `contract_spu_fabric_0_phase1a_2026-10-15.md`  
**Attempt 1:** `build/spu_fabric/fabric_0_tracefreeze_01/result.json`  
**Attempt 2:** `build/spu_fabric/fabric_0_tracefreeze_02/result.json`

## Diagnosis

The second authorized attempt reached `profile trace serialization and
readback`, then timed out. Its stage evidence records 11.088 seconds for source
oracle extraction and validation and 43.809 seconds in the profile stage. The
specific timeout stage is now known.

The remaining cost was repeated whole-trace JSON work. For 288,794 records in
each of three profiles, the generator serialized each final record, then
decompressed every profile, parsed every record, serialized it again to check
canonical form, and serialized expected values again to recompute their
digest. That readback repeated substantial work after the write-time ordering,
source-oracle, and digest checks.

## Repair

1. Compute each canonical expected-value digest row once while making private
   source spools; replay those bytes in profile order.
2. Validate client ordering and exact per-client counts during profile writes.
3. On readback, verify gzip integrity, newline-terminated record count,
   decompressed canonical-stream hash, and compressed-file hash. Do not parse
   and re-serialize every output record a second time. Canonical encoding is
   guaranteed by the single canonical writer; the decompressed stream hash
   verifies that the published bytes are exactly those it emitted.
4. Preserve the complete source-oracle checks, deterministic profile schedule,
   D4 invalid-result policy, source hashes, and atomic publication behavior.

## Execution boundary

The owner authorized one Repair-2 attempt on 2026-10-15:

| Limit | Authorization |
|---|---:|
| Maximum attempts | 1 |
| Per-attempt timeout | 180 seconds |
| Cumulative budget | 180 seconds |
| Automatic retries | None |
| Detached-runner evidence | `build/spu_fabric/fabric_0_tracefreeze_03/runner/` |
| Generator evidence | `build/spu_fabric/fabric_0_tracefreeze_03/generation/` |

Verify all final and evidence paths are absent and verify the frozen sources
against `spu_strategy/spu_fabric_0_phase1a_repair2_sources_2026-10-15.sha256`.
Execute exactly once:

```bash
tools/run_detached_job.sh --output build/spu_fabric/fabric_0_tracefreeze_03/runner --timeout 180 --notify-desktop -- python3 -B tools/prepare_spu_fabric_0_traces.py --evidence-dir build/spu_fabric/fabric_0_tracefreeze_03/generation
```

This authorization covers repaired Phase 1A trace preparation only. It does
not authorize retries, timeout extension, Phase 1B, RTL, synthesis,
placement/routing, or hardware work.
