# SPU handoff: Arch reconciliation

**Purpose:** preserve and compare the Ubuntu and Arch work before choosing a
canonical development line. This handoff is a starting point, not permission
to merge, rewrite history, delete branches, reinstall a machine or publish
additional material.

## Ubuntu snapshot

* Public repository: https://github.com/pinnacletechnologysolutionsltd/SPU
* Public preservation branch: `archive/ubuntu-pre-arch-reconciliation`.
* Reviewed freeze commit: `510a2559df00f5e03fe7c92feaec26d6078aba6e`
  (57 reachable commits). The archive branch was subsequently advanced by a
  documentation-only commit containing this handoff. The public default was
  `master` when checked.
* Ubuntu local `dev/next` was at `510a255` before the handoff commit. Check
  current refs again before reconciliation; the archive is not an automatic
  mirror of later development.
* The annotated local tag `v0.2-h0-uart-silicon` points to
  `4d126fb17f7c2a34cd2f1123e65d75fe0a89496f`. The archive push did **not**
  publish the tag. Its classification is **EXPERIMENTAL / SILICON-DEMONSTRATED**,
  not production-qualified; see [hardware evidence §3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc).

The Ubuntu checkout was not clean. In particular, `docs/README.md` was modified;
`research/obs_0/`, `research/SYMBOLIC_REPRESENTATION_FOLLOWUPS.md`, the tag-message
file and many `spu_strategy/` files were untracked. They are **not** in the public
snapshot merely because they exist on disk. Inventory and preserve all tracked,
untracked and ignored work on both machines before any cleanup.

## Evidence outside Git

The local annotated tag records a tested bitstream and routed checkpoint by
SHA-256; neither binary is in Git. It also names the preservation bundle
`v0.2-h0-uart-silicon-2026-11-04` and a manifest hash. Locate the bundle and
verify the manifest against the tag; confirm an independently accessible
off-machine copy. The bundle's current location and backup integrity were not
verified while writing this handoff. The public source branch is not a backup
of untracked work, ignored build evidence, tool installations or that bundle.

## First steps on Arch

1. Record the Arch checkout's current branch, HEAD, remotes, worktrees, staged
   and unstaged changes, untracked and ignored material, tags and local branches.
   Do not reset or switch away from a dirty checkout. Preserve unique work and
   evidence in a verified backup before changing it.
2. Verify the public preservation ref independently:

   ```sh
   git ls-remote --heads https://github.com/pinnacletechnologysolutionsltd/SPU.git refs/heads/archive/ubuntu-pre-arch-reconciliation
   ```

   After obtaining the branch, verify that the reviewed freeze commit
   `510a2559df00f5e03fe7c92feaec26d6078aba6e` is its ancestor and inspect
   every subsequent commit. Stop if unexpected changes are present.
3. In a separate checkout or worktree, obtain the archive branch without
   overwriting existing refs, then compare histories and file contents with
   the Arch work and current public `master`. Check for common ancestry rather
   than assuming it; the public `master` and Ubuntu development history were
   reported to have unrelated histories. Identify unique commits, equivalent
   changes, conflicts and work that exists only outside Git.
4. Prepare a reconciliation plan and a reviewable proposed result on a
   separate branch. Preserve the archive ref and silicon evidence; retain
   negative results and qualification limits. Select tests appropriate to the
   actual changes and follow each repository's existing execution gates.
5. Report the comparison, backup locations and verification, proposed merge
   method, conflicts and test evidence before changing public `master`, its
   default-branch setting or deleting any branch.

## After reconciliation

Decide with the owner how the accepted development line should relate to
`master`, and which older branches can safely be retired. A fresh Ubuntu desktop
installation is a separate operation: first verify independent backups of both
machines and required evidence, then inventory and restore the required
toolchains and validate their versions and relevant builds. Do not infer a
production release or physical qualification from public visibility.
