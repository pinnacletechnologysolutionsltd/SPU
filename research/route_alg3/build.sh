#!/usr/bin/env bash
# ROUTE-ALG-3 private build. NOT YET AUTHORIZED TO RUN. Launch only via tools/run_detached_job.sh (AGENTS.md 4.2).
# Same configure flags as the fixture's capture_build, new source/build dirs. Reference build: 279.6 s, -j 2.
set -euo pipefail
R=/home/user/Projects/hardware/SPU/build/route_alg3
[ ! -e "$R/build" ] || { echo "refusing: $R/build exists"; exit 2; }
ulimit -c 0
/usr/bin/cmake -S "$R/source" -B "$R/build" -DARCH=xilinx -DBUILD_GUI=OFF -DBUILD_PYTHON=ON -DBUILD_TESTS=OFF \
  -DBUILD_HEAP=ON -DEIGEN3_INCLUDE_DIRS=/usr/include/eigen3 -DEXTERNAL_CHIPDB=ON \
  -DEXTERNAL_CHIPDB_ROOT=/home/user/.local/openxc7/share/nextpnr -DCURRENT_GIT_VERSION=f681eb3a-spu-native-route-capture \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  "-DCMAKE_CXX_FLAGS=-DSPU_CONSTANT_GUARD_PROBE -DSPU_NATIVE_ROUTE_DIAGNOSTICS" \
  -DCMAKE_CXX_COMPILER=/usr/bin/c++ -DCMAKE_C_COMPILER=/usr/bin/cc
/usr/bin/cmake --build "$R/build" --target nextpnr-xilinx -j 2
sha256sum "$R/build/nextpnr-xilinx"
