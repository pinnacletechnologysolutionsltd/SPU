# Source this file to enable the repo's Artix-7 openXC7 toolchain in fish.
#
# Default install prefix:
#   $HOME/.local/openxc7
#
# Override before sourcing:
#   set -gx OPENXC7_ROOT /opt/openxc7; source tools/env_openxc7.fish

if not set -q OPENXC7_ROOT
    set -gx OPENXC7_ROOT $HOME/.local/openxc7
end

if not test -d $OPENXC7_ROOT
    echo "openXC7 install not found: $OPENXC7_ROOT" >&2
    return 1
end

if not contains -- $OPENXC7_ROOT/bin $PATH
    set -gx PATH $OPENXC7_ROOT/bin $PATH
end

if set -q PYTHONPATH
    if not contains -- $OPENXC7_ROOT/lib/python (string split : $PYTHONPATH)
        set -gx PYTHONPATH $OPENXC7_ROOT/lib/python $PYTHONPATH
    end
else
    set -gx PYTHONPATH $OPENXC7_ROOT/lib/python
end

set -gx NEXTPNR_XILINX_PYTHON_DIR $OPENXC7_ROOT/lib/python
set -gx PRJXRAY_DB_DIR $OPENXC7_ROOT/share/nextpnr/prjxray-db
