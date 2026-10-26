# Engineering Contract: SIM-G2A-R2 Parser Rejection Controls

**Date:** 2026-10-18

**Contract ID:** `sim_g2a_r2_parser_rejections_2026-10-18`
**Status:** PROPOSED — REVIEW ONLY; IMPLEMENTATION AND EXECUTION NOT AUTHORIZED

**Spec Author:** Codex

**Halt-and-Flag Implementer:** Owner-assigned C++ implementer
**Integration Auditor:** Owner-assigned reviewer

## 1. Objective and scope

Complete only the missing parser rejection coverage required by the frozen
SIM-G2A contract. Do not modify the encoder, parser, packet writer, renderer,
ISA, ROM, RTL, FPGA flow, CMake configuration, or production executable.

### Allowed target

- `../spu-sim/tests/test_t1d_scene.cpp`
- Test-only inline input strings in that file. Add fixture files only if an
  input cannot be represented clearly inline; no production fixture changes.

The test amendment must validate the current implementation. If any test finds
behavior contrary to the frozen contract, halt and preserve the failing test
and evidence. Do not change implementation code, weaken the test, or retry.

## 2. Frozen baseline identity

Before editing, verify that the standalone simulator remains at base commit
`013acd4230442e0e126640604c11176f274962ab` and that these artifacts match:

| Artifact | SHA-256 |
|---|---|
| Existing `build/sim-g2a/spu-sim` | `ca524aaedd5a61c6bb469d5fcdf57552c4044a15c4ddf6317b9428911b4ac847` |
| Existing `tests/test_t1d_scene.cpp` | `a78f30ebaf3839404a63b7119009f75136262f4d3cd732f34ae48118d6317d57` |

The implementation source hashes and fixture manifest hash from the SIM-G2A
qualification record also remain the baseline. Record all hashes and the
pre-amendment dirty status in the R2 evidence note. If the executable or any
implementation source identity differs, halt before editing.

## 3. Required rejection matrix

Extend the existing C++ parser/CLI tests to cover each case below. For parser
unit cases, assert the stable diagnostic category exactly. For CLI cases,
assert a nonzero process exit, the expected diagnostic on stderr, and the
specified output-file behavior.

| Category | Input/control | Required result |
|---|---|---|
| x upper bound | `x=640` | `SCENE_RANGE` |
| y upper bound | `y=480` | `SCENE_RANGE` |
| z upper bound | `z=65536` | `SCENE_RANGE` |
| RGB upper bound | one channel `16` | `SCENE_RANGE` |
| Triangle count | one triangle | `SCENE_SCHEMA` |
| Triangle count | three triangles | `SCENE_SCHEMA` |
| Vertex tuple arity | two coordinates | `SCENE_SCHEMA` |
| Vertex tuple arity | four coordinates | `SCENE_SCHEMA` |
| RGB tuple arity | two channels | `SCENE_SCHEMA` |
| RGB tuple arity | four channels | `SCENE_SCHEMA` |
| Degenerate geometry | repeated vertices | `SCENE_DEGENERATE` |
| Degenerate geometry | three distinct collinear vertices | `SCENE_DEGENERATE` |

For invalid CLI inputs, prove that a previously absent destination remains
absent. For a destination pre-created with sentinel bytes, prove that it remains
byte-for-byte unchanged. Keep the already passing tests for malformed syntax,
duplicate/missing/extra keys, encoding errors, forbidden number forms,
oversize input, signed writer boundaries, packet fields, exclusive output, and
injected partial-write cleanup.

The test harness must avoid shell injection and quote temporary paths safely.
All temporary input, output, and diagnostic files must live in the existing
build directory and be removed on successful completion.

## 4. Execution allocation proposed for separate authorization

- One test-only amendment pass; no production-source edits.
- One focused verification attempt.
- Maximum 60 seconds per command and 180 seconds cumulative command time.
- No automatic retries, timeout extensions, rebuild of `spu-sim`, or full
  repository gate.
- Stop on the first baseline mismatch, test failure, timeout, or evidence
  discrepancy. Preserve the result and request renewed authorization before
  any correction or rerun.

The executable hash must be identical before and after R2. Build only the
existing `spu_sim_t1d_scene_tests` target so the test binary incorporates the
amendment while production simulator code remains untouched.

## 5. Proposed commands after authorization

Run from the `spu-sim` repository root, with `timeout 60s` on each command and
within the 180-second cumulative limit:

```bash
git rev-parse HEAD
sha256sum build/sim-g2a/spu-sim tests/test_t1d_scene.cpp
cmake --build build/sim-g2a --target spu_sim_t1d_scene_tests --parallel 2
ctest --test-dir build/sim-g2a -R '^sim_t1d_scene_conformance$' --output-on-failure
sha256sum build/sim-g2a/spu-sim tests/test_t1d_scene.cpp
git diff --check -- tests/test_t1d_scene.cpp
```

The implementer must capture the test-only diff and its SHA-256 before running
the build. The final evidence must include command/status/time records, test
output, before/after executable hashes, amended test-source hash, base commit,
and worktree status. Verify the production executable hash equals the frozen
value both before and after the campaign.

## 6. Acceptance and disposition

R2 passes only when every required matrix case rejects with its specified
diagnostic, CLI failures have nonzero status and preserve output-file
conditions, the focused test passes, and production source/executable
identities remain unchanged.

A pass closes only the parser rejection coverage hold. The final SIM-G2A
aggregate record must continue to cite the original halted campaign failure,
SIM-G2A-R1, the prior 4/4 CTest result, all packet/frame hashes, and R2 as
separate evidence. Do not rewrite the earlier failure as success.

This contract authorizes review and preparation only. Test-source editing,
build, test execution, and any qualification decision require separate owner
authorization of the bounded R2 allocation.
