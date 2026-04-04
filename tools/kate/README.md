# Kate syntax for Sovereign Assembly

KSyntaxHighlighting grammar for **Sovereign Assembly** (`.sas`) and
**Laminar Lang** (`.lam`) files used in the
[SPU-13 Sovereign Engine](../../README.md) project.

Works with **Kate**, **KWrite**, and **KDevelop**.

## Install

### Per-user (recommended)

```sh
mkdir -p ~/.local/share/org.kde.syntax-highlighting/syntax/
cp tools/kate/sovereign.xml ~/.local/share/org.kde.syntax-highlighting/syntax/
```

Restart Kate / KWrite — *Sovereign Assembly* will appear under
**Settings → Configure Kate → Open/Save → Modes & Filetypes** and will
auto-detect `.sas` / `.lam` files.

### System-wide

```sh
sudo cp tools/kate/sovereign.xml /usr/share/org.kde.syntax-highlighting/syntax/
```

## Highlight tokens

| Token | Default style | Covers |
|---|---|---|
| `Keyword` | `dsKeyword` | LD ADD SUB MUL ROT LOG |
| `FlowKeyword` | `dsControlFlow` | JMP SNAP COND CALL RET NOP |
| `QuadrayKeyword` | `dsFunction` | QLOAD QADD QROT … ANNE |
| `Register` | `dsVariable` | R0–R25 |
| `QuadrayRegister` | `dsDataType` | QR0–QR12 |
| `Hex` | `dsBaseN` | 0x… literals |
| `Number` | `dsDecVal` | decimal integers |
| `Label` | `dsPreprocessor` | `LOOP:` definitions |
| `Comment` | `dsComment` | `;` to EOL |

## Project links

- [Project README](../../README.md)
- [Example programs](../../software/programs/)
