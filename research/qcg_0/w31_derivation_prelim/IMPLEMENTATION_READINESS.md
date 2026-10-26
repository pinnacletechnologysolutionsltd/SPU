# QCG-W31-I1 implementation readiness

Date: 2026-10-23. Independent author: ChatGPT. **PASS — implementation readiness.**
Implementation blockers: none found by source inspection, 18 synthetic tests and the non-launching environment preflight.
Registered derivation remains **HOLD for separate owner authorization**. Attempts consumed: **0/3**.
No registered preparation, sequential route or Cell B workload was executed. No actual W31 stage tables or derivation certificate were generated.
The earlier `INTERPRETER_PREPARATION_STATUS.md` is preserved as a historical preliminary record; this record supersedes its implementation checklist only.

## Implementation and evidence boundary

`w31_arithmetic.py` implements exact Q and ordered W31 raw/reduced checks, primitive counts and diagnostic width costs.
`w31_poly.py` implements the frozen primitives and shared counters for nested operations.
`w31_prepare.py`, `w31_sequential.py` and `w31_cell_b.py` implement the eight sequential and five Cell B programs.
`w31_routes.py` provides transactional state, append-only per-request diagnostics, scheduling, canonical rational pairs and state hashes.
`w31_table.py` checks the versioned JSON table structure. These sources implement stage derivation; they are not the P0 performance/comparator implementation or simulator qualification.

The registered entry is isolated in `derive_w31.py`; it has not been invoked.
Its manifest contains literal registered inputs transcribed from pre-registration §§9.1/9.2 and the contract, not computed outcomes.
The 11 handoff document/reference hashes match the intake identities. The allowed certified references were used only as independent inputs; no candidate source, tests, output, evidence or refusal event was consulted.

Sequential FD tables advance in the selected §5 order before scalar sample arithmetic; their events keep the named a/b steps.
S3 computes the preceding interval's increment when its ending sample exists: the output `increment_from_previous` at qNN represents inc_(NN-1), is null at q00, and is charged inside the issued ending-sample request under a12/b22/c15. No increment is manufactured after a failed ending sample. This preserves §3 request atomicity and the §5 delayed increment schedule.
A preparation failure is recorded separately with `PREPARATION_REFUSED` (or `PREPARATION_INVALID`) and prevents route issuance; it is never fabricated as a q00 arithmetic result.

## Frozen sources and inputs

Complete checksum-only source/input inventory: `SOURCE_INPUTS.sha256`.
Inventory SHA-256: `4a06969a253844878e98484920c80cf5fb631038534b92c5691f1e37c9e703be`.
Input manifest: `INPUT_MANIFEST.json`, SHA-256 `8fb53298611b755cb91fe6f1d075d38622e0d5c33a04e409a5a591a3b2e65cfa`.
The inventory covers every interpreter, launcher and synthetic-test source, the input manifest and all 11 handoff inputs. It excludes itself to avoid circularity.

| Source | SHA-256 |
|---|---|
| `derive_w31.py` | `515ca9446fc90ee6b25535fe1702b48ab5a7fe373824ecfb56ec99f934ad2646` |
| `launch_w31.py` | `bdf8c7ac3bd4faa1d6d3c49629f7ffe2ed63266af0b65674895d4e7131983252` |
| `test_w31_boundaries.py` | `3320ddcf8c52a1015b613867b16ce6ecc3d1b77224bac59649df5cd74919cba1` |
| `test_w31_controls.py` | `b67c95ebac49f91db7f5f36c408d70c239b77223254a0d79dd1a2de07d1d58ef` |
| `test_w31_synthetic.py` | `3a6e18e57246f3354f29006c1e8f8eaeb319fe9feae362986756f17e00abb7e6` |
| `w31_arithmetic.py` | `464afe1654c2ca7b285cddf269209e7abe680ecf117b20ab44a54488d7f2df27` |
| `w31_cell_b.py` | `1e473325fc945e6100e08669c2289c017013e2890a7e7b7e3f29c5eccc2dc8de` |
| `w31_poly.py` | `6cb180a034cb9420ebea8089e457dcea447062997c2ebfc200c825f391149620` |
| `w31_prepare.py` | `929cd77a8ce5734fd27d9d704d4d2a5ff19a466d6a9fe67faf549addba760c52` |
| `w31_routes.py` | `c4a270b53e65ae66b8ad6c681e9b2b61c53ffc327d0e62312faf250f8ce75c70` |
| `w31_sequential.py` | `1e45fe7af2b380b1532d7d219c14840c6f1d345f4ab241240658d516963f813a` |
| `w31_table.py` | `52f81c0e09d8a62ce41ef3d0480865fede363a308cba2f42d20793d103e7ae7c` |

