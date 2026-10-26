# SIM-G1 — T1d interoperability reproducibility closeout

```bash
(cd build/gpu_evaluation/sim_g1_repro && sha256sum -c SHA256SUMS)
```

**Contract ID:** `sim_g1_repro_closeout_2026-10-17`

**Status:** BOUNDED REPLAY COMPLETE — PASS; see `build/gpu_evaluation/sim_g1_repro/run_02/replay_manifest.json`

**Objective:** Close the provenance gap for the already demonstrated Python/C++ T1d comparison by reconstructing the tested inputs from immutable source archives and replaying all three frozen scenes.

**Scope:** Software source provenance and bounded framebuffer comparison only.

## 1. Existing evidence and boundary

The standalone SIM-1 C++ package at commit
`013acd4230442e0e126640604c11176f274962ab` provides the bounded
`gpu.scene.t1d.two-triangle-v1` packet renderer. The archived comparison report
records byte-exact 921,600-byte frame matches against Python's finite-width
T1d device model for `identity`, `rotate_bcd`, and `reflect_bc`.

This tranche reproduces those results from reconstructed sources. It does not
implement a renderer, expand the T1d profile, establish ISA-driven GPU
execution, qualify cycle timing, or establish FPGA pixel equality. The Python
path remains the reference/device-model implementation; SIM-1 remains a
separate C++ software implementation.

## 2. Frozen source inputs

Use these exact identities; do not substitute the current working tree:

| Input | Identity / source |
|---|---|
| SPU base source | Git archive of commit `963a685004b96e275e7e58ebefac98c6e1321597`, SHA-256 `73776e7abc3eb2e0d3ef4cd3ce8b4940c21092a054bfc008d3dd4a89094e83e8`, 244,183,040 bytes |
| SPU experiment overlay | `gpu_w1_source_e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3.tar`, SHA-256 `e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3`; accompanying JSON manifest SHA-256 `c4d60c45e961c115cc6a0c823ebce52480c0797d3fbc7af112189701c8601df2` records per-file hashes and the base commit |
| SIM-1 source | Git archive of commit `013acd4230442e0e126640604c11176f274962ab`, SHA-256 `a643b5d55588aa43b58f9571f336b11823a12b80b53a22bcec8949beb48340b4`, 235,520 bytes |
| Scene fixtures | `examples/gpu/golden_core_tetra_views/{identity,rotate_bcd,reflect_bc}.json` in the SPU overlay; their hashes are recorded in its manifest |
| Existing comparison record | `build/gpu_evaluation/gc_tetra_20261017/sim1_cpp_frame_comparison.json`; preserve as historical evidence and compare its expected packet/frame hashes with replay |

The SIM-1 checkout currently has no configured remote. A verified source
archive is an acceptable retrieval mechanism. Record each artifact's SHA-256,
size, source commit, creation command, and included license files in
`source_manifest.json`. The SPU base archive plus overlay archive must
reconstruct the Python inputs without access to the original dirty working
tree. Existing preview code reads Git metadata, so the reconstruction procedure
creates a deterministic local provenance commit from the exact base archive
before applying the hash-pinned overlay. That synthetic commit is a replay
container; the manifest retains the original source commit identity.

The source archive exports were prepared with:

```bash
git archive --format=tar --prefix=spu-base/ 963a685004b96e275e7e58ebefac98c6e1321597 > build/gpu_evaluation/sim_g1_repro/spu_base_963a685.tar
git -C ../spu-sim archive --format=tar --prefix=spu-sim/ 013acd4230442e0e126640604c11176f274962ab > build/gpu_evaluation/sim_g1_repro/spu_sim_013acd4.tar
cp build/gpu_evaluation/gpu_w1c/source_snapshot_01/gpu_w1_source_e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3.tar build/gpu_evaluation/sim_g1_repro/
cp build/gpu_evaluation/gpu_w1c/source_snapshot_01/gpu_w1_source_e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3.json build/gpu_evaluation/sim_g1_repro/
cp build/gpu_evaluation/gc_tetra_20261017/sim1_cpp_frame_comparison.json build/gpu_evaluation/sim_g1_repro/historical_comparison.json
```

The frozen source exports in this package were created with:

