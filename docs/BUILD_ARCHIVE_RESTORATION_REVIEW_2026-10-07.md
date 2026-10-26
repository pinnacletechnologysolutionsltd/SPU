# Build archive restoration review: HALT before production qualification

Date: 2026-10-07. Production pruning remains held. This review changes no
archive, source checkout, registered worktree, or external helper. The supplied
seven-step procedure and its current verifier do not meet the stated broader
restoration acceptance criterion.

## Verified failures of the current acceptance gate

The reviewed source is
`/home/user/.gemini/antigravity/brain/fc32ee9d-1132-44fe-80f4-305dcdc58deb/scratch/archive_qualification/verify_restore.py`.
Its exact SHA-256, stdout/stderr, and six isolated synthetic outcomes are in
[`negative_controls_01/results.json`](../build/archive_restoration_review_20261007/negative_controls_01/results.json).
These controls run the supplied script on disposable `/tmp` fixtures, retaining
the production source unchanged. No archival or hardware campaign was launched.

| Control | Observed verifier result | Acceptance defect and minimal correction |
|---|---|---|
| Intact regular file | Exit 0 | Positive control |
| Undeclared empty directory | Exit 0 | `actual_dirs` and `declared_dirs` are collected but never reconciled; require equal sets |
| Undeclared symlink | Exit 0 | Only declared links are checked; require equal link path sets before relocation |
| Missing declared empty directory | Exit 0 | Require directory set equality, including empty directories |
| Broken `.git` pointer with expected HEAD | Exit 0, Git error downgraded to warning | Require declared pointer presence/type, recovered gitdir/common-dir identities, and successful HEAD/status commands; fail closed |
| Absolute internal link relocation | Exit 0, rewritten target ends with newline and does not resolve | Strip the record terminator before parsing; preserve actual target characters with an unambiguous manifest format |

The retained historical fixture log does record ten matching dirty-status
items and passing hash/symlink/extra-file negative controls. Those specific
results do not cover the failures above. The clean real-candidate trial cannot
qualify restoration of dirty worktrees or unreachable detached commits.

## Additional blocking defects found by source inspection

* Dirty-state validation accepts any nonempty intersection of status lines.
  Losing nine of ten dirty entries would pass. Clean expected status skips
  comparison entirely. Require exact status parity, using NUL-delimited output
  and preserving leading status spaces; check successful execution in all cases.
* Relocation unlinks and recreates a link, so it is not atomic. It also rewrites
  a tampered existing target before checking it. Check original raw link parity
  first, then use a sibling temporary symlink and atomic replacement; compare
  against the declared relocation after the replacement.
* The original-source leak audit runs only without relocation and prints rather
  than fails. Run a post-relocation audit and reject forbidden residual source
  dependencies; classify external/escaping dependencies explicitly.
* Git pointers are exempted from file equality but their presence and restored
  administrative destination are not actually checked. A Git manifest with
  missing `.git` can skip all Git checks. Require every declared pointer and
  all required Git metadata, including common object-store accessibility.
* The tar selection subprocess lacks `check=True`; stdout and stderr are merged
  and parsed as names. GNU tar verbose names may quote/escape whitespace and
  control characters. A text-line parser does not guarantee selection parity.
  Fail on tar error, keep diagnostics separate, and use a proven archive-member
  representation or explicitly reject unsupported names before packaging.
* `git bundle create --all` does not explicitly include detached HEAD. Require
  HEAD in the bundle and verify object availability after independent restoration;
  also cover index-referenced objects not reachable from bundled commits.
* Step 2 assumes the `.git` pointer is absolute. Resolve a relative gitdir
  against its worktree; use Git's resolved administrative paths. Validate that
  the standalone case is self-contained when alternates/shared object stores
  exist, rather than assuming a copied `.git` is sufficient.
* `fuser -v <directory>` alone does not establish recursive quiescence or protect
  against a writer starting later. Establish an owner-controlled stopped-source
  or filesystem-snapshot boundary, then inventory and archive that same state.

## Required qualification extension

Retain current trial evidence and label it with its actual scope. Repair and
hash the verifier and fixture runner before any new qualification. Require
negative controls for each failure above, dirty index/worktree differences,
untracked/ignored retained data, a clean status becoming dirty, relative Git
pointers, detached unreachable HEAD, extra/missing directories and links, and
tampering of the original absolute internal link. Check modes if inventory modes
are part of declared parity. Reject unsupported special files and ambiguous
names rather than silently hashing or parsing them as regular files.

Do not execute Steps 4–7 against production candidates on the strength of the
current verifier. Preserve FASM, synthesized/routed netlists, constraints,
tool/chipdb identities, evidence waveforms, and explicitly declared dirty state.
Any later production pruning still requires the owner's explicit authorization
after corrected independent extraction and durable-replica verification.
