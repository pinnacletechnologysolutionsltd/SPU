# SIM-PUBLIC-0: clean-clone T1d workflow

2026-10-23. **Local packaging PASS; external reproducibility pending.**
Source: `spu-sim` `c1e0676eee5d2398b8d90eec43bd55b2d2f6b924`.
The original checkout remains clean and unchanged. No simulator functionality,
qualification evidence, or SIM-G3 status was changed.

## Shortest tested workflow

Requirements for this Linux recipe: Git, CMake 3.16+, a C++17 compiler and
standard library, a CMake build tool (Make in this test), a POSIX shell and
coreutils (`wc`, `sha256sum`). Start in a fresh checkout's root directory.
No Python, Vivado, FPGA board, or research-repository checkout is needed by
these user commands. Python and Bubblewrap belong only to the local test harness.

```sh
git checkout --detach c1e0676eee5d2398b8d90eec43bd55b2d2f6b924
cmake -S . -B build/public0 -DCMAKE_BUILD_TYPE=Release
cmake --build build/public0 --parallel 2 --target spu-sim
build/public0/spu-sim gpu render fixtures/gpu_t1d_scene_wire_64b.bin --output build/public0/t1d.rgb8
test "$(wc -c < build/public0/t1d.rgb8)" -eq 921600
printf '%s\n' '96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10  build/public0/t1d.rgb8' | sha256sum -c -
```

Success prints `build/public0/t1d.rgb8: OK`. The file is raw 640 x 480 RGB8,
three bytes per pixel, not a PNG. Run from the checkout root so the packaged
default reciprocal ROM resolves. Use a fresh build directory for reproduction.
This builds only the executable needed to render; the existing README also
documents the broader `validate_release` conformance workflow.

The public `git clone` command is deliberately pending: the inspected local
repository has no configured remote, and no public URL has been supplied.
Do not distribute a guessed URL or describe the public download as tested.

## Local test and result

Exact harness command, from the SPU research repository root:

```sh
ulimit -v 2097152
timeout 60s python3 research/sim_public0/check_clean_clone.py /home/john/Projects/hardware/spu-sim research/sim_public0/local_02
```

The output path is exclusive; choose a new path for any authorized later check.
The test used a `git clone --no-local --no-checkout`, then detached the pinned
revision. No hardlinks or alternates to the original repository were needed.
Inside Bubblewrap, `/home`, `/opt`, `/tmp`, and `/run` were hidden, except the
independent temporary clone and the read-only workflow script. A new device
namespace exposed no FPGA board. Network namespaces disabled networking and
the environment contained only PATH, HOME and LC_ALL. The host OS and system
toolchain were shared; this was not a fresh distribution image or VM.

`local_02/result.json` reports PASS, **13.760 seconds** including local clone,
checkout, configuration, two-worker Release build, render, size check and
strict hash check. `local_02/step_2.log` records the executed quickstart and
compiler/build output. The run had a 60-second external wall limit, 55-second
subprocess limits and a 2 GiB address-space limit per process (not an aggregate
memory cap). Host/tool versions are in `environment.txt`.

`local_01` preserves an initial harness failure: Bubblewrap could not create
`/work` under a read-only root. Moving test mounts under the private `/tmp`
fixed the harness. That attempt never configured or ran the simulator.

## Documentation and packaging gaps

The existing README already supplies the build/render commands, full expected
hash and hardware-free requirements. No missing runtime fixture or simulator
feature was found. The useful documentation changes are small:

1. Supply a public clone URL and the full pinned commit.
2. Put the minimal T1d path before the scalar and optional scene-encoding tour.
3. Use a failing hash check, rather than asking readers to compare printed hashes.
4. Name Git/build-tool/coreutils requirements for this recipe, the required
   working directory, and the raw framebuffer format.

This note and `quickstart.sh` provide reviewable text without changing the
frozen source baseline. Publishing or choosing repository hosting is pending
owner input. A public fetch check and a timed unfamiliar-developer run are still
needed to establish the stated external under-15-minute milestone. Installation
time, download latency, other operating systems, older compilers and other
machines were not measured. No new full conformance claim follows from this
render smoke test.

Documentation checks: `python3 tools/doc_audit.py --actual-pass 238` exited 0
and reported existing tracked-tree findings (14 broken links, 30 uncited
claims, one stale suite total, 166 orphaned docs, one superseded-status hit).
It scans tracked Markdown, so it does not certify this new untracked note.
`git diff --check -- research/sim_public0` and explicit new-file whitespace
checks found no whitespace errors. No production/shared code changed; unrelated
RTL, arithmetic and synthesis gates were not run.

SIM-XCON-1P remains CLOSED / PASS, with its durable evidence in SPU commit
`159d18432711c315d9610b2044a19c68a88a2830`. Its bounds remain C++/Python
full-frame agreement and RTL selected-pixel colour 29/29; full-frame RTL
equivalence is not established and FPGA execution of that comparison was not
tested. SIM-G3 remains INCOMPLETE. This tranche reran none of those comparisons.
