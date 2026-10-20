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
- `software/tests/data/iris.csv` is the UCI Iris dataset (Fisher, 1936; DOI
  10.24432/C56C76), licensed CC BY 4.0 by its source, not MIT. It is
  byte-identical to UCI's `iris.data`; see `software/tests/data/IRIS_PROVENANCE.md`.
  `software/models/iris_som_v1.json` is a map trained on that dataset and must
  keep the same attribution.
- The Paderborn University Bearing Data Center corpus is licensed CC BY-NC 4.0
  (Lessmeier et al., DOI 10.36001/phme.2016.v3i1.1577). This repository does not
  contain the corpus. Files derived from it (`software/datasets/paderborn_*`,
  `docs/PADERBORN_*`) are not offered under the MIT or CC0 grants above for the
  corpus-derived content; any recordings, features or trained maps built from the
  corpus remain non-commercial under CC BY-NC 4.0.
- The `photonics/` and `results/` directories have been removed from the current source tree. Their contents
  remain available in earlier public Git history. This licensing map does not assign a directory-level license to
  those historical files. Any existing file-specific or third-party licenses and notices remain applicable.

Before moving a file between licensed directory scopes, preserve its original
license notice or obtain the required contributor permission.
