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
- The `photonics/` and `results/` directories are not part of this release. This licensing map assigns no
  license to them; any earlier distribution of those files is governed by the notices published with that
  distribution.
- `research/` (research experiments, their findings and frozen records) is covered by the root fallback
  (Apache-2.0) unless a file carries a more-specific notice.
- Exception: where present, the historical source snapshots in `research/xc7_qual_1/src/` and
  `research/xc7_qual_2/src_*/` contain unmodified copies of `.v`, `.xdc` and `.ys` files from `hardware/`. Each copy is byte-identical to a
  version of a `hardware/` file in this repository's history, and those versions carry no more-specific notice.
  The copies keep the `hardware/` license (CERN-OHL-W-2.0); being stored under `research/` does not relicense
  them. The `HEAD_COMMIT` and `SOURCES.sha256` records in those directories were written by the experiments and
  follow the `research/` fallback. These XC7 snapshots are in the development history; they are not part of
  the curated v0.2 release tree, in which this exception therefore has no files to apply to.
- Vivado- and nextpnr-generated report excerpts and logs under `tools/vivado/tests/` are tool output kept as
  test fixtures; they retain any notice printed by the tool that produced them.
- The `.bin` files under `software/` and `fixtures/` are assembled program images, lookup tables and wire
  payloads generated from the sources in this repository; they follow the license of their directory.
- Bench photographs under `docs/bench_captures/` follow the `docs/` license. Location and device metadata
  were removed from the three photographs in `docs/bench_captures/t1n_h1_2026-09-28/`; see `SANITIZED.txt` there.

Before moving a file between licensed directory scopes, preserve its original
license notice or obtain the required contributor permission.
