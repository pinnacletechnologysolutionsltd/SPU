# Newcomer publication set and clean-clone rerun

Date: 2026-10-07. Status: **local clean-clone usability qualification PASS**
for the frozen proposal. No remote publication or merge is performed.
Publication, archive qualification and pruning remain HELD.

## Completed proposal qualification

The clean-clone rerun completed in 58 seconds with exactly one terminal marker,
`COMPLETE`. Review of all **26 individual command results**, raw expected
outputs, source identity and final cleanliness establishes the local usability
result; it is not inferred merely from the collection marker or exit code.

* VM checks passed with 89 checks; the twelve-step Fibonacci program passed.
* Exact six-joint robotics matched the maintained reference and closed exactly.
  Its focused test passed 162 pair and 45 chain comparisons.
* Baseline, edited-fixture and saved-edit GPU previews and inspection passed.
  S1 passed six tests; S3 passed five. **Icarus was available**: S2 ran and
  passed its RTL parity checks, including seven depth-setup vectors. It was
  not skipped. On a machine without Icarus, report S2 RTL verification as
  untested separately from preview usability.
* The 23 proposal files and 23 existing dependency hashes match the freeze;
  all 28 recorded artifact hashes match. HEAD matches the proposed commit,
  and initial, final and reviewed Git status are clean.

Independent-review artifacts:

* [Publication patch](../build/newcomer_publication_20261007/freeze_01/publication.patch)
* [File/dependency manifest](../build/newcomer_publication_20261007/freeze_01/publication_manifest.json)
* [Frozen runner](../build/newcomer_publication_20261007/freeze_01/run_quickstart.py)
* [Frozen budget and artifact hashes](../build/newcomer_publication_20261007/freeze_01/plan.json)
* [Individual command results](../build/newcomer_publication_20261007/quickstart_01/quickstart_results.json)
* [Result review and raw-log hashes](../build/newcomer_publication_20261007/quickstart_01/review_01.json)

The result establishes **local clean-clone usability only**. Remote checkout,
installed packaging, full repository regression and hardware qualification
remain untested. The proposal is ready for an owner publication decision;
archive pruning is an independent held workstream, not a publication gate.

## Completed walkthrough interpretation

The previous walkthrough has exactly one terminal marker, `COMPLETE`, with
exit 0 and duration 22 seconds. Its collection exit does not mean every command
passed. At committed revision `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`,
the VM checks and Fibonacci command passed. Four other commands failed because
the robotics entry point or GPU package was absent: **PUBLICATION_GAP**.
The frozen working overlay passed all six commands using the standard library.
It was dirty, so that success did not qualify a clean published tree.

## Proposed file set

A new independent local proposal repository contains commit
`2a1fcda43070df975d0a6f8dfa1b59cdc99247c5`, based on the same committed
revision. The main repository's dirty work and historical evidence are intact.
The complete 23-file list, per-file hashes and existing dependency hashes are in
[publication_manifest.json](../build/newcomer_publication_20261007/freeze_01/publication_manifest.json).
The reviewable [publication patch](../build/newcomer_publication_20261007/freeze_01/publication.patch)
contains only this proposal.

| Publication group | Included files |
|---|---|
| Robotics runtime | `tools/rational_robotics_unshared_demo.py`, `software/lib/rational_robotics_unshared.py` |
| GPU runtime | Twelve `.py` files in `software/spu_gpu_eval/`: package initializer, CLI, scene, packet, reference, preview, device arithmetic/packet/loader/model/preview/inspect |
| Editable scenes | `examples/gpu/t1d_two_triangle.json`, `examples/gpu/t1d_two_triangle_vertex_b.json` |
| Focused tests | `test_rational_robotics_unshared.py`, `test_gpu_scene_compiler_s1.py`, `test_gpu_device_model_s2.py`, `test_gpu_pixel_inspect_s3.py` under `software/tests/` |
| Entry/navigation | Two-line quickstart link in the committed `README.md`; `docs/NEWCOMER_SOFTWARE_QUICKSTART.md`; `docs/gpu_scene_preview.md` |

