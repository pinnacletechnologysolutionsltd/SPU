# SIM-CAP1-I2: minimal C++ capability-manifest schema (DESIGN ONLY, not implemented)

Mirrors `capability_manifest()` in `software/spu_vm.py`; same keys, same meaning.
Emitted by `spu_vm --manifest` (JSON, sorted keys, no clock, no git call).

| key | C++ value | Python equivalent |
|---|---|---|
| `schema_version` | `1` | `1` |
| `implementation` | `"software/vm/spu_vm.cpp"` | `"software/spu_vm.py"` |
| `profile` | `"full"` (C++ VM has no `base` axis; `base` is not accepted) | `full`/`base` |
| `metric_semantics` | `legacy_dot` \| `gram_v1`, as selected by `--metric-semantics` | same |
| `source_revision` | `sha256:` of the concatenation, in sorted path order, of `spu_vm.cpp` and every project header it includes (`checked_math.h`, `assembly_operands.h`, `spu_gram_spread.h`); per-file digests listed under `source_files` | sha256 of `spu_vm.py` |
| `build_id` | `spu_vm.cpp:<profile>:<first 12 hex of source_revision>` | `spu_vm.py:<profile>:<12 hex>` |
| `metric_semantics_detail.spread_opcode_0x15` | same object shape: `support`, `semantic_contract`, `tests`, `conformance`, `evidence`, `scope`, `rtl_functional`, `physical` | same |

Rules (identical to Python):
* `conformance` is always `"not_run"` and `evidence` `null` in the manifest; a test run binds a pass to `source_revision`.
* `legacy_dot` scope text must contain `qualified: false` (spread(A,A) != 0).
* `gram_v1` scope: Gram-consistent spread, atomic `DEGENERATE_METRIC`/`OVERFLOW` refusal, signed-32 result lanes, exact 256-bit intermediates.
* `tests` ids name `test_gram_v1_spread.py` and `test_gram_v1_spread_cpp.py`; an id must exist in its file.
* Reproducibility: the digest is computed at build time by the Makefile and compiled in as `-DSPU_SRC_SHA=<hex>`, so the binary reports the source it was built from, not the source on disk at run time. Compiler id (`__VERSION__`) goes under `toolchain`, not into `source_revision`.
* Implementation (the Makefile hash step, `--manifest` flag, and a parity test comparing the C++ and Python manifests field by field) is NOT done in I2.
