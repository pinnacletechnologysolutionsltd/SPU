# Sovereign Assembly — VS Code Extension

Syntax highlighting, snippets, and build tasks for **Sovereign Assembly** (`.sas`)
and **Laminar Lang** (`.lam`) files used in the
[SPU-13 Sovereign Engine](../../README.md) project.

## What is SPU-13?

The SPU-13 is a bit-exact, pipelined, rational-field Q(√3) algebraic processor
designed for high-precision manifold calculations and 60-degree resonance
graphics. All arithmetic is exact — no floating point, no division, no
transcendental approximations. Programs are written in Sovereign Assembly, a
compact ISA whose instructions operate on surd pairs `(a + b·√3)`.

## Install

**From VSIX (recommended):**
```
code --install-extension sovereign-tools-0.1.0.vsix
```
Or open VS Code → Extensions → `...` → *Install from VSIX…* and select the
`.vsix` file.

**Development install:**
```
cd tools/sovereign-tools
npm install -g @vscode/vsce   # one-time
vsce package                  # produces sovereign-tools-0.1.0.vsix
code --install-extension sovereign-tools-0.1.0.vsix
```

Alternatively, copy this directory into
`~/.vscode/extensions/sovereign-tools-0.1.0/` and reload VS Code.

## Features

| Feature | Details |
|---|---|
| Syntax highlighting | Opcodes, registers, labels, hex/decimal literals, comments |
| Code snippets | 10 snippets — `ld`, `rot`, `snap`, `pell`, `qload`, `qadd`, `equil`, `jinv`, `davis`, `spread` |
| Build task | F5 / Ctrl+Shift+B runs `spu_vm` on the open file |
| `--proof` task | Secondary task passes `--proof` flag for Davis Law verification output |

## Usage

1. Open any `.sas` file — syntax highlighting activates automatically.
2. Type a snippet prefix (e.g. `pell`) and press **Tab** to expand.
3. Press **Ctrl+Shift+B** (or **F5**) to run the current file via `spu_vm`.
   The `spu_vm` binary is expected at `${workspaceFolder}/software/vm/spu_vm`.

## Snippets quick reference

| Prefix | Expands to |
|---|---|
| `ld` | `LD R0, 1, 0  ; R0 = 1 + 0·√3` |
| `rot` | `ROT R0  ; Pell step: ×(2+√3)` |
| `snap` | `SNAP  ; Davis Gate assert` |
| `pell` | Full Pell rotor loop |
| `qload` | `QLOAD QR0, R0` |
| `qadd` | `QADD QR0, QR1` |
| `equil` | `EQUIL  ; VE check` |
| `jinv` | `JINV R0  ; Janus flip` |
| `davis` | SNAP-bracketed critical section |
| `spread` | `SPREAD R0, QR0, QR1` |

## Project links

- [Project README](../../README.md)
- [Language reference](../../docs/) *(if present)*
- [Example programs](../../software/programs/)
