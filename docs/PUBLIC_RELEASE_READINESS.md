# Public release readiness (PUBLIC-1)

Dated 2026-10-20. This record covers the newcomer-facing entry points only: the
[README](../README.md), the [capability matrix](CAPABILITY_MATRIX.md), the [documentation index](index.md) and the
[contributor guide](../CONTRIBUTING.md#ways-to-help). It publishes nothing and changes no RTL, firmware, board file,
simulator behavior, ISA or mathematical contract.

## What was validated

All commands ran from a **snapshot of the working tree** (tracked plus untracked, non-ignored files) committed into
a throwaway repository, with no `build/` directory, Python 3.14.8 on Linux, stdlib only, one process, 1 GiB address-space
limit, 60 s wall limit (120 s for the longest experiment).

| Check | Result |
|---|---|
| README first run: `spu_vm_test.py` | `88 passed, 0 failed`, `PASS` in the snapshot; `89 passed` at committed `HEAD` `963a685`. The difference is uncommitted VM work by another session; the docs say "N passed, 0 failed" |
| README first run: `device-preview` (new `--out`, no pre-existing `build/`) | exit 0; writes `scene_packet.bin`, `ideal_preview.ppm`, `device_preview.ppm`, `pixel_comparison.json`, `manifest.json`; full-frame ideal/model agreement 307,200 of 307,200 pixels; `device_preview.ppm` SHA-256 `6d1ae81a7e678f19754d8cd0f5fd5e54131337d24b8bfddd35870eb8fab35cc5`, `scene_packet.bin` `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee`; reruns are identical |
| README first run: `inspect --x 320 --y 0` | triangle 0 wins in both paths, RGB `[15, 0, 0]`, ideal depth 2000, modeled depth 1999 |
| [Software quickstart](NEWCOMER_SOFTWARE_QUICKSTART.md), all 11 commands in a fresh `venv` | all exit 0: VM, Fibonacci (`PC=12 steps=12 snap_failures=0 [PASS]`), robotics (`PASS: fused six-joint chain matches reference and closes exactly`), ideal/device preview, inspect, edited scene (background at (100,200), triangle 1 at (300,200)) |
| Experiment commands named in the docs | `phy_r1` 5+7, `phy_r2` 7, `phy_r3` 8, `rel1` 8, `geo_i1` 8 (27 s), `hex_c1` 9, `ngw_h1` 7 test groups PASS; `som_rp0` builds with `-Wall -Wextra -Werror` and matches the oracle on 1,489 cases |
| Internal links in the files this tranche edited | all resolve, including anchors; two links to this page resolved after it was added |
| `tools/doc_audit.py --actual-pass 238` | runs; reports repository-wide findings (links into untracked material, orphans, uncited-claim candidates) that pre-date this tranche; see blockers |
| Whole-docs link audit (179 pages) | 131 broken links: 116 point into the gitignored `build/` evidence tree, 6 to the unpublished sibling `spu-sim`, 3 anchors, 2 missing research logs, 2 via the `docs/knowledge` symlink deleted in the working tree |

Not run: full `run_all_tests.py` regression, FPGA synthesis or P&R, any board, installed-package (`pip install -e .`) flow,
the SIM-1 C++ flow, a non-Linux platform.

## Publication blockers

None of these was resolved or worked around; permissions were not assumed.

**Licensing**
1. **Contributor terms conflict.** `CONTRIBUTING.md` says every contribution is licensed under Apache-2.0, while `LICENSING.md` assigns
   CERN-OHL-W-2.0 to `hardware/`, MIT to `software/`, CC0 to `docs/` and `knowledge/`, and Apache-2.0 to root files and `tools/`. The owner must
   decide which governs contributions, then align the two files. This tranche left both licensing texts unchanged.
2. **`research/` has no license.** The new experiment directories (346 untracked files under `research/`) are not mentioned in the license map and have no notice;
   `spu_strategy/` is in the same position. A scope entry or per-directory license file is needed before they are published.
3. **Third-party reference material.** `Quadray-Rotors-v5.pdf` and `Synergetics-Cookbook.pdf` sit in the repository root, are gitignored, and must stay out of any
   release; their redistribution terms are not recorded here. One reading-map document describes the cookbook. Two untracked photographs (`IMG_1839.jpeg`, `IMG_1842.jpeg`) are in the root; they
   need an owner decision on rights and privacy before any commit.

**Publication state**
4. **The newcomer software is not on the default branch.** `master` lacks `software/spu_gpu_eval`, the robotics demo and the quickstart; they exist only on the public review
   branch `codex/newcomer-software-20261008` (commit `2a1fcda`), whose draft PR could not be created for lack of collaborator rights. The README's first-run commands fail
   on a clone of the current default branch.
5. **Large uncommitted state.** At writing: 71 modified tracked files and about 1,450 untracked files, including every `research/` experiment, most of the newest docs and the
   changed VM. Local `master` (`963a685`) and remote `master` (`ff0fb05`) differ, with the relationship unverified without a fetch. Nothing was staged, committed or pushed here.
6. **Concurrent in-flight changes.** `software/spu_vm.py` and its test carry another session's uncommitted edits (the 88 versus 89 count), and `docs/knowledge` (a tracked symlink) is
   deleted in the working tree. Both must be settled by their owner before a release commit.
7. **Unpublished sibling simulator.** The guided tour, supported-demonstrations page and project status link to `../../spu-sim` (SIM-1), which has no remote and 18 uncommitted changes.
   Those pages cannot be followed by an outsider.
8. **Evidence links into `build/`.** 116 links in existing pages target the gitignored `build/` tree. Either publish a curated evidence archive (the 2026-10-14 package is a start) or rewrite
   those links. Separately, the MkDocs site serves only `docs/`: links from pages to `../research/` and `../knowledge/` (outside `docs_dir`) will not resolve there until a site build is designed (out of scope here).
9. **Dated status pages.** `START_HERE.md` and `PROJECT_STATUS_2026-10-17.md` carry 15 and 17 October statuses. They are accurate for their dates and are labelled as such; refresh before announcing.

## Recommended release sequence

1. Owner decides the contributor-license question (blocker 1) and the `research/`/`spu_strategy/` scope (blocker 2); keep the PDFs and photographs out.
2. The owner of the VM and `docs/knowledge` changes settles them; commit them separately.
3. Commit the newcomer software set (GPU evaluation, robotics demo, quickstart) and this tranche's docs on a branch off the reconciled `master`.
4. Re-run the validation table above from a fresh anonymous clone of that branch (the frozen October runner does this for the older set), then fix any gap.
5. Commit `research/` experiments with their license decision; either publish an evidence archive or repoint the `build/` links; publish or de-link `spu-sim`.
6. Merge to the default branch, tag it, and only then announce. Keep the limitations in the README in any announcement.
