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

# Optional Boost ABI shim -- the fish counterpart of the block in
# tools/env_openxc7.sh, which this file was missing. openXC7's prebuilt
# bbasm/nextpnr-xilinx are linked against a specific Boost minor version and
# Boost keeps no ABI compatibility across minor releases, so a distribution
# upgrade silently breaks BOTH and with them every A7 bitstream build. If a
# matching set of Boost shared objects has been placed in
# $OPENXC7_ROOT/lib/boost-<version>, prepend it. Absent on most machines,
# where this loop does nothing.
#
# To repopulate it on Arch after an upgrade has broken the toolchain, take the
# .so files from the OLD package still in the pacman cache -- symlinking the
# new version's libraries does NOT work, the ABI really has changed:
#   tar -I zstd -xf /var/cache/pacman/pkg/boost-libs-<old>-x86_64.pkg.tar.zst \
#       -C /tmp/boostx usr/lib
#   mkdir -p $OPENXC7_ROOT/lib/boost-<old>
#   cp /tmp/boostx/usr/lib/*.so.<old> $OPENXC7_ROOT/lib/boost-<old>/
for _openxc7_boost in $OPENXC7_ROOT/lib/boost-*
    if test -d $_openxc7_boost
        if set -q LD_LIBRARY_PATH
            if not contains -- $_openxc7_boost (string split : $LD_LIBRARY_PATH)
                set -gx LD_LIBRARY_PATH $_openxc7_boost $LD_LIBRARY_PATH
            end
        else
            set -gx LD_LIBRARY_PATH $_openxc7_boost
        end
    end
end
set -e _openxc7_boost

set -gx NEXTPNR_XILINX_PYTHON_DIR $OPENXC7_ROOT/lib/python
set -gx PRJXRAY_DB_DIR $OPENXC7_ROOT/share/nextpnr/prjxray-db