```bash
git archive --format=tar --prefix=spu-base/ 963a685004b96e275e7e58ebefac98c6e1321597 > build/gpu_evaluation/sim_g1_repro/spu_base_963a685.tar
git -C ../spu-sim archive --format=tar --prefix=spu-sim/ 013acd4230442e0e126640604c11176f274962ab > build/gpu_evaluation/sim_g1_repro/spu_sim_013acd4.tar
cp build/gpu_evaluation/gpu_w1c/source_snapshot_01/gpu_w1_source_e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3.tar build/gpu_evaluation/sim_g1_repro/
cp build/gpu_evaluation/gpu_w1c/source_snapshot_01/gpu_w1_source_e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3.json build/gpu_evaluation/sim_g1_repro/
cp build/gpu_evaluation/gc_tetra_20261017/sim1_cpp_frame_comparison.json build/gpu_evaluation/sim_g1_repro/historical_comparison.json
```

The prepared source package is
[`build/gpu_evaluation/sim_g1_repro/source_manifest.json`](/home/user/Projects/hardware/SPU/build/gpu_evaluation/sim_g1_repro/source_manifest.json).
It records exact byte sizes, SHA-256 values, source commits, export commands,
license files, all three scene hashes, the 88-file overlay manifest identity,
and the prior comparison record. The adjacent `SHA256SUMS` covers each tar and
JSON artifact; all entries verified. The original W1 overlay was frozen from a
dirty workspace, so its per-file hashes, rather than an assumed clean Git
commit, pin its contents. Its original generation invocation was not retained;
the manifest identifies the generator, source commit, dirty status, exact
archive hash, and full file list.

The import/hash-only preflight was run from reconstructed sources. It resolved
`software.spu_gpu_eval.cli` inside the reconstructed SPU tree, matched all 88
overlay file hashes, and verified the reciprocal ROM hash. Python was 3.14.8.
The deterministic synthetic Git commit was
`62aa4f993b917618d7b128381d82d4b980e840c9`. Archive checks passed. No SIM-1
build, C++ render, or framebuffer replay was run. The replay manifest remains
separate and must include build tools, commands, import origin, synthetic
reconstruction commit, and result hashes.

## 3.1 External prerequisites

The replay uses a Linux x86-64 host, Git, GNU `tar`, `sha256sum`, `realpath`,
Python 3.10 or later with its standard library, a C++17 compiler, CMake 3.16 or
later, and the build tool selected by CMake (GNU Make for the default Unix
Makefiles generator). No network access, pyserial import, FPGA tools, or
third-party Python rendering package is required. The Python preflight must
report the interpreter version. The CMake compiler identification and version
must be recorded in the replay manifest.

## 3. Reproduction procedure

Run from a clean Linux checkout of the SPU repository with the three frozen
source archives and their reviewed SHA-256 manifest available locally. Store
all generated files below the new output directory shown here; refuse an
existing output directory.

```bash
set -e
RUN="$(pwd)/build/gpu_evaluation/sim_g1_repro/run_02"
test ! -e "$RUN"
mkdir -p "$RUN/source/spu" "$RUN/source/sim1" "$RUN/output"
(cd build/gpu_evaluation/sim_g1_repro && sha256sum -c SHA256SUMS)
tar -xf build/gpu_evaluation/sim_g1_repro/spu_base_963a685.tar -C "$RUN/source/spu"
git -C "$RUN/source/spu/spu-base" init
GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null git -C "$RUN/source/spu/spu-base" -c core.excludesFile=/dev/null add --force -A
GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_AUTHOR_NAME=SIM-G1 GIT_AUTHOR_EMAIL=sim-g1@example.invalid GIT_AUTHOR_DATE=2026-10-17T00:00:00Z GIT_COMMITTER_NAME=SIM-G1 GIT_COMMITTER_EMAIL=sim-g1@example.invalid GIT_COMMITTER_DATE=2026-10-17T00:00:00Z git -C "$RUN/source/spu/spu-base" -c user.name=SIM-G1 -c user.email=sim-g1@example.invalid -c commit.gpgsign=false commit --quiet -m "SIM-G1 reconstructed source base 963a685"
tar -xf build/gpu_evaluation/sim_g1_repro/gpu_w1_source_e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3.tar -C "$RUN/source/spu/spu-base"
tar -xf build/gpu_evaluation/sim_g1_repro/spu_sim_013acd4.tar -C "$RUN/source/sim1"
# The preview CLI requires outputs beneath the reconstructed tree's ROOT/build/gpu_evaluation.
# Redirect that scratch-only path into this replay's evidence directory.
mkdir -p "$RUN/source/spu/spu-base/build"
ln -s "$RUN/output" "$RUN/source/spu/spu-base/build/gpu_evaluation"
python3 --version
cmake --version
c++ --version
cmake -S "$RUN/source/sim1/spu-sim" -B "$RUN/build-sim1" -DCMAKE_BUILD_TYPE=Release
cmake --build "$RUN/build-sim1" --parallel 2
ctest --test-dir "$RUN/build-sim1" --output-on-failure
```

