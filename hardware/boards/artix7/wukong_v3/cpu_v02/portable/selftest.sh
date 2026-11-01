#!/usr/bin/env bash
# Offline self-test of compare.py and preflight.sh. Needs GOLDEN_VIVADO. Usage: selftest.sh SCRATCH_DIR (must not exist). Runs no Vivado.
set -eu
S=${1:?scratch dir}; [ ! -e "$S" ] || { echo "exists: $S"; exit 2; }
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); G=$GOLDEN_VIVADO
mk() {  # build a run directory that is a copy of the golden outputs (no checkpoints)
  local R=$1; mkdir -p "$R"/{synth,route,analysis,bit/out}
  cp "$G"/board3_01/synth/{run_manifest.txt,*.rpt} "$R/synth/"
  for f in "$G"/board3_01/analysis/*.txt; do cp "$f" "$R/analysis/"; done
  mv "$R/analysis/rom_props.txt" "$R/analysis/synth_rom_props.txt"; mv "$R/analysis/rom_loads.txt" "$R/analysis/synth_rom_loads.txt"
  cp "$G"/board3p_01/route/*.rpt "$G"/board3p_01/route/*.txt "$R/route/"
  cp "$G/board3p_01/analysis/rom_props.txt" "$R/analysis/route_rom_props.txt"; cp "$G/board3p_01/analysis/rom_loads.txt" "$R/analysis/route_rom_loads.txt"
  cp "$G"/board4b_01/bit/{cpu_board_2r_top.bit,cpu_board_2r_top.bin,bitstream_properties.txt,pre_bitstream_drc.rpt,waivers.rpt} "$R/bit/out/"
}
mk "$S/same"; python3 -I "$HERE/compare.py" "$S/same" | tail -4; python3 -I "$HERE/compare.py" "$S/same" > /dev/null && echo "CONTROL 1 (golden vs itself): expected PASS-BIT-EXACT, got rc=0"
mk "$S/binflip"; python3 - "$S/binflip/bit/out" <<'PY'
import sys; p=sys.argv[1]+'/cpu_board_2r_top.bin'; b=bytearray(open(p,'rb').read()); b[100000]^=1; open(p,'wb').write(b)
PY
if python3 -I "$HERE/compare.py" "$S/binflip" > "$S/binflip.out"; then echo "CONTROL 2 FAILED: bin flip not detected"; exit 1; else echo "CONTROL 2 (flipped .bin byte): rc=$? as expected"; tail -1 "$S/binflip.out"; fi
mk "$S/rptdiff"; sed -i '0,/WNS/s/WNS/WNX/' "$S/rptdiff/route/routed_timing_summary.rpt"
python3 -I "$HERE/compare.py" "$S/rptdiff" | grep -E 'DIFF|report differences|VERDICT'
mk "$S/hdr"; python3 - "$S/hdr/bit/out" <<'PY'
import sys; p=sys.argv[1]+'/cpu_board_2r_top.bit'; b=bytearray(open(p,'rb').read()); i=b.find(b'2026/10/30'); b[i+9:i+10]=b'1'; open(p,'wb').write(b)   # header date only
PY
python3 -I "$HERE/compare.py" "$S/hdr" | grep -E '^\.bit|VERDICT'
echo "CONTROL 5 (preflight --offline):"; GOLDEN_VIVADO=$G bash "$HERE/preflight.sh" --offline || true
