# QCG-W31-I1-R1 three-defect repair

Date: 2026-10-23. **Repair verification PASS; execution HOLD pending separate independent review and authorization.**
No remaining repair blocker observed. Actual registered workload outcomes remain unmeasured.
This report supersedes the earlier implementation-readiness claim for the repaired identity only; it is not an execution-readiness certificate.

## Preserved and repaired identities

Reviewed baseline commit: `c261820b5e68e2ddf23488cd6ddc2a556f325301`.
`SOURCE_INPUTS.sha256` remains byte-identical, SHA-256 `4a06969a253844878e98484920c80cf5fb631038534b92c5691f1e37c9e703be`. It is historical and is not reinterpreted as the repaired inventory.
The launcher, authorization fingerprint and future derivation certificate now use `SOURCE_INPUTS_R1.sha256`, SHA-256 `b9c4adadd7cf7168cda3b85f67687facce818ed799ca914532be1a1bff5cff9e`.
The repaired inventory covers all 17 Python sources, the unchanged input manifest, the 11 unchanged handoff inputs and the preserved reviewed inventory (30 entries). It excludes itself and this narrative report.
`INPUT_MANIFEST.json` remains unchanged, SHA-256 `8fb53298611b755cb91fe6f1d075d38622e0d5c33a04e409a5a591a3b2e65cfa`.
No authorization file was created; an authorization bound to the old inventory would fail the repaired launcher's fingerprint gate.

## R1 — unconditional checks

`w31_verify.py` provides explicit fail-closed checksum and manifest checks. Launcher source checks, input identities, tool versions, namespace/rlimit checks, table validation and refusal-state invariants use unconditional errors instead of security-critical asserts.
Synthetic negative controls reject both a modified inventory and a modified inventoried payload under explicit `-O` and independently under `PYTHONOPTIMIZE=2`; intact controls pass. No frozen inventory or input is mutated by these tests. Arithmetic foundation assertions are confined to its synthetic `__main__` checks, not a launch/completion gate.

## R2 — certified grid/value gate

Required numerical input exists and matches the contract pin:
`research/qcg_0/QUINTIC_FIXTURE_VALUES.json`, SHA-256 `8827ac9e4b9a343f1c5481f1a99211673c0805e16534e361598aff2c28354b34`.
Its `sequential.PH3`, `sequential.PH5` and `cell_B.rows` are the contract's certified numerical rows. No candidate input is used.
Preflight checks reference identity and required shape. The launcher mounts only this numerical reference read-only at `/references/QUINTIC_FIXTURE_VALUES.json`. The registered entry rechecks its hash, and must pass `check_certified` before writing artifacts or RUNNER_DONE.
Successful issued samples are checked against certified position, derivative, speed, tangent and curvature rows; the expected (Nk,Dk) pair is mapped by the contract's uncounted Fraction oracle rule Dk=sigma_ref², Nk=kappa_ref·Dk. The diagnostic S value is checked against the certified S polynomial. Grid parameters are checked against both certified row parameters and k/16. Cell B checks the seven certified values and monotonicity flag. S3 increments are checked only when their ending request succeeded. Reference values are never copied into refused/unissued or unavailable outputs.
Missing files, wrong hashes, missing fields and numerical mismatches prevent completion. Synthetic tests cover wrong values, wrong row parameters, a wrong grid despite a matching synthetic reference parameter, Cell B mismatch, and an exact missing-reference HOLD diagnostic. No registered numerical gate or interpreter workload was executed during repair.

## R3 — export-only S3 convention

The arithmetic program and event generation in `w31_sequential.py` are byte-identical to the reviewed source. Scheduler dependency classification and request execution order are unchanged.
`w31_routes.export_s3` only relabels the already computed delayed scalar: exported qNN `increment_to_next` comes from successful q(NN+1); q16 is null if q16 itself succeeded. The arithmetic remains charged to the ending request under a12/b22/c15. Export introduces no counted operations or events and changes no state hash, ledger, request status or refusal event.
If the ending request refuses, the earlier successful sample has `increment_available=false` and no increment payload; it is never populated from a certified row or falsely represented as terminal null. Refused requests have no values; later dependent requests retain their existing NOT_ISSUED representation.
Synthetic tests exercise q00/q15/q16 for all eight arms, compare exported ledgers with the original evaluator's counts, and force actual increment e1 refusals at q02 and q16. They check rollback, unchanged ending-request attribution, unavailable intervals and the existing NOT_ISSUED rules.

## Exact changed paths