## Exact commands — no derivation launched

Preparation verification (executed, 18 tests PASS):

```bash
/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 -- python3 -B -m unittest discover -s research/qcg_0/w31_derivation_prelim -p 'test_w31_*.py'
python3 -B research/qcg_0/w31_derivation_prelim/launch_w31.py --preflight
sha256sum -c research/qcg_0/w31_derivation_prelim/SOURCE_INPUTS.sha256
git diff --check -- research/qcg_0/w31_derivation_prelim
```

Future derivation entry command, **not executed** (working directory `/home/user/Projects/hardware/SPU`):

```bash
/usr/bin/python3 -B research/qcg_0/w31_derivation_prelim/launch_w31.py --attempt 1 --authorization-file build/qcg_0/w31_authorization_01.txt
```

The authorization file does not exist as part of this preparation. Only after separate owner authorization may it be created, containing exactly:

```text
GO QCG-W31 DERIVATION
source_manifest_sha256=4a06969a253844878e98484920c80cf5fb631038534b92c5691f1e37c9e703be
attempt=1
```

The launcher freezes its complete child argv in `launch.json` before execution. Its child starts with `/usr/bin/timeout 30 /usr/bin/prlimit --as=1073741824:1073741824 --fsize=4194304:4194304 --`, then Bubblewrap, then `/usr/bin/python3 -I -B /work/derive_w31.py --bounded-authorized-entry`.
Tool versions are frozen in `INPUT_MANIFEST.json`; the namespace/resource preflight passed on this host. The preflight executes only a synthetic namespace/rlimit assertion, never the registered entry. Python: 3.14.8; host: Linux-7.2.7-1-cachyos-x86_64-with-glibc2.44.

## Enforcement and terminal evidence

- GNU timeout owns the external 30-second deadline; the runner has no SIGTERM handler and never returns 124. Only supervisor return 124 permits TIMEOUT. Kernel kills and other exits are FAILED.
- Hard RLIMIT_AS = 1 GiB and hard RLIMIT_FSIZE = 4 MiB apply before the namespace/runner. The probe verified both soft/hard limits. Runner writes are additionally bounded to 4 MiB/file and 8 MiB total; finalization checks 10 MiB with 4 KiB reserved metadata. Output-cap events force FAILED.
- Bubblewrap creates a fresh network namespace. The probe found only its down loopback interface. Only system runtime paths and this independent source directory are read-only mounted, plus the exclusive output leaf; the candidate tree is absent. No installs or network calls occur.
- No automatic retry, timeout extension or budget widening. Explicit attempt numbers must increase monotonically and existing attempt directories cannot be reused. Each future invocation needs authorization bound to that attempt and this source inventory.
- `build/qcg_0/w31_independent/attempts.jsonl` is append-only under an exclusive lock, flushed/fsynced. Exclusive `attempt_NN` directories are authoritative consumed slots, including interrupted/unavailable launches. A failure after reserving a slot consumes it. Maximum 3 slots; none created during preparation.
- One finalization path writes required terminal metadata and the append-only journal terminal record before creating a marker. Metadata/journal failure forces FAILED. Exactly one COMPLETE/FAILED/TIMEOUT marker is required; otherwise RESULT_UNAVAILABLE. COMPLETE additionally requires exit zero, unchanged pins, no cap breach and RUNNER_DONE. The runner writes table hashes and the reviewer certificate before RUNNER_DONE and has no access to candidate results.

Synthetic tests cover all sequential arms and tapes on nonregistered linear/nonlinear curves, five Cell B arms with a nonregistered retiming, polynomial operation counts/values, nested counters, every raw/reduced check class, zero-divisor precedence, refusal recovery/repeat, rollback, q02 scheduling, namespace construction and terminal failure modes.
A boundary test initially used a denominator rescued by the specified parity shift; the fixture was corrected. No registered workload was used to debug implementation.
Full repo/ROTC/math/FPGA gates were not run: changes are isolated exploratory reference software under the approved scope and research execution policy, with no shared infrastructure, RTL, ISA or arithmetic-kernel changes.

PASS is limited to implementation readiness from synthetic verification. Actual registered arithmetic outcomes, full table validation on those outcomes and independent comparison remain unmeasured and require the separate bounded derivation GO.
