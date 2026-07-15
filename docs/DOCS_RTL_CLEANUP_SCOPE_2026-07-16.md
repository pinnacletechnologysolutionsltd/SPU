# Scoped task: SPU-4 docs, legacy-module cleanup, status-badge honesty

**Status:** Draft scope for review — not yet approved for execution.
**Origin:** Follows a doc-vs-RTL audit (Gemini, 2026-07-16) and the doc/claim-boundary
cleanup earlier the same day (see `AGENTS.md` git log, commits `37d24f6`/`ce835e2`/`d5a17e6`).
All facts below were verified directly against the tree on 2026-07-16, not taken from
the audit report at face value — see the "Verification notes" under each item.

This is a specification for someone (human or AI) to review and refine before any
file is touched. Nothing described here has been executed.

---

## Item 1 — SPU-4 dedicated architecture document

**Problem:** SPU-4 has real, tested RTL (14 files under `hardware/rtl/core/spu4/`)
and solid test coverage (12+ dedicated testbenches under `hardware/tests/spu4/` and
`hardware/tests/common/`, including a formal-verification harness for the Euclidean
ALU, `spu4_euclidean_alu_formal.sby`) — but there is no dedicated architecture
document for it. `find docs knowledge -iname "*spu4*" -o -iname "*sentinel*"`
returns nothing. The closest existing material is
`knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7 ("Deployment Architecture: The
Arlinghaus Constellation"), which covers SPU-4's dual edge/cluster role well but
is one section inside a doc that's primarily about spatial analysis, not
findable as "the SPU-4 spec."

**Proposed deliverable:** A new `knowledge/SPU4_ARCHITECTURE.md` (or similar name)
covering: the RTL module map (decoder/regfile/sequencer/dream_sequencer/
euclidean_alu/cluster_bridge/som_edge/boot_master/sovereign_bus/standalone_top/
core/top/sentinel), the dual-role split (standalone edge node vs. cluster
satellite — reusing Arlinghaus §7's framing rather than re-deriving it), the
cluster_bridge frame format (already documented in the module's own header
comment, worth pulling into prose), and a test-coverage table analogous to
`docs/hardware_evidence.md`'s per-subsystem sections. Cross-link from
`AGENTS.md` and `docs/SPIN_CATALOG.md` once it exists.

**Open question for review:** should this absorb Arlinghaus §7 (moving it out
of that doc) or just summarize-and-link? Moving it risks breaking
`ARLINGHAUS_SPATIAL_SYNTHESIS.md`'s own narrative arc; duplicating it risks
drift between two copies.

---

## Item 2 — Legacy module audit (bare `spu_*.v` naming)

**Problem:** 85 files under `hardware/rtl/` still use the pre-`spu13_`/`spu4_`
naming convention. Cross-referencing all 85 against every `.ys`/`.sh` build
script found **22 with zero direct references**:

```
spu_tetra_primitives.v   spu_som_sidecar_top.v   spu_som_node.v
spu_som_node_array.v     spu_sdram_ctrl_32bit.v  spu_mem_bridge_ddr3.v
spu_ghost_boot.v         spu_ecp5_prim.v         spu_ddr3_bridge_gowin.v
spu_davis_gate.v         spu_cartesian_quantizer.v  spu_cache_weight.v
spu_artery_tx.v
```

**Verification notes — do not treat the above as a confirmed-dead list.** The
"grep the filename against .ys/.sh" method has a real false-negative problem:
`spu_davis_gate.v` shows 0 direct references but is actually instantiated by
`spu_nano_core.v`, which *is* referenced elsewhere — it just never appears as
literal text in a synth script because Verilog module instantiation, not
filename mention, is what actually matters, and `-y` directory
auto-discovery (used by `run_all_tests.py` and some `.ys` flows) finds
modules without naming the file. Spot-checked two more: `spu_som_node.v` is
instantiated by `spu_som_node_array.v`, but that pair together has no
instantiator anywhere — looks like a genuinely orphaned subsystem, probably
superseded by the BRAM-backed `spu_som_bmu.v`/`spu_som_weight_bram.v` path
that the current SOM-SIDECAR spin actually uses (see 2026-07-16 session).
`spu_som_sidecar_top.v` (under `hardware/rtl/core/spu13/`, not the board
top) is confirmed genuinely dead — this is the exact orphaned cfg-bus
variant found and left alone during this session's SOM-SIDECAR fix (see
`hardware/tests/spu13/spu13_tang25k_som_sidecar_top_tb.v`'s own header
comment).

**Required before any deletion/archival:** for each of the 22, trace the
actual Verilog instantiation graph (`grep` for the bare module name as an
instance, not the filename), not just build-script text. A file can be
"live" via indirect instantiation even with zero `.ys` hits.

**Proposed deliverable:** a verified disposition for each of the 22 —
archive (matching the `hardware/boards/tang_primer_25k/archive/` convention
already established this session), delete outright if truly duplicate/dead,
or reclassify as "used but only reachable via instantiation" and leave alone.

**Explicitly out of scope for this task:** renaming the other 63 bare
`spu_*.v` files that *are* actively referenced, to match the `spu13_`/`spu4_`
convention. That's a much larger, higher-risk effort (touches every synth
script and board top that references them) and should be its own separate,
later-scoped task if wanted at all — don't fold it into this one.

---

## Item 3 — Status-badge honesty pass

**Problem:** Several `knowledge/` docs use the same "✅ implemented/tested"
vocabulary for both real, silicon/testbench-proven modules and purely
conceptual/future modules that don't exist in the tree at all. This is worse
than ordinary staleness — it actively misrepresents build status to a reader
(including anyone evaluating the project) rather than just being out of date.

**Confirmed instances:**
- `knowledge/RATIONAL_SHADER.md` — already flagged with a staleness banner
  this session (commit `37d24f6`), not yet resolved at the content level.
  Claims `spu_rasterizer.v`, `spu_fragment_pipe.v`, `spu_bresenham_killer.v`,
  `HAL_SDRAM_Winbond.v` as implemented/tested; none exist under those names.
- `knowledge/RATIONAL_SOM_NGUYEN_CLUSTER_NOTES.md` — not yet audited this
  session, flagged by the 2026-07-16 Gemini report as referencing
  `spu_nguyen_cluster.v`, `spu_nguyen_weight.v`, `spu_feature_ingest.v`,
  `spu_som_update.v`, none of which exist anywhere in the repo (verified).

**Proposed approach:** rather than a banner-only fix (which flags staleness
but leaves the misleading badges in the body), do a real per-claim pass:
for each module marked "✅"/"implemented"/"tested", either confirm it against
the tree and keep the badge, or change the badge to something honest
("planned", "conceptual", "not built") and say so plainly. Same discipline
already applied to `HARDWARE_MANIFEST_SPU13.md`'s Navier-Stokes/bio-coherence
claims (commit `ce835e2`) — the mechanism there was "keep what's real, cut
what isn't," not "delete the whole document."

**Open question for review:** should conceptual/future content be moved out
of `knowledge/` entirely into an explicit roadmap doc (clearly separating
"what exists" from "what's planned"), or is a strict, consistently-applied
badge convention within the existing docs sufficient? The former is a bigger
restructure; the latter is lower-risk but relies on nobody reintroducing an
inflated badge later.

---

## General notes for whoever executes this

- Verify every file-existence and reference claim directly (`find`/`grep`)
  before acting on it — this document's own claims were checked this way,
  and the source audit this task is based on had real errors (flagged files
  that actually existed, just outside the directory it searched). Don't
  compound that by trusting a second-hand summary of a summary.
- Run `python3 run_all_tests.py` before and after any RTL file is
  archived/deleted — 161/161 is the current baseline (2026-07-16).
- None of this touches the tensegrity workstream (GTP's in-flight
  TENSEGRITYLINK work) or SOM-SIDECAR's still-pending board run — keep this
  scoped to documentation and dead-code hygiene only.
