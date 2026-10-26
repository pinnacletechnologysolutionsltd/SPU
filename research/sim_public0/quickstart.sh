#!/bin/sh
# Run from a fresh spu-sim checkout at the pinned revision; no installation.
set -eu
test "$(git rev-parse HEAD)" = c1e0676eee5d2398b8d90eec43bd55b2d2f6b924
test -z "$(git status --porcelain)"
cmake -S . -B build/public0 -DCMAKE_BUILD_TYPE=Release
cmake --build build/public0 --parallel 2 --target spu-sim
build/public0/spu-sim gpu render fixtures/gpu_t1d_scene_wire_64b.bin --output build/public0/t1d.rgb8
test "$(wc -c < build/public0/t1d.rgb8)" -eq 921600
printf '%s\n' '96950fa5610063be28056ab0ff9f198a94bbc38ab9aa48949684592d69de7a10  build/public0/t1d.rgb8' | sha256sum -c -
test -z "$(git status --porcelain)"
