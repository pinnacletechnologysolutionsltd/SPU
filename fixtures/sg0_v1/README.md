# SG-0 frozen preparation inputs v1

Prepared 2026-10-18 for the SG-0 implementation contract. These are reviewed-design
inputs and expected vectors, not an implemented or qualified bridge.

- `unique_cycle.proof.json` is copied byte-for-byte from the qualified SSM-3
  `proofs/unique_cycle.json`, including its original inputs and full proof history.
- `inputs.json` freezes parameter order, recipe matrices/offsets, exact transforms,
  projection/rounding rules, expected vertices, scenes/packets and diagnostic pixels.
- `catalogue_before.json` preserves the exact 11-scene workbench allowlist.
  Two proposed appended entries and the exact resulting catalogue hash are in inputs.
- `preparation.json` records checks performed and dimensions not run.
- `SHA256SUMS` pins these data files; this README is descriptive metadata.

Generation ownership: the future `research.sg0` generator must derive example
scenes and their catalogue pins from the proof/inputs. Do not hand-edit generated
scenes, the copied proof or expected coefficients to obtain a pass. Frozen changes
require a new version and contract review. No existing catalogue/scene was changed
in this preparation step.

Executed preparation: independent proof replay, exact recipe and zero-sum bridge
identities, agreement with the existing projector, scene parser and packet encoder,
and selected ideal pixel decisions. Expected integer vertices were proposed in
the earlier SG-0 design and checked against these existing APIs. These are not
independent renderer qualification, full-frame comparisons or workbench publication.

Run from repository root:

```bash
sha256sum -c fixtures/sg0_v1/SHA256SUMS
python3 -m research.ssm3.verify_artifact fixtures/sg0_v1/unique_cycle.proof.json
python3 fixtures/sg0_v1/test_catalogue_serialization.py
```

The preparation-only serialization regression checks the unchanged 11-entry
base bytes and the frozen 13-entry catalogue hash. New entries use explicit
`id`, `path`, `sha256`, `group` field order regardless of input dictionary order;
existing entries retain their original serialization. It publishes no files.

The controlling [SG-0 contract](../../spu_strategy/contract_sg0_certified_geometry_2026-10-18.md)
remains implementation preparation until execution ratification.
