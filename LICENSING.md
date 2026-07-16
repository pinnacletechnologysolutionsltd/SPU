# Repository licensing map

This repository uses directory-specific licenses. A nearer file or directory
notice takes precedence over the root fallback.

| Scope | License |
|---|---|
| `hardware/` | CERN-OHL-W-2.0, from `hardware/LICENSE`, except files carrying a more-specific notice |
| `software/` | MIT, from `software/LICENSE`, except files carrying a more-specific notice |
| `docs/` and `knowledge/` | CC0 1.0 Universal, from `docs/LICENSE` |
| Root-level files and `tools/` without a more-specific notice | Apache-2.0, from the root `LICENSE` |

This map documents the repository's current license layout; it does not
relicense existing contributions. In particular:

- MCU firmware currently located under `hardware/` follows the hardware
  directory license unless its source file says otherwise.
- The installable `spu-host` Python distribution contains only
  `software/spu_host/` and is MIT-licensed.
- Generated artifacts and third-party material retain their own notices.

Before moving a file between licensed directory scopes, preserve its original
license notice or obtain the required contributor permission.