- `research/qcg_0/w31_derivation_prelim/derive_w31.py` (modified)
- `research/qcg_0/w31_derivation_prelim/launch_w31.py` (modified)
- `research/qcg_0/w31_derivation_prelim/test_w31_controls.py` (modified)
- `research/qcg_0/w31_derivation_prelim/test_w31_synthetic.py` (modified)
- `research/qcg_0/w31_derivation_prelim/w31_routes.py` (modified)
- `research/qcg_0/w31_derivation_prelim/w31_table.py` (modified)
- `research/qcg_0/w31_derivation_prelim/w31_verify.py` (added)
- `research/qcg_0/w31_derivation_prelim/w31_certified.py` (added)
- `research/qcg_0/w31_derivation_prelim/test_w31_r1_integrity.py` (added)
- `research/qcg_0/w31_derivation_prelim/test_w31_r1_values.py` (added)
- `research/qcg_0/w31_derivation_prelim/test_w31_r1_export.py` (added)
- `research/qcg_0/w31_derivation_prelim/SOURCE_INPUTS_R1.sha256` (added)
- `research/qcg_0/w31_derivation_prelim/REPAIR_R1_REPORT.md` (added)

## Verification

All invocations were bounded synthetic tests or non-launching verification:

```bash
/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- python3 -B -m unittest discover -s research/qcg_0/w31_derivation_prelim -p 'test_w31_*.py'
/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- python3 -O -B -m unittest discover -s research/qcg_0/w31_derivation_prelim -p 'test_w31_*.py'
/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- env PYTHONOPTIMIZE=2 python3 -B research/qcg_0/w31_derivation_prelim/launch_w31.py --preflight
sha256sum -c research/qcg_0/w31_derivation_prelim/SOURCE_INPUTS_R1.sha256
git diff --check -- research/qcg_0/w31_derivation_prelim
```

Results: 26 tests PASS normally and 26 PASS under -O; optimized preflight PASS; all 30 repaired inventory entries PASS; whitespace check PASS. No timeout or retry occurred. Original reviewed inventory preservation and unchanged arithmetic/arm-program identities were checked separately.
No candidate path or candidate evidence was consulted. No contract, ISA, RTL, CI or shared infrastructure was changed. No actual W31 derivation, actual stage table or authorization file was produced. No attempt directory exists; attempts consumed remain **0/3**. Candidate, contract freeze and P0 execution remain HOLD.

## Complete Python source hashes

| Source | SHA-256 |
|---|---|
| `derive_w31.py` | `15cce316f08fb711cfe36df2ed7e623b174958d5bc91cd8a827125e389985a9e` |
| `launch_w31.py` | `eab5f0f6a82fd2fc749dd177f41aedfc270fbc353f52d609fd5b3cf5eea1c829` |
| `test_w31_boundaries.py` | `3320ddcf8c52a1015b613867b16ce6ecc3d1b77224bac59649df5cd74919cba1` |
| `test_w31_controls.py` | `40a440d09502ba36aac7cebc1a41b794aeab9344e8af4795707351a6bcd8b5fd` |
| `test_w31_r1_export.py` | `d136da76b02c43bed900fdfb16049a91bf7b6908fbffb3b9fe58d60dad03b16c` |
| `test_w31_r1_integrity.py` | `a4ba13efae7031594c03ca2b8d726b8a5e8b3128b20c5d82ba8332ba596d267b` |
| `test_w31_r1_values.py` | `b4750098f32cb6ee1e1c32a68a17cf0853cdea19304318c35c4b47dd32b98f97` |
| `test_w31_synthetic.py` | `7b97b083366d0334c57fb3db02b0dd4e431ca700fcb69a30d8988d21e1c8a9eb` |
| `w31_arithmetic.py` | `464afe1654c2ca7b285cddf269209e7abe680ecf117b20ab44a54488d7f2df27` |
| `w31_cell_b.py` | `1e473325fc945e6100e08669c2289c017013e2890a7e7b7e3f29c5eccc2dc8de` |
| `w31_certified.py` | `7f2b7bb7d1e1a775d59082014385a0b1a8d63f2cc59dc27df21f90f94edbd408` |
| `w31_poly.py` | `6cb180a034cb9420ebea8089e457dcea447062997c2ebfc200c825f391149620` |
| `w31_prepare.py` | `929cd77a8ce5734fd27d9d704d4d2a5ff19a466d6a9fe67faf549addba760c52` |
| `w31_routes.py` | `bc8d518e47583c0733a21e813efc3a6a54744e42af8e605cbbc991ef11633c47` |
| `w31_sequential.py` | `1e45fe7af2b380b1532d7d219c14840c6f1d345f4ab241240658d516963f813a` |
| `w31_table.py` | `f1690cc27bd71b89fead0e7571635fa1e42b236dd86f4eb61d3586b755f504f5` |
| `w31_verify.py` | `21e4155a23c844bd1352ca410996c3d12b2b6a9df36a96afc68381484ffbbf52` |
