# QCG-W31-I1-R2 — outer launcher isolation repair

**Repair verification PASS; execution HOLD for independent R2 review and separate authorization.**
Predecessor: local commit `549e24974da85f336700a70e06dbe07ca299c764`. No commit, tag or push was made.

## Repair and frozen entry

The outer interpreter must start with `-I -S -B`: -I ignores Python environment paths and user-site packages; -S suppresses all site initialization, including sitecustomize/usercustomize; -B suppresses bytecode writes. Before importing verification code, the script checks these interpreter flags using built-in sys alone and rejects unsafe startup. It also checks startup again on entry to main.
After importing its standard-library dependencies, it appends only its resolved source directory to the isolated runtime search path. Standard-library paths retain precedence. This restores legitimate w31 imports without importing caller-controlled Python paths.

This is the current frozen future command, **not executed**, from `/home/user/Projects/hardware/SPU`:

```bash
/usr/bin/python3 -I -S -B research/qcg_0/w31_derivation_prelim/launch_w31.py --attempt 1 --authorization-file build/qcg_0/w31_authorization_r2_01.txt
```

Earlier nonisolated entry commands are superseded. No authorization file exists as a result of this repair. The existing authorization format, exact fingerprint matching, monotonic slot rules and attempt paths are unchanged; the fingerprint and future certificate now bind SOURCE_INPUTS_R2.sha256.

## Predecessor and R2 identities

R1 SOURCE_INPUTS_R1.sha256 is preserved byte-for-byte: `b9c4adadd7cf7168cda3b85f67687facce818ed799ca914532be1a1bff5cff9e`.
The original SOURCE_INPUTS.sha256 is also unchanged: `4a06969a253844878e98484920c80cf5fb631038534b92c5691f1e37c9e703be`.
Separate R2 inventory: **`2269d198859785d21e50bdf3957c41b769f89f4b024593f86a4993222c1e4f8c`** (SHA-256 of SOURCE_INPUTS_R2.sha256).
Its 32 entries cover all 18 Python sources, unchanged inputs/manifest and both predecessor inventories. It excludes itself and this narrative report. Complete source hashes are in that inventory; changed Python source hashes follow.

| Source | SHA-256 |
|---|---|
| `launch_w31.py` | `e628a039364992051f5b55675a1a06cf523bd8a0963615083c4afe51eacc3d52` |
| `derive_w31.py` | `1e19b3427081908978d73934127b4dadde01fdc856d03b318c9552d3bdd6daaf` |
| `test_w31_r2_startup.py` | `1e0a00ca8b83aeee4f00b4b26a95f30a3bcb5f68e4382fb45ea50d5c989fa1ce` |

## Exact changed paths

- `research/qcg_0/w31_derivation_prelim/launch_w31.py` (modified)
- `research/qcg_0/w31_derivation_prelim/derive_w31.py` (modified)
- `research/qcg_0/w31_derivation_prelim/test_w31_r2_startup.py` (added)
- `research/qcg_0/w31_derivation_prelim/SOURCE_INPUTS_R2.sha256` (added)
- `research/qcg_0/w31_derivation_prelim/REPAIR_R2_REPORT.md` (added)

## Verification

```bash
/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- python3 -B -m unittest discover -s research/qcg_0/w31_derivation_prelim -p 'test_w31_*.py'
/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- python3 -O -B -m unittest discover -s research/qcg_0/w31_derivation_prelim -p 'test_w31_*.py'
/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- env PYTHONOPTIMIZE=2 /usr/bin/python3 -I -S -B research/qcg_0/w31_derivation_prelim/launch_w31.py --preflight
sha256sum -c research/qcg_0/w31_derivation_prelim/SOURCE_INPUTS_R2.sha256
git diff --check -- research/qcg_0/w31_derivation_prelim
```

Results: **29 tests PASS normally; 29 PASS under -O; optimized non-launching preflight PASS; 32/32 inventory hashes PASS; whitespace check PASS.**
New controls first reproduce invalid-checksum acceptance through malicious PYTHONPATH and user-site startup hooks without isolation, then reject modified synthetic inventories and covered payloads under isolated normal and optimized execution. Positive real-preflight controls pass with the same hostile environment and an injected verifier module present. Missing authorization still rejects before any attempt directory is created; unsafe flag combinations reject before verification imports.
Certified numerical checks, certified reference bytes, S3 exports, arithmetic and scheduler sources are byte-identical to R1. The registered entry differs only in its certificate inventory filename. AST comparison confirms resource sandbox/preflight/finalization functions are unchanged; authorization/accounting main is unchanged except the startup check and R2 inventory name. No existing check was removed or weakened.

No remaining repair blocker observed. These are implementer-reported synthetic results, not an independent R2 acceptance certificate. No candidate access, contract changes, registered derivation, registered tables, authorization creation or registered attempt occurred. Attempt directory is absent; **0/3 consumed**. QCG-0 P0 remains HOLD. Stop here for independent review.