For each frozen view, generate the Python finite-width device-model output,
render its emitted packet using the reconstructed C++ executable, and compare
the complete RGB8 payload after removing the 15-byte PPM header. Run each
command separately so it stays within its 60-second limit. First run this
preflight from the reconstructed SPU root after setting `RUN` as above:

```bash
RUN="$(pwd)/build/gpu_evaluation/sim_g1_repro/run_02"
PKG="$(pwd)/build/gpu_evaluation/sim_g1_repro"
cd "$RUN/source/spu/spu-base"
env -u PYTHONPATH -u PYTHONHOME python3 -c 'import hashlib,json,pathlib,sys,software.spu_gpu_eval.cli as cli; assert sys.version_info >= (3,10); root=pathlib.Path.cwd().resolve(); manifest=json.loads(pathlib.Path(sys.argv[1]).read_text()); assert pathlib.Path(cli.__file__).resolve()==root/"software/spu_gpu_eval/cli.py"; assert len(manifest["files"])==88; assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in manifest["files"].items()); assert hashlib.sha256(pathlib.Path(sys.argv[2]).read_bytes()).hexdigest()=="a64327c1bc0c8c74a4fb8c849a922a1f8b3d6a6e2e3bb58951d11f2012bb5248"; print("Python",sys.version.split()[0],"import origin, 88 overlay files, and reciprocal ROM hash: PASS")' "$PKG/gpu_w1_source_e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3.json" "$RUN/source/sim1/spu-sim/hardware/rtl/arch/gpu_reciprocal_lut_q15.mem"
test "$(git rev-parse HEAD)" = 62aa4f993b917618d7b128381d82d4b980e840c9
test "$(sed -n 's/^CMAKE_HOME_DIRECTORY:INTERNAL=//p' "$RUN/build-sim1/CMakeCache.txt")" = "$RUN/source/sim1/spu-sim"
test -x "$RUN/build-sim1/spu-sim"
sha256sum "$RUN/build-sim1/spu-sim"
```

Only after that preflight passes, run the three render comparisons. Use the
same shell session so `RUN` and the reconstructed working directory remain set;
each command line is a separately bounded operation.

```bash
env -u PYTHONPATH -u PYTHONHOME python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/golden_core_tetra_views/identity.json --out "$RUN/output/identity"
"$RUN/build-sim1/spu-sim" gpu render "$RUN/output/identity/scene_packet.bin" --output "$RUN/output/identity/sim1.rgb8" --rom "$RUN/source/sim1/spu-sim/hardware/rtl/arch/gpu_reciprocal_lut_q15.mem"
python3 -c 'from pathlib import Path; import hashlib,sys; h=bytes.fromhex("50360a363430203438300a3235350a"); w=Path(sys.argv[1]).read_bytes(); p=Path(sys.argv[2]).read_bytes(); q=Path(sys.argv[3]).read_bytes(); assert hashlib.sha256(w).hexdigest()==sys.argv[4], "packet hash mismatch"; assert p.startswith(h) and len(p)==len(h)+921600; rgb=p[len(h):]; assert len(q)==921600 and q==rgb, "RGB8 mismatch"; assert hashlib.sha256(rgb).hexdigest()==sys.argv[5] and hashlib.sha256(q).hexdigest()==sys.argv[5], "historical frame hash mismatch"' "$RUN/output/identity/scene_packet.bin" "$RUN/output/identity/device_preview.ppm" "$RUN/output/identity/sim1.rgb8" e2ef44e4087e7c8a2d1a67c3ef24abde1e2542d9b8f5a74c11753762dad43942 434e6b5525fcfc75ddb8e5888a1e6cda0c4e877c5d08518af90a5aa01ba90691
env -u PYTHONPATH -u PYTHONHOME python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/golden_core_tetra_views/rotate_bcd.json --out "$RUN/output/rotate_bcd"
"$RUN/build-sim1/spu-sim" gpu render "$RUN/output/rotate_bcd/scene_packet.bin" --output "$RUN/output/rotate_bcd/sim1.rgb8" --rom "$RUN/source/sim1/spu-sim/hardware/rtl/arch/gpu_reciprocal_lut_q15.mem"
python3 -c 'from pathlib import Path; import hashlib,sys; h=bytes.fromhex("50360a363430203438300a3235350a"); w=Path(sys.argv[1]).read_bytes(); p=Path(sys.argv[2]).read_bytes(); q=Path(sys.argv[3]).read_bytes(); assert hashlib.sha256(w).hexdigest()==sys.argv[4], "packet hash mismatch"; assert p.startswith(h) and len(p)==len(h)+921600; rgb=p[len(h):]; assert len(q)==921600 and q==rgb, "RGB8 mismatch"; assert hashlib.sha256(rgb).hexdigest()==sys.argv[5] and hashlib.sha256(q).hexdigest()==sys.argv[5], "historical frame hash mismatch"' "$RUN/output/rotate_bcd/scene_packet.bin" "$RUN/output/rotate_bcd/device_preview.ppm" "$RUN/output/rotate_bcd/sim1.rgb8" 8d829ce865a2053578e5369b437ec9b603023cbf624e6a6d573f112af7ee7b37 f8a6afbfeb929e5079b800893acf5fb15623c0e9a09807d61bac1d4d66baaad4
env -u PYTHONPATH -u PYTHONHOME python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/golden_core_tetra_views/reflect_bc.json --out "$RUN/output/reflect_bc"
"$RUN/build-sim1/spu-sim" gpu render "$RUN/output/reflect_bc/scene_packet.bin" --output "$RUN/output/reflect_bc/sim1.rgb8" --rom "$RUN/source/sim1/spu-sim/hardware/rtl/arch/gpu_reciprocal_lut_q15.mem"
python3 -c 'from pathlib import Path; import hashlib,sys; h=bytes.fromhex("50360a363430203438300a3235350a"); w=Path(sys.argv[1]).read_bytes(); p=Path(sys.argv[2]).read_bytes(); q=Path(sys.argv[3]).read_bytes(); assert hashlib.sha256(w).hexdigest()==sys.argv[4], "packet hash mismatch"; assert p.startswith(h) and len(p)==len(h)+921600; rgb=p[len(h):]; assert len(q)==921600 and q==rgb, "RGB8 mismatch"; assert hashlib.sha256(rgb).hexdigest()==sys.argv[5] and hashlib.sha256(q).hexdigest()==sys.argv[5], "historical frame hash mismatch"' "$RUN/output/reflect_bc/scene_packet.bin" "$RUN/output/reflect_bc/device_preview.ppm" "$RUN/output/reflect_bc/sim1.rgb8" c0c439c1955a43f86793fa439aa2d1617a4a671a8237850c5acde802f63b772d ad7415db404a5189012b1dfcd30bd096317420d631f4555a7cf3b4459e162c7e
```

