#!/usr/bin/env bash
# generate_gerbers.sh — Export Gerber/NC-Drill files from SPU-13 ECP5 KiCad project
#
# Requires: kicad-cli (KiCad 8.0 command-line tools)
# Install:  apt install kicad-cli  or  pacman -S kicad
#
# Usage:    bash generate_gerbers.sh
# Output:   build/gerbers/  (Gerbers + drill files + ZIP archive)

set -euo pipefail

PROJECT_DIR="hardware/pcb"
PROJECT_NAME="spu13_ecp5_carrier"
OUTPUT_DIR="build/gerbers"
PROJECT_FILE="${PROJECT_DIR}/${PROJECT_NAME}.kicad_pcb"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo "[*] Generating Gerber files for ${PROJECT_NAME}..."

# Check for kicad-cli
if ! command -v kicad-cli &> /dev/null; then
    echo "  ⚠  kicad-cli not found. Install KiCad 8.0 or run manually:"
    echo "     kicad-cli pcb export gerbers ${PROJECT_FILE} -o ${OUTPUT_DIR}"
    echo "     kicad-cli pcb export drill  ${PROJECT_FILE} -o ${OUTPUT_DIR}"
    echo ""
    echo "  Creating placeholder directory structure for future Gerber output."
    touch "${OUTPUT_DIR}/.gitkeep"
    echo "  [+] Placeholder created. Replace with actual Gerbers after KiCad export."
    exit 0
fi

# Export Gerber layers (F.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts)
echo "  [+] Exporting Gerber layers..."
kicad-cli pcb export gerbers \
    --layers "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
    "${PROJECT_FILE}" \
    -o "${OUTPUT_DIR}"

# Export NC-Drill file
echo "  [+] Exporting NC-Drill file..."
kicad-cli pcb export drill \
    --format excellon \
    --generate-map \
    "${PROJECT_FILE}" \
    -o "${OUTPUT_DIR}"

# Create a ZIP archive for PCB fab houses
echo "  [+] Creating Gerber ZIP archive..."
cd "${OUTPUT_DIR}"
zip -qX "${PROJECT_NAME}_gerbers.zip" *.gbr *.gbrjob *.drl *.map 2>/dev/null || true
cd - > /dev/null

echo "[*] Gerber files generated in: ${OUTPUT_DIR}"
ls -lh "${OUTPUT_DIR}/"
echo "[*] Done. Upload the ZIP to your PCB fab house."
