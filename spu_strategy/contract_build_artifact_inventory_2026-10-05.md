# Engineering Contract: Read-Only Build Artifact Inventory

- **Date:** 2026-10-05
- **Contract ID:** `contract_build_artifact_inventory_2026-10-05.md`
- **Status:** COMPLETE
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Codex after §0 review
- **Integration Auditor:** inventory report inspection and repository gates

## 0. Pre-execution review

Run from the repository root:

```bash
git status --short
sed -n '88,118p' docs/REPOSITORY_MAP.md
sed -n '1,125p' docs/DETACHED_JOB_RUNNER.md
rg --files tools | rg '(audit|inventory|manifest)'
```

Preserve every existing modified, deleted, and untracked path. Halt if the
repository map no longer requires inventory before disposition, if an existing
inventory tool covers this scope, or if the output path below exists.

**Review result:** the map requires inventory followed by manual classification
and recorded disposition; no build inventory tool exists. The working tree has
concurrent GPU, hardware, documentation, and evidence changes. This contract
reads `build/` metadata and writes only a new report directory. No conflict was
found; preserve all existing paths.

## 1. Objective and scoped files

Create one standard-library Python utility that inventories `build/` without
reading file contents or changing existing paths. Its output is a machine-
readable review artifact, not a cleanup authorization.

Modify only:

```text
tools/build_artifact_inventory.py
software/tests/test_build_artifact_inventory.py
spu_strategy/contract_build_artifact_inventory_2026-10-05.md
AGENTS.md
```

Write the generated report only to this new directory:

```text
build/repository_cleanup/build_inventory_20261005_02/
```

Do not move, rename, truncate, overwrite, or delete any existing file or
directory. Do not edit `.gitignore`, repository maps, evidence ledgers, source
snapshots, or prior cleanup reports.

## 2. Inventory fields and interpretation

The utility shall record the scan timestamp, root, total apparent bytes, file
and directory counts, symlinks, top-level directory sizes/counts, file
extensions, largest regular files, `.git` metadata entries, checkout/worktree
directory names, `result.json` files, and `COMPLETE`/`FAILED`/`TIMEOUT` marker
counts. It shall report the total number of same-name/size candidate groups
and whether the displayed list was truncated.

It may list repeated `(basename, apparent size)` groups as review candidates.
It shall not hash file contents, infer that files are duplicates, decide that
data is disposable, or recommend deletion. The report shall state that human
review of contracts, evidence references, active worktrees, and generators is
required before any disposition.

The scan shall include hidden paths, not follow symlinks, and fail without
writing output if traversal encounters an I/O error. It shall refuse an
existing output directory and restrict output to a new child of
`build/repository_cleanup/`.

## 3. Implementation and execution commands

1. Add `tools/build_artifact_inventory.py` as a single-purpose module of 50–150
   lines using only the Python standard library.
2. Implement `--root` and `--out` arguments. Write sorted JSON to
   `<out>/inventory.json` only after a complete scan.
3. Add focused fixture tests for hidden paths, symlink handling, exact counts
   and repeated-name/size candidates, successful fresh output, and refusal to
   overwrite an existing output directory.
4. Run the exact commands:

```bash
python3 tools/build_artifact_inventory.py --help
test ! -e build/repository_cleanup/build_inventory_20261005_02
python3 tools/build_artifact_inventory.py --root build --out build/repository_cleanup/build_inventory_20261005_02
```

5. Parse the generated JSON and summarize its totals without printing the full
   report:

```bash
python3 -c 'import json; from pathlib import Path; p=Path("build/repository_cleanup/build_inventory_20261005_02/inventory.json"); d=json.loads(p.read_text()); print(json.dumps({k:d[k] for k in ("root", "apparent_bytes", "regular_file_count", "directory_count", "symlink_count", "scan_errors")}, sort_keys=True))'
```

## 4. Verification gates

Run:

```bash
git diff --check -- AGENTS.md tools/build_artifact_inventory.py software/tests/test_build_artifact_inventory.py spu_strategy/contract_build_artifact_inventory_2026-10-05.md
python3 software/tests/test_build_artifact_inventory.py
python3 tools/build_artifact_inventory.py --help
```

This module reads filesystem metadata and changes no RTL, arithmetic kernel,
hardware build flow, or shared regression runner. Per root `AGENTS.md` §4.1,
the focused inventory fixtures and diff checks are the applicable gates; the
full trace/math suite and Artix-7 synthesis are reserved for changes to those
systems.

## 5. Completion record

- Inventory: `build/repository_cleanup/build_inventory_20261005_02/inventory.json`
- Snapshot: 16,448,570,906 apparent bytes; 47,398 regular files; 10,038
  directories; 22 symlinks; no traversal errors.
- Focused fixture tests: 2 passed. CLI help: passed. Scoped whitespace checks:
  passed.
- Prior broad gates: repository verifier 238 passed / 0 failed; required ROTC,
  IROTC, math/oracle, and Padé tests passed; Artix-7 synthesis result was
  `COMPLETE`, exit 0, under unit
  `spu-a7_pade_01-20261005T043720Z-166824`.
- No build files were moved or deleted. This inventory is preparation for
  contract/evidence-aware manual classification, not a cleanup disposition.

## 6. Stop conditions

- Stop before output creation if the output path exists or escapes the stated
  `build/repository_cleanup/` parent.
- Stop without a partial report on traversal or serialization error.
- Stop if any implementation step would mutate an existing build artifact.
- Do not use this inventory to authorize cleanup. Each future disposition
  requires manual contract/citation review and a separate owner-approved scope.
