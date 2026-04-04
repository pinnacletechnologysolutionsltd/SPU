# vim-sovereign — Vim/Neovim plugin for Sovereign Assembly

Syntax highlighting and file-type settings for **Sovereign Assembly** (`.sas`)
and **Laminar Lang** (`.lam`) files used in the
[SPU-13 Sovereign Engine](../../README.md) project.

Compatible with **Vim 8+** and **Neovim** without modification.

## Features

- Syntax highlighting for opcodes, registers, labels, literals, and comments
- Sensible indentation defaults (4-space, expandtab)
- `commentstring` set to `;` for `gcc` / `tcomment` / native `gc`
- `<F5>` runs `./software/vm/spu_vm %` when the binary is present
- `<leader>p` runs with `--proof` for Davis Law verification output

## Install

### Manual

**Vim:**
```sh
cp -r tools/vim-sovereign/* ~/.vim/
```

**Neovim:**
```sh
cp -r tools/vim-sovereign/* ~/.config/nvim/
```

### vim-plug

```vim
" Until published on GitHub, use the local path:
Plug '/path/to/SPU/tools/vim-sovereign'

" Once published:
" Plug 'sovereign-spu/vim-sovereign'
```

### lazy.nvim

```lua
{
  dir = "/path/to/SPU/tools/vim-sovereign",
  -- Once published: 'sovereign-spu/vim-sovereign'
}
```

### packer

```lua
use '/path/to/SPU/tools/vim-sovereign'
-- Once published: use 'sovereign-spu/vim-sovereign'
```

## Highlight groups

| Group | Linked to | Covers |
|---|---|---|
| `sovereignOpcode` | `Keyword` | LD ADD SUB MUL ROT LOG |
| `sovereignFlowOp` | `Conditional` | JMP SNAP COND CALL RET NOP |
| `sovereignQuadrayOp` | `Function` | QLOAD QADD QROT … ANNE |
| `sovereignRegister` | `Identifier` | R0–R25 |
| `sovereignQRegister` | `Type` | QR0–QR12 |
| `sovereignHex` | `Number` | 0x… literals |
| `sovereignNumber` | `Number` | decimal integers |
| `sovereignLabel` | `Label` | `LOOP:` definitions |
| `sovereignComment` | `Comment` | `;` to EOL |

## Project links

- [Project README](../../README.md)
- [Example programs](../../software/programs/)
