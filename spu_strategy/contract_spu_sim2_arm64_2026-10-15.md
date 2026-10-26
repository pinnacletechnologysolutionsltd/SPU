# Engineering Contract: SPU-SIM-2 ARM64 Reproducibility

**Date:** 2026-10-15
**Contract ID:** `spu_sim2_arm64_2026-10-15`
**Status:** REVIEWED — TRANSFER IN PROGRESS; ARM64 execution HOLD
**Spec Author:** Codex
**Halt-and-Flag Implementer:** Owner-assigned ARM64 operator
**Integration Auditor:** Owner-assigned reviewer

## 1. Objective

Rebuild and execute the frozen SIM-1 source commit on the ROCK64 running
Armbian AArch64. Verify the existing newcomer build/run instructions on that
native ARM64 environment. Do not change the SIM-1 implementation or fixtures.

This is a software portability test on the ROCK64 host. It is not an FPGA,
accelerator, or peripheral qualification.

## 2. Frozen baseline and boundaries

Use this exact source commit:

```text
013acd4230442e0e126640604c11176f274962ab
```

The commit tree was independently compared with all 40 entries of the SIM-1
source manifest; every path and SHA-256 matched. The manifest is
`../spu-sim/build/release/sim1_source_manifest.json`, SHA-256
`74411bd87c51149e717ada9e64c8580d40dd1e6122eb1824289316dc2c92365c`.
The accepted profile is `spu13-soft-v1`; the immutable inputs are described by
`fixtures/manifest.json` at the frozen source commit.

Do not edit, regenerate, stage, commit, or tag files in `spu-sim`. A mismatch
requires HALT and a separate disposition; do not repair or rebaseline during
this study.

## 3. Source transfer and connection preflight

The exact source bundle was prepared and verified on the development PC:

| Transfer artifact | Identity |
|---|---|
| `/tmp/spu-sim-sim1.bundle` | 71,112 bytes; SHA-256 `460f8ab1c30ccc5c04ed348410e24ebe9e4dc66c3080d9ff95f57d55467dff36` |
| Bundle verification | `git bundle verify` passed; `master` and `HEAD` point to the frozen commit |

On the ROCK64, obtain the LAN address and confirm SSH service state:

```bash
hostname -I
systemctl is-active ssh
```

On the development PC, set `SIM2_ROCK64_USER` and `SIM2_ROCK64_IP` to the
confirmed account and address, verify the connection, and transfer the bundle:

```bash
ssh "${SIM2_ROCK64_USER}@${SIM2_ROCK64_IP}" 'uname -m && systemctl is-active ssh'
scp /tmp/spu-sim-sim1.bundle "${SIM2_ROCK64_USER}@${SIM2_ROCK64_IP}:~/spu-sim-sim1.bundle"
```

On the ROCK64, verify and check out the exact commit:

```bash
test ! -e "$HOME/spu-sim"
sha256sum "$HOME/spu-sim-sim1.bundle"
git bundle verify "$HOME/spu-sim-sim1.bundle"
git clone "$HOME/spu-sim-sim1.bundle" "$HOME/spu-sim"
git -C "$HOME/spu-sim" checkout --detach 013acd4230442e0e126640604c11176f274962ab
git -C "$HOME/spu-sim" rev-parse HEAD
git -C "$HOME/spu-sim" status --porcelain
sha256sum "$HOME/spu-sim/fixtures/manifest.json"
```

Do not proceed unless the commit and fixture-manifest hash match the frozen
values. Use another transfer method only under a separately reviewed amendment.

## 4. Preflight requirements

Before building, record and verify all of the following on the ROCK64:

1. `uname -m` returns `aarch64`.
2. `/etc/os-release`, compiler identity, and CMake identity are captured.
3. `git rev-parse HEAD` returns the frozen commit above.
4. `git status --porcelain` is empty before running commands.
5. The checked-out `fixtures/manifest.json` has SHA-256
   `dc26d3fed6577aa9b7b2cb41cdbe2346a6416be43e513e1224ec26b1f4828d4c`.
6. The evidence destination `build/sim2_rock64_20261015/` is absent.

HALT before test execution if any condition fails or the source transfer method
cannot provide the exact commit.

## 5. Newcomer and ARM64 command sequence

From the clean checkout root on the ROCK64, execute these commands in order:

```bash
uname -a
cat /etc/os-release
c++ --version
cmake --version
git rev-parse HEAD
git status --porcelain
sha256sum fixtures/manifest.json
cmake -S . -B build/release -DCMAKE_BUILD_TYPE=Release
cmake --build build/release --parallel
ctest --test-dir build/release --output-on-failure
build/release/spu-sim assemble examples/scalar_quadray.sas -o build/scalar_quadray.spusim
build/release/spu-sim run build/scalar_quadray.spusim --snapshot build/scalar_quadray.snapshot.json
cmp build/scalar_quadray.snapshot.json examples/scalar_quadray.expected.snapshot.json
build/release/spu-sim gpu render fixtures/gpu_t1d_scene_wire_64b.bin --output build/t1d.rgb8
wc -c build/t1d.rgb8
sha256sum build/t1d.rgb8
```

The test must use a native AArch64 compiler and executable. Do not cross-compile
on x86-64 for this gate. Preserve stdout, stderr, individual exit statuses,
source identity, and generated outputs under the evidence directory.

## 6. Acceptance criteria

All conditions are required:

- The preflight passes and the source revision remains clean.
- Release configuration and full build complete successfully.
- CTest passes all three registered tests, including the conformance suite and
  both always-active `SIM_CHECK` probes.
- The scalar/Quadray snapshot compares byte-for-byte equal to the frozen file.
- T1d output is exactly 921,600 bytes and has SHA-256
  `96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10`.
- Evidence contains the platform/tool identities, exact command order and
  results, source commit, fixture-manifest hash, snapshot comparison result,
  framebuffer size/hash, and one terminal disposition.

A pass establishes this SIM-1 workload on this ROCK64 AArch64 software
environment. It does not establish performance, cycle accuracy, FPGA
equivalence, broader ISA coverage, or portability to other ARM64 systems.

## 7. Execution budget and stop conditions

**Proposed allocation for owner authorization:** one attempt; 600 seconds per
attempt and cumulative; no retries. This is a proposed budget, not execution
authorization.

The attempt begins only after the frozen source has been checked out on the
ROCK64 and the preflight passes. A command failure, timeout, source mismatch,
fixture mismatch, output mismatch, missing evidence, or missing terminal result
consumes the attempt. Do not retry, extend the timeout, change sources, or
substitute another machine without renewed owner authorization.

No source edits, commits, public release, FPGA operations, or hardware
acceleration are included.
