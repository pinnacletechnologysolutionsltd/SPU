#!/usr/bin/env bash
# Generate the nextpnr-xilinx chip database used by Artix-7 builds.

set -euo pipefail

DEVICE_CHIP="${1:-100t}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd)"

case "$DEVICE_CHIP" in
    35t)
        PART="xc7a35tcsg324-1"
        CHIPDB_NAME="xc7a35t"
        ;;
    100t)
        PART="xc7a100tfgg676-1"
        CHIPDB_NAME="xc7a100tfgg676"
        ;;
    200t)
        PART="xc7a200tsbg484-1"
        CHIPDB_NAME="xc7a200t"
        ;;
    *)
        echo "Unknown device: $DEVICE_CHIP (use 35t|100t|200t)" >&2
        exit 1
        ;;
esac

OPENXC7_ROOT="${OPENXC7_ROOT:-$HOME/.local/openxc7}"

if [ -f "$SCRIPT_DIR/env_openxc7.sh" ]; then
    # shellcheck source=/dev/null
    source "$SCRIPT_DIR/env_openxc7.sh"
elif [ -f "$OPENXC7_ROOT/export.sh" ]; then
    # shellcheck source=/dev/null
    source "$OPENXC7_ROOT/export.sh"
else
    echo "openXC7 environment helper not found." >&2
    echo "Set OPENXC7_ROOT or source tools/env_openxc7.sh first." >&2
    exit 1
fi

OUT_DIR="${A7_CHIPDB_DIR:-$REPO_ROOT/build/chipdb}"
BBA="$OUT_DIR/${CHIPDB_NAME}.bba"
BIN="$OUT_DIR/${CHIPDB_NAME}.bin"

if [ -f "$BIN" ] && [ "${FORCE:-0}" != "1" ]; then
    echo "Chip database already exists: $BIN"
    echo "Use FORCE=1 $0 $DEVICE_CHIP to regenerate it."
    exit 0
fi

BBAEXPORT="${NEXTPNR_XILINX_PYTHON_DIR:-$OPENXC7_ROOT/lib/python}/bbaexport.py"
XRAY_ROOT="${PRJXRAY_DB_DIR:-$OPENXC7_ROOT/share/nextpnr/prjxray-db}/artix7"
METADATA_ROOT="${OPENXC7_METADATA_DIR:-$OPENXC7_ROOT/lib/external/nextpnr-xilinx-meta/artix7}"
CONSTIDS="${OPENXC7_CONSTIDS:-$OPENXC7_ROOT/lib/constids.inc}"

for required in "$BBAEXPORT" "$XRAY_ROOT" "$METADATA_ROOT" "$CONSTIDS"; do
    if [ ! -e "$required" ]; then
        echo "Missing required openXC7 file or directory: $required" >&2
        exit 1
    fi
done

mkdir -p "$OUT_DIR"

echo "Generating $PART chip database..."
python3 "$BBAEXPORT" \
    --xray "$XRAY_ROOT" \
    --metadata "$METADATA_ROOT" \
    --device "$PART" \
    --constids "$CONSTIDS" \
    --bba "$BBA"

bbasm --le "$BBA" "$BIN"
echo "Chip database: $BIN"
