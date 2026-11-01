#!/usr/bin/env bash
# CPU-REPRO-1 portable preflight. Read-only. Usage: preflight.sh [--offline] [RUN_ID]
#   --offline : skip Vivado, memory, disk and process checks (hash and structure checks only).
# Env: VIVADO_SETTINGS (path to settings64.sh; required unless --offline), GOLDEN_VIVADO (golden build/vivado dir; optional, enables golden-artifact checks).
set -u
OFFLINE=0; [ "${1:-}" = "--offline" ] && { OFFLINE=1; shift; }
RUN_ID=${1:-}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); PKG=$(cd "$HERE/.." && pwd); REPO=$(cd "$PKG/../../../../.." && pwd)
cd "$REPO" || exit 90
fail() { echo "PREFLIGHT_HOLD $1: $2"; exit "$1"; }
git rev-parse --show-toplevel > /dev/null 2>&1 || fail 90 "not a git checkout"
[ "$(git rev-parse --show-toplevel)" = "$REPO" ] || fail 90 "package is not at the expected depth inside the repository"
( cd "$PKG" && sha256sum -c PACKAGE_SHA256.txt > /dev/null 2>&1 ) || fail 91 "PACKAGE_SHA256.txt mismatch"
# Phase S manifest of the golden build lists every synthesis source; hashes must match the checkout (paths differ for the five moved files).
M="$PKG/provenance/build_identity/phaseS_run_manifest.txt"
want=$(grep '^source_sha256' "$M" | awk '{print $2}' | sort)
got=$(grep '^sv ' "$PKG/filelists/candidate_portable.f" | awk '{print $2}' | xargs sha256sum | awk '{print $1}' | sort)
[ "$want" = "$got" ] || fail 92 "portable filelist sources differ from the golden synthesis manifest"
[ "$(grep -c '^sv ' "$PKG/filelists/candidate_portable.f")" = 22 ] || fail 92 "expected 22 sv entries"
grep -q "^xdc_sha256 $(sha256sum "$PKG/constraints/cpu_board_3.xdc" | cut -c1-64)" "$M" || fail 92 "XDC differs from the golden manifest"
for h in $(grep '\.vh$' "$PKG/provenance/build_identity/cpu_integrate_4_SOURCE.sha256" | awk '{print $2":"$1}'); do
  [ "$(sha256sum "${h%%:*}" | cut -c1-64)" = "${h##*:}" ] || fail 92 "header ${h%%:*} differs"; done
[ "$(sha256sum tools/vivado/spu_vivado_flow.tcl | cut -c1-64)" = 9aa1e17c5064a242187b4059a370851f6c3109348b5f4a433871ae73abd092f0 ] || fail 92 "flow script hash"
( cd "$PKG" && sha256sum -c portable/PORTABLE_SHA256.txt > /dev/null 2>&1 ) || fail 91 "portable/PORTABLE_SHA256.txt mismatch"
if [ -n "${GOLDEN_VIVADO:-}" ]; then
  [ "$(sha256sum "$GOLDEN_VIVADO/board4b_01/bit/cpu_board_2r_top.bin" | cut -c1-64)" = cc259988b32dcd890a25c8a1765c6a28e3fafa280bcaed1aa5073f552dbc156c ] || fail 93 "golden .bin hash"
  [ "$(sha256sum "$GOLDEN_VIVADO/board4b_01/bit/cpu_board_2r_top.bit" | cut -c1-64)" = 442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea ] || fail 93 "golden .bit hash"
fi
if [ $OFFLINE = 0 ]; then
  [ -n "${VIVADO_SETTINGS:-}" ] && [ -f "$VIVADO_SETTINGS" ] || fail 94 "VIVADO_SETTINGS not set or missing"
  ver=$(bash -c "source '$VIVADO_SETTINGS' > /dev/null 2>&1; cd "$(mktemp -d)" && vivado -version 2>&1 | head -3")
  echo "$ver" | grep -q 'vivado v2026.1 ' || fail 94 "Vivado is not 2026.1"
  echo "$ver" | grep -q 'SW Build 6511674 ' || fail 94 "Vivado SW build is not 6511674"
  avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$avail" -ge 5242880 ] || fail 96 "MemAvailable ${avail} kB < 5242880 kB (5 GiB)"
  [ "$(df -k --output=avail "$REPO" | tail -1)" -ge 20971520 ] || fail 93 "less than 20 GiB free"
  pgrep -f '[v]ivado -mode' > /dev/null && fail 88 "another Vivado is running"
fi
[ -z "$RUN_ID" ] || { [ ! -e "$REPO/build/cpu-repro-1/$RUN_ID" ] || fail 89 "build/cpu-repro-1/$RUN_ID exists"; }
echo "PREFLIGHT_OK repo=$(git rev-parse --short HEAD) dirty=$(git status --porcelain -- hardware tools | wc -l) offline=$OFFLINE"
