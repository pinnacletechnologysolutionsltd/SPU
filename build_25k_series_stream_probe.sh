#!/usr/bin/env bash
# build_25k_series_stream_probe.sh -- Tang 25K series-stream silicon probe.
# Walks all 8 committed golden vectors (incl. 2 singular) through the eps^3
# Hyper-Catalan series evaluator with ONE shared M31 multiplier muxed
# between the Fp4 tower and the stream.
set -e
mkdir -p build

CST="${CST:-hardware/boards/tang_primer_25k/tang_primer_25k.cst}"

echo "=== Series-Stream Probe for Tang Primer 25K ==="

echo "--- Yosys Synthesis ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_series_stream_probe.ys

echo "--- NextPNR Place & Route ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst="$CST" \
    --json build/series_stream_probe.json \
    --write build/series_stream_probe_pnr.json \
    --freq 12

echo "--- Gowin Bitstream Pack ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/series_stream_probe_pnr.json \
    -o build/tang_primer_25k_series_stream_probe.fs

echo "=== DONE: build/tang_primer_25k_series_stream_probe.fs ==="
echo "Flash:  openFPGALoader -b tangprimer25k build/tang_primer_25k_series_stream_probe.fs"
echo "UART (115200, BL616 CDC / pin C3):"
echo "  SSTR:P V=8 M=1A E=00   PASS (8 vectors, 26 mults + 1 tower each)"
echo "  SSTR:F V=<n> M=<mm> E=<code>   FAIL (B0+v root, C0+v counts, D0+v flag)"