Write a machine-readable replay manifest under `$RUN` containing source
archive hashes, source commits, build tool versions, scene and packet hashes,
Python and C++ frame hashes, byte counts, comparison results, and exact
commands. The reviewer must be able to reproduce the run from the distributed
archives on a clean checkout without a Git remote or the original workspace.

## 4. Acceptance criteria

- All three reconstructed scene definitions and source files match the frozen
  manifest hashes.
- SIM-1 builds from the archived commit and its conformance suite passes.
- Each scene packet has the historical expected SHA-256.
- Each Python and C++ frame is 921,600 bytes and matches the historical
  expected SHA-256 and the other implementation byte-for-byte.
- The replay manifest captures commands, source and tool identities, and
  results; no output depends on unstated files from the dirty workspace.
- Report the result as cross-implementation consistency for three frozen
  packets. Do not call it an independent correctness proof or physical GPU
  qualification.

## 5. Execution budget and stop conditions

The owner authorized one replay attempt with a 60-second wall-clock limit per
command and a five-minute cumulative campaign budget. `run_01` stopped before
build because the operator supplied the SIM-1 archive digest where the ROM
digest was required; no arithmetic or source conclusion followed. The corrected
`run_02` replay passed archive and source checks, built SIM-1, passed all three
CTest checks, and matched packet and RGB8 hashes for all three scenes. Its
machine-readable record is
[`build/gpu_evaluation/sim_g1_repro/run_02/replay_manifest.json`](/home/user/Projects/hardware/SPU/build/gpu_evaluation/sim_g1_repro/run_02/replay_manifest.json).

The initial `run_02` preview invocation was rejected before writing output
because the CLI enforces its reconstructed-root output policy. The corrected
procedure above creates a symlink in the reconstructed scratch tree so output
remains below the replay evidence directory. No renderer, ISA, RTL, or FPGA
flow was changed. The result is limited to cross-implementation consistency for
the three frozen packets; it is not an independent correctness proof or
physical GPU qualification.

Do not edit ISA-A, RTL, the Python rasterizer, SIM-1 semantics, or FPGA build
flows. Do not commit, publish, or configure remotes as part of this tranche.

## 6. Related evidence

- `docs/GOLDEN_CORE_T1D_SIM1_COMPARISON_2026-10-17.md`
- `spu_strategy/contract_spu_sim_sim1_2026-10-15.md`
- `spu_strategy/contract_gpu_w1c_local_viewer_2026-10-17.md`
