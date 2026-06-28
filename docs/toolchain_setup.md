# Toolchain Setup

This repo uses two FPGA toolchain layers:

- OSS CAD Suite for Gowin, ECP5, iCE40, simulation, and general synthesis.
- OpenXC7 for Artix-7 / Wukong place-and-route and bitstream work.

Do not assume OSS CAD Suite alone is enough for Wukong. The standard OSS CAD
Suite package provides the non-Xilinx nextpnr targets we use, but Artix-7 uses
the separate OpenXC7 `nextpnr-xilinx` flow plus a generated chip database.

## Canonical Local Layout

Use this install prefix for OpenXC7 unless there is a reason not to:

```text
$HOME/.local/openxc7
```

The repo expects:

```text
$HOME/.local/openxc7/bin/nextpnr-xilinx
$HOME/.local/openxc7/bin/bbasm
$HOME/.local/openxc7/bin/xc7frames2bit
$HOME/.local/openxc7/lib/python/bbaexport.py
$HOME/.local/openxc7/share/nextpnr/prjxray-db
$HOME/.local/openxc7/lib/external/nextpnr-xilinx-meta
$HOME/.local/openxc7/lib/constids.inc
```

Bitstream packing also needs Project X-Ray's `fasm2frames.py`. Keep its Python
environment isolated from the system interpreter:

```bash
python3 -m venv $HOME/.local/openxc7/venv
$HOME/.local/openxc7/venv/bin/python -m pip install textX PyYAML simplejson intervaltree
```

If `fasm2frames` is not installed as an executable, point the build script at a
stable Project X-Ray source checkout:

```bash
export PRJXRAY_ROOT=$HOME/src/prjxray
export OPENXC7_PYTHON=$HOME/.local/openxc7/venv/bin/python
```

Override the prefix with `OPENXC7_ROOT`:

```bash
OPENXC7_ROOT=/opt/openxc7 bash hardware/boards/artix7/build_a7.sh 100t robotics synth
```

## Permanent Shell Setup

Permanent setup should add only the OpenXC7 executable path and prefix. Avoid
permanent global `PYTHONPATH`; the repo helper and Artix build scripts set that
locally when needed.

### fish

```fish
set -Ux OPENXC7_ROOT $HOME/.local/openxc7
fish_add_path $HOME/.local/openxc7/bin
```

For a one-shot session with all OpenXC7 Python paths:

```fish
source tools/env_openxc7.fish
```

### bash / zsh

Add this to `~/.bashrc`, `~/.zshrc`, or the equivalent shell file:

```bash
export OPENXC7_ROOT="$HOME/.local/openxc7"
export PATH="$OPENXC7_ROOT/bin:$PATH"
```

For a one-shot session with all OpenXC7 Python paths:

```bash
source tools/env_openxc7.sh
```

## Artix-7 Chip Database

Generate each chip database once. The outputs live under `build/chipdb/`.

```bash
tools/generate_a7_chipdb.sh 100t
```

Expected output:

```text
build/chipdb/xc7a100tfgg676.bin
```

Other supported generator targets:

```bash
tools/generate_a7_chipdb.sh 35t
tools/generate_a7_chipdb.sh 200t
```

Regenerate with:

```bash
FORCE=1 tools/generate_a7_chipdb.sh 100t
```

## OS Notes

### Linux

Recommended for all targets. Install OSS CAD Suite from its release archive,
extract it somewhere stable, and add its `bin` directory to `PATH` or source its
environment file.

Common source-build dependencies for OpenXC7:

```text
cmake git gcc/g++ make python3 boost eigen
```

Arch package names are typically:

```bash
sudo pacman -S --needed base-devel cmake git python boost boost-libs eigen
```

Ubuntu/Debian package names are typically:

```bash
sudo apt install build-essential cmake git python3 libboost-all-dev libeigen3-dev
```

### macOS

OSS CAD Suite provides macOS archives for Intel and Apple Silicon. After
download, macOS may quarantine the archive; follow the OSS CAD Suite release
instructions for clearing quarantine or activating the extracted environment.

OpenXC7 source builds are possible, but Linux or WSL2 is the lower-friction path
for Wukong until we have a macOS-tested Artix-7 build recipe.

### Windows

OSS CAD Suite provides Windows archives. For this repo, use WSL2 Linux for the
OpenXC7 Artix-7 flow. Native Windows OpenXC7 setup is not the canonical path.

### CI / Headless

Do not rely on user shell startup files. Set `OPENXC7_ROOT`, add
`$OPENXC7_ROOT/bin` to `PATH`, then call:

```bash
tools/generate_a7_chipdb.sh 100t
bash hardware/boards/artix7/build_a7.sh 100t robotics synth
```

For Wukong robotics place-and-route with schematic-derived pins:

```bash
A7_FREQ=2 \
  bash hardware/boards/artix7/build_a7.sh 100t robotics pnr
```

Use `pack` after P&R to emit `build/spu_a7_100t_ROBOTICS.bit`.
