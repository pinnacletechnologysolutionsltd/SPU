# SIM-CAP1 integration follow-through — 2026-10-25

Status: targeted functional checks PASS; ISA clarification added;
commit/release integration remains pending. Original frozen contract and
amendment unchanged. No QROT/rotate(), RTL, baseline or tracked-binary edits.

## Change made

Added SIM-CAP1 v1 clarification below the Geometry Output table in
`knowledge/isa_reference.md`. Preserved the original SPREAD row, quoted it with
commit provenance `3524a9eb624d71ccd53c600d47919d29905e7ef4`, and documented
software's `SPREAD Rd,QRa,QRb`, destination pair, independent metric selection,
unreduced Gram result and refusal semantics. The historical row was checked
in that commit. No existing unrelated ISA edits were removed.

## Targeted verification

Evidence: `build/sim_cap1_integration_20261025/`. Source hashes and HEAD are in
`source_identity.json`; full dirty status is in `working_tree_status.txt`.
Tests check the shared working-tree sources, not an isolated committed SIM-CAP1
patch. The frozen contract limits this activity to targeted checks; no broad
regression or FPGA qualification was run and no commit is declared ready.

| Command | Result / log |
|---|---|
| `timeout 60 python3 software/tests/test_gram_v1_spread.py` | PASS, 124 checks; python_gram.log |
| `timeout 60 python3 software/tests/test_gram_v1_spread_cpp.py` | PASS, 4022 cases: 1253 OK, 2761 OVERFLOW, 8 DEGENERATE_METRIC; Pell, 5 legacy cases and proof; cpp_gram.log |
| `timeout 60 python3 software/spu_vm_test.py` | PASS, 88 checks; legacy_vm.log |
| `timeout 60 python3 software/cross_validate.py` | PASS, 5/5; legacy_cross.log |
| `timeout 60 g++ -std=c++17 -I software/common/include -o build/sim_cap1_integration_20261025/spu_quadray_test software/common/tests/spu_quadray_test.cpp` followed by that executable under `timeout 60` | PASS, including retained legacy spread checks; legacy_cpp.log |
| `timeout 60 g++ -std=c++17 -O2 -Wall -o build/sim_cap1_integration_20261025/spu_vm_current software/vm/spu_vm.cpp` | PASS; build.log |
| `python3 tools/doc_audit.py --actual-pass 238` | exit 0; doc_audit.log; does not establish a new regression count |
| `git diff --check -- knowledge/isa_reference.md research/sim_cap1_spread/INTEGRATION_REVIEW_2026-10-25.md` | PASS |

Both Gram test processes additionally inherited `ulimit -v 2097152` (2 GiB
address space). The C++ test compiles its own current-source driver and proof
VM; it does not validate the tracked executable.

## Hunk separation findings

| File/group | SIM-CAP1 portion | Shared work to exclude or explicitly resolve |
|---|---|---|
| spu_quadray.h | gram header include and spread_gram method (entire current diff) | Historical spread and rotate untouched |
| spu_gram_spread.h and four gram test/oracle/driver files | New Gram arithmetic and conformance files | New files need explicit inclusion in any eventual commit |
| spu_vm.py | metric constants/helpers, selection, SPREAD branch/proof, metric manifest detail | CPU profiles/manifest infrastructure, assembler validation, canonical control flow and general fault handling |
| spu_vm.cpp | gram include, enum/constructor selection, SPREAD branch/proof, CLI selector | Checked arithmetic, canonical control/operand repairs, shared faults, rounding and assembler changes |
| spu_vm_test.py | No SIM-CAP1 hunk identified | Existing COND rejection change belongs to canonical control-flow work |
| run_all_tests.py | Gram test invocation/count/report additions | CPU-profile and GPU accounting/registration changes |
| isa_reference.md | Newly added SIM-CAP1 clarification only | Existing surd extension and encoding/status edits |
| examples/02_quadray_orbit/quadray_orbit.sas | None | Preserve existing unrelated diff |
| software/vm/checked_math.h | Shared VmFault dependency used by Gram refusal | Untracked shared checked-arithmetic header; ownership unresolved |

This is a semantic hunk map, not proof of authorship. In particular, constructor,
manifest and fault changes share surrounding hunks with other work. Explicit
paths alone are insufficient for these mixed files: construct/review a selective
patch against the intended baseline and verify it in isolation before committing.
Do not stage whole mixed files, the orbit example or the tracked executable.

## Manifest and binary findings

C++ source has no capability-manifest emitter/CLI option. Its metric enum and
selection exist, but there is no C++ machine-readable metric_semantics manifest.
The simulator integration policy requires build-bound manifests for released
builds. Thus arithmetic tests passing does not establish C++ release readiness.
No manifest schema or build-identity implementation was invented in this pass.

Python emits metric_semantics and the amended top-level metric detail. The
legacy entry says `qualified: false` in its scope string, not a Boolean JSON
field. Consumers must not mistake that prose for a machine-readable qualification
flag. Conformance remains `not_run` in the static manifest; tests do not turn
that field into build-bound passing evidence automatically.

The tracked executable predates current VM source/header timestamps. It differs
byte-for-byte from the fresh build (both SHA-256 values preserved in evidence),
but compiler flags/build provenance are insufficient to infer exact functional
staleness from that difference. Both executables recognize metric selector
validation. No reproducible source identity is exposed by the tracked binary.
Leave it untouched and unstaged per amendment §8; the fresh binary lives only
under build/. Do not distribute the tracked binary as a verified current build.

A supplemental CLI Pell attempt is INVALID as a full-width fixture: LD encodes
narrow immediates, so the supplied int32 witness lanes were truncated before
SPREAD. Both executions rejected the different loaded vectors. Preserve
tracked_pell.log/rebuilt_pell.log as failed diagnostic design, not evidence
against Gram arithmetic or a binary equivalence check. The passing driver suite
seeds full int32 registers directly and remains the valid Pell evidence.

## Disposition

No staging or commit performed. Amendment §8 explicitly retains staging/commit
HOLD and says software/vm/spu_vm stays unstaged. A source-only selective commit
would be preferable to bundling shared edits or rebuilding the tracked binary,
but first resolve shared dependency ownership and test the actual selected patch.
C++ manifest/release identity remains a genuine reporting gap. No claim of
integration completion, hardware qualification or broad regression success follows.
