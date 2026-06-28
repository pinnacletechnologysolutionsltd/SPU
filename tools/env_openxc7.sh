#!/usr/bin/env bash
# Source this file to enable the repo's Artix-7 openXC7 toolchain.
#
# Default install prefix:
#   $HOME/.local/openxc7
#
# Override before sourcing:
#   OPENXC7_ROOT=/opt/openxc7 source tools/env_openxc7.sh

if [ -n "${BASH_VERSION:-}" ]; then
    _openxc7_script="${BASH_SOURCE[0]}"
else
    _openxc7_script="$0"
fi

OPENXC7_ROOT="${OPENXC7_ROOT:-$HOME/.local/openxc7}"

if [ ! -d "$OPENXC7_ROOT" ]; then
    echo "openXC7 install not found: $OPENXC7_ROOT" >&2
    return 1 2>/dev/null || exit 1
fi

case ":$PATH:" in
    *":$OPENXC7_ROOT/bin:"*) ;;
    *) export PATH="$OPENXC7_ROOT/bin:$PATH" ;;
esac

case ":${PYTHONPATH:-}:" in
    *":$OPENXC7_ROOT/lib/python:"*) ;;
    *) export PYTHONPATH="$OPENXC7_ROOT/lib/python${PYTHONPATH:+:$PYTHONPATH}" ;;
esac

export OPENXC7_ROOT
export NEXTPNR_XILINX_PYTHON_DIR="$OPENXC7_ROOT/lib/python"
export PRJXRAY_DB_DIR="$OPENXC7_ROOT/share/nextpnr/prjxray-db"

unset _openxc7_script
