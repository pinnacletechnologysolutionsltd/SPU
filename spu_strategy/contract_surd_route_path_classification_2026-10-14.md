# Surd CPU routed-path classification diagnostic

**Date:** 2026-10-14
**Contract ID:** `contract_surd_route_path_classification_2026-10-14`
**Status:** DRAFT — preparation authorized; route execution awaits a frozen owner budget

## 1. Objective and scope

Complete one routing-only diagnostic for the frozen placed Surd CPU candidate
and publish a reproducible path-classification report. Capture the routes the
backend actually selected, then classify every selected timing path as
`SUPPORTED`, `CONSERVATIVELY_BOUNDED`, or `UNKNOWN` using the rules below.
Preserve placement and the logical netlist. Do not change the numerical timing
model or claim integrated 25 MHz qualification.

The baseline packet is
`build/spu_surd_register/backend_compatibility_20261012/routing_timing_preparation_01/`.
Its `input_identity.json`, `placement_artifact_audit.json`,
`timing_model_audit.json`, `proposed_route_binding.json`, and `REVIEW.md` are
read-only evidence. The static mapping is
`build/spu_surd_register/backend_compatibility_20261012/public_spec_mapping_01/`.
The checkpoint restoration closeout is
`build/spu_surd_register/backend_compatibility_20261012/checkpoint_restore_closeout_02/`.

## 2. Claims and classification rules

For each selected path, retain the actual routed cell pins, site wires, BELs,
net identities, source/endpoint, clock domain, and the backend path identifier.
Keep the raw backend timing observation separate from the classification; its
numeric value remains unqualified under the current model.

| Classification | Required evidence |
|---|---|
| `SUPPORTED` | The captured, selected path is wholly within a documented timing specification's stated endpoints, primitive mode, pins, conditions, and corner. Cite the specification and exact applicability evidence. Similar topology or a connectivity witness alone is insufficient. |
| `CONSERVATIVELY_BOUNDED` | A cited, defensible bound covers the complete selected path. Record the bound's direction, included/excluded path segments, assumptions, source, units, device/grade, process corner, and required coverage. Do not derive intrinsic cell delays by splitting a macro bound. |
| `UNKNOWN` | Applicable evidence does not cover the complete selected path, or an endpoint, mode, route segment, condition, source, or required corner is unresolved. State the missing obligation. |

Every path must receive exactly one classification. No path may be dropped
because the backend reports it as unconstrained, ignored, or lacking a timing
index; record that condition and classify it `UNKNOWN` unless a separately
reviewed required-boundary rule proves it out of scope. Identify paths omitted
by the backend report by comparing the routed design's clocks and required
timing boundary with the enumerated report paths.

The report must give total counts by classification and by path class, plus a
machine-readable row for every path. Preserve route and source hashes, exact
commands, tool and database identities, clock restoration evidence, parser
version, and report-generation command. State unresolved DSP, clock,
interconnect, IO, and corner obligations explicitly. The expected 80 DSP48s
must appear in the route inventory even if no applicable bound exists.

## 3. Halt-and-flag review before execution

The existing route argv is explicitly a draft. Before creating a launch packet,
review and resolve each item below without changing the frozen candidate,
backend, chip database, or timing model:

1. Prove the exact CLI and imported-checkpoint setting precedence for device,
   seed, router, constraints, and target frequency from the frozen executable.
2. Cold-load the exact placed checkpoint and verify connected netlist identity,
   all 51,197 cell bindings and unique BEL ownership, restored route state, and
   the source-audited primary and derived 25 MHz clock constraints.
3. Define falsifiable route completeness, ownership, legality, and placement
   preservation checks against the exact routed artifact schema. Include
   negative controls for a missing route, a conflicting owner, and changed
   placement or connectivity.
4. Define and validate the path extractor against native route data. It must
   preserve full path sequence and actual selected resource/pin identities;
   it must not infer the route from static site metadata or synthesize a path
   by joining connectivity witnesses.
5. Define the path-to-spec applicability checker and its negative controls.
   A deliberately similar but endpoint/mode-incompatible path must be refused;
   an uncovered DSP or interconnect path must remain `UNKNOWN`.
6. Freeze one output directory, all inputs and scripts, exact command,
   environment, tool versions, and a nonzero owner-authorized maximum attempt
   count, per-attempt timeout, and cumulative campaign budget. A launched
   attempt consumes a slot regardless of outcome.

If any gate fails, stop before route execution and publish the failing evidence
and minimal correction. Do not repair or replace the backend timing model.

## 4. Execution and evidence

After all pre-execution gates pass and the owner budget is recorded, launch the
single authorized route command through the repository detached runner with a
new child of `build/spu_surd_register/backend_compatibility_20261012/` as its
output directory. The route command must use the exact frozen placed JSON,
chip database, XDC and executable named by the reviewed packet, with packing,
placement changes, hold fixes, FASM/bitstream generation, and board activity
disabled. Retain the quoted command, source status, versions, stdout/stderr,
terminal marker, routed JSON, native timing report, route audit, path inventory,
classification JSON, and human-readable report.

Interpret a run only when exactly one `COMPLETE`, `FAILED`, or `TIMEOUT`
terminal marker exists. A successful process exit alone is not a PASS. The
diagnostic PASS requires a complete legal route, unchanged placement and
logical connectivity, and a complete classification inventory. Unknown paths
are valid diagnostic findings and do not fail the diagnostic if they are
explicitly represented. A missing or ambiguous path inventory fails the
diagnostic.

Do not automatically retry or extend a budget. After the detached runner
reports `LAUNCHED`, record its unit and evidence directory and end the agent
turn. A later invocation may interpret the durable terminal result.

## 5. Explicit exclusions and status boundary

- No timing values are inserted into, substituted in, or recalibrated against
  the backend model.
- No macro bound is decomposed into intrinsic cell or wire delays.
- No CPU/Surd/ISA/RTL change, place-and-route repair, or database regeneration.
- No silicon, board, energy, performance, or 25 MHz timing-closure claim.
- A complete route and path-classification report establish actual route
  selection and evidence applicability only. Integrated 25 MHz remains
  unqualified until full clock, DSP, interconnect, timing-corner and required
  setup/hold coverage is independently established.

Current baseline: placement/restoration `PASS`; static mapping `PREPARED`;
route selection and numerical timing-model qualification `PENDING`; integrated
25 MHz `UNQUALIFIED`.
