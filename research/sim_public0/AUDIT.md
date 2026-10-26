# SIM-PUBLIC-0 independent audit and preservation (SIM-PUBLIC-0P)

2026-10-23. Audit by Claude (read-only on `spu-sim`); accepted by the owner as PASS within the tested scope. `README.md`, `quickstart.sh`, `check_clean_clone.py`, `environment.txt`, `local_01/` and `local_02/` are preserved unaltered; this file and `audit_rerun/` are additions.

## Verified at preservation time
- spu-sim HEAD `c1e0676eee5d2398b8d90eec43bd55b2d2f6b924`, 0 dirty lines, no remote; the pinned commit is the one checked out in `local_02/step_1.log` and asserted by `quickstart.sh`.
- `local_01`: failed harness attempt (bwrap cannot create `/work` on a read-only root), exit 1 at step 3, before any simulator step; kept as evidence.
- `local_02`: 3/3 steps exit 0, 13.76 s, `pass: true`; render 921,600 bytes, `sha256sum -c` OK for `96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10` (the frozen T1d frame hash, same as SIM-XCON-1P); source tree clean after the build.
- `audit_rerun/`: one independent rerun of the documented harness command (output path new, `ulimit -v 2097152`, `timeout 60s`): 3/3 exit 0, 14.67 s, same frame hash, clean tree after. spu-sim still clean afterwards. This was part of the audit, not a preservation-stage run; no simulator run happened in SIM-PUBLIC-0P.
- `quickstart.sh` SHA-256 `7b7feb07eda2f72c8cdb10efba4e211ca0efa9633dfe03b80e03dba2958f7849`.

## Clarification
`quickstart.sh` is the fully tested workflow. The command block in `README.md` is illustrative: it omits the script's pinned-HEAD check and its clean-tree checks before and after the build. Do not describe the README block as the tested artifact.

## Limits (unchanged)
Local clone only (`git clone --no-local` of a local path); shared host OS, kernel and toolchain (GCC 16.2.1, CMake 4.4.4, Make 4.4.1), not a fresh image or VM; host `/usr`, `/etc`, `/sys` visible in the sandbox; `ulimit -v` is per process, not an aggregate cap. Not measured: public clone (no remote or URL exists), other OSes/compilers/machines, install and download time, an unfamiliar developer's timed walkthrough (the under-15-minute milestone is not established). The `doc_audit.py` counts in README were not re-verified. Render smoke test only: no conformance claim, SIM-G3 INCOMPLETE, no full-frame RTL equivalence, no FPGA execution. Nothing published, tagged or pushed.