The README is based on committed content, with a focused navigation addition;
the broad dirty README is not imported. The GPU guide links the included
quickstart instead of requiring an unpublished roadmap. One trailing blank
line was removed from the package initializer to pass the scoped whitespace
gate. Runtime arithmetic and model source otherwise match the working files.
No RTL, hardware tools, CPU extension, campaign evidence, archive helper,
installed console script or ISA change is included.

## Dependency and source review

Imports use only the Python standard library and the included/committed local
modules. The maintained `software/lib/rational_robotics.py` reference remains
the committed version. Twenty-three existing dependency files are separately
hashed: the reference, licenses, T1d reference/wire fixtures, reciprocal ROM,
and selected RTL provenance sources. The RTL files are read or hashed for
provenance, not synthesized. Dirty hardware versions are not overlaid.

Runtime prerequisites are Git, Python 3.10+, and Python's `venv` support for
the isolated walkthrough. A PPM-capable viewer is optional. No pip installation
or third-party package is needed for these source-checkout commands. The
installed toolkit's `pyserial` dependency and console entry points remain
outside this qualification. S2's optional verification gate additionally needs
Icarus Verilog (`iverilog`, `vvp`); that is a test prerequisite, not a preview
runtime prerequisite. Hardware build/synthesis tools are not required.

Existing license files remain: software MIT, documentation CC0, and the root
Apache license for files without a narrower applicable license. This review
changes no licensing terms or notices. Sources parse successfully; the scoped
staged whitespace check and new-document links pass inside the proposed tree.
The completed clean-clone evidence above supplies the scoped functional
qualification; it is not inferred from parsing, link or whitespace checks.

## Frozen rerun procedure (completed; do not relaunch)

The owner requested a new clean-clone rerun. Freeze this distinct qualification
to one attempt, a 1,200-second timeout, and 1,200 seconds cumulative budget,
matching the preceding walkthrough's limit. Do not reuse or extend the earlier
consumed attempt. Do not retry this attempt without renewed authorization.

```bash
tools/run_detached_job.sh --output build/newcomer_publication_20261007/quickstart_01 --timeout 1200 --notify-desktop -- python3 build/newcomer_publication_20261007/freeze_01/run_quickstart.py build/newcomer_publication_20261007/quickstart_01
```

The script clones the **committed proposal** with `--no-local`; no working
overlay is applied. It verifies HEAD, complete file presence and hashes, and
clean Git status, then creates an isolated environment below ignored `build/`.
User site packages and inherited Python search paths are disabled. It records
each command, exit code, stdout/stderr and duration, and runs VM, Fibonacci,
exact robotics, baseline/edited/saved-edit GPU previews and inspection, plus
the four focused tests and documentation/whitespace checks. Packet parity,
inspection decisions, artifact hashes, source cleanliness, and software-only
manifest markers are checked separately.

Failure categories remain explicit: missing declared files is a publication
gap; unavailable executables/venv is an environment failure; wrong results,
assertions or failed commands after complete source verification are functional
failures; incorrect source hashes/HEAD/initial cleanliness are source-identity
failures. Missing S2 compilers are reported separately without blocking demo
collection. A failed qualification command or validation makes the job exit
nonzero; collection completion alone is not a pass.

After launch, end the agent turn. A later invocation may inspect only after
exactly one of `COMPLETE`, `FAILED`, or `TIMEOUT` exists. Review individual rows
in `quickstart_results.json` and raw logs; never infer success from launch,
elapsed time or documentation audit exit 0. The repository-wide audit retains
known corpus findings and is not itself a clean-publication gate.

This is local clean-clone usability qualification. Anonymous remote checkout,
editable installation, full repository regression, hardware correctness,
physical timing and energy remain untested. Passing this rerun authorizes no
push, merge, archive qualification upgrade, or production pruning.
