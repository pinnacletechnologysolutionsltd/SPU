# SSM-4 frozen input copies

The seven JSON files are exact copies of the ratified preparation pack at
`spu_strategy/ssm4_preparation_2026-10-18/`: six SSM-3 proofs and four affine
recipe vectors. The original pack remains unchanged. Historical metadata such
as `implementation_status: NOT_STARTED` describes fixture creation, not current
SSM-4 execution status; see the [implementation README](../../research/ssm4/README.md).

Run from repository root:

```bash
sha256sum -c fixtures/ssm4_v1/SHA256SUMS
```

Change no proof, expected outcome or recipe to accommodate an implementation.
