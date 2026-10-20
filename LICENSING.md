# Repository licensing map

This repository uses directory-specific licenses. A notice in a file takes
precedence over its directory's default, and a nearer directory notice takes
precedence over the root fallback.

| Scope | License |
|---|---|
| `hardware/` | CERN-OHL-W-2.0, from `hardware/LICENSE`, except files carrying a more-specific notice |
| `software/` | MIT, from `software/LICENSE`, except files carrying a more-specific notice |
| `docs/` and `knowledge/` | CC0 1.0 Universal, from `docs/LICENSE` |
| `examples/` and `fixtures/` | MIT, from `software/LICENSE`, for original content by the repository owner, except files carrying a more-specific notice and third-party material |
| `spu_strategy/` | Apache-2.0, from the root `LICENSE`, for original content by the repository owner, except files carrying a more-specific notice |
| Root-level files and `tools/` without a more-specific notice | Apache-2.0, from the root `LICENSE` |

This map documents the repository's current license layout; it does not
relicense existing contributions. In particular:

- MCU firmware currently located under `hardware/` follows the hardware
  directory license unless its source file says otherwise.
- The installable `spu-host` Python distribution contains only
  `software/spu_host/` and is MIT-licensed.
- Generated artifacts and third-party material retain their own notices.
- The `examples/`, `fixtures/` and `spu_strategy/` rows state the license under
  which the owner offers that original material from this release onward. They
  make no claim about earlier grants or about any other person's contributions.
- `photonics/` and `results/` have no license mapping yet; no license is
  granted for them by this map.

Before moving a file between licensed directory scopes, preserve its original
license notice or obtain the required contributor permission.
