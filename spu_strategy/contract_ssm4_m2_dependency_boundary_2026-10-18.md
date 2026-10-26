# SSM-4-M2: execution dependency boundary proposal

Date: 2026-10-18. Status: READ-ONLY CLASSIFICATION COMPLETE; amendment NOT APPROVED.
No implementation, current inventory, qualification runner or campaign is changed.

## 1. Review and verify the proposal first

Run from the repository root; this checks inventory data without executing tests:

```bash
python3 build/ssm4/m2_dependency_classification_20261018_01/verify_proposal.py
sha256sum -c build/ssm4/m2_dependency_classification_20261018_01/evidence.sha256
```

Inspect `classification_55.json`, `script_edges.json`, `dynamic_discovery.json`,
`proposed_source_set.json`, `proposed_research_domain.json`,
`proposed_execution_manifest.json`, `proposed_boundary_conditions.json`,
`environment_review.json` and `verification.json` in that evidence directory.
These are review candidates, not installed manifests or execution qualification.

## 2. Classification result and call graph

All 55 paths are CONDITIONALLY REACHABLE — INCLUDE. Each resolves to an existing
file and a child process invocation in `run_all_tests.py`; records identify the
literal reference, subprocess line and enclosing/preceding skip guards. No path
is justified as an unreachable reference. No execution was observed or inferred:
the campaign has not run. Earlier successful gates and reaching each block are
conditions of every downstream invocation.

File-existence guards currently select all 55. Loop-based calls check existence
and continue when missing. Do not convert that possibility into an exclusion;
freeze membership and hashes or reject drift before execution. The Vulkan child
script is reachable even when it later skips device dispatch. Its optional GPU
branch remains in the proposed source boundary.

The planned call graph is:

```
detached launcher -> worker -> run_elapsed_deadline.py -> check_repo.sh
  -> SSM-4 source/ancestry/capture/verify/comparison and unittest discovery
  -> SG-0 / SSM-3 / projection focused tests
  -> GPU S1/S2/S3 and named trace/math tests
  -> tools/verify_repo.sh -> run_all_tests.py
       -> discovered Verilog benches -> Icarus/vvp or Verilator/make fallback
       -> discovered C++ tests -> compiler/generated executables
       -> selected Python children -> imports, helpers, generated test programs
       -> optional Vulkan compiler/host/shader branch
```

Read-only discovery finds 173 Verilog bench files and 12 C++ entry files before
parameter variants. These counts are source-discovery counts, not a projected
suite pass total. `script_edges.json` records 285 import statements and 59
process/dynamic-load call sites in the 55 scripts; they are potential edges, not
observed dispatches or a proof of all dynamic Python behavior.

## 3. Proposed complete repository boundary and counts

Use a conservative repository-tree superset rather than another list of guessed
leaf dependencies. Capture regular files under `software`, `hardware`, `tools`,
`fixtures`, `examples`, `knowledge`, `research`, and `photonics`. Add the existing
238-entry inventory, tracked Markdown read by the citation gate, root policy and
configuration files, root memory tables, and exact discovered Verilog/C++ inputs.
Keep `hardware/archive` library sources: excluding archived tests from discovery
does not exclude library files searched by the compiler.

Exclude generated/cache/VCS directory components `.git`, `.venv`, `__pycache__`,
`.mypy_cache`, `.pytest_cache`, `build`, and `node_modules`. Retain explicitly
declared qualified SG-0 inputs under build via the existing inventory. Also
exclude SSM-4's own future `research/ssm4/provenance/` output to prevent recursive
self-capture. Other historical input archives are conservatively included.
Current selection contains zero symlinks. A newly encountered link must stop
capture for explicit review, not silently follow a new external source.

Snapshot counts:

| Set | Files |
|---|---:|
| Existing mixed implementation/execution inventory | 238 |
| Proposed execution additions | 1,950 |
| Complete proposed union | 2,188 |
| Behavior-defining research-domain subset | 148 |

The union is 75,926,095 bytes at this snapshot. Every entry records exact path,
SHA-256, byte size and mode. The broad superset intentionally includes unused
neighbors; inclusion is not an assertion that every file executes.

Separate the two roles without discarding the current compatibility inventory:

- Research manifest: 148 behavior-defining implementation, proof/recipe input,
  reference and SG-0 handoff entries. It is a subset of the execution envelope.
- Execution dependency manifest: the full 2,188-entry bounded union, including
  research overlap, tests, runners, compiler inputs and relevant configuration.

`proposed_research_manifest.json` is an intermediate copy of the legacy 238-entry
set, not the new 148-entry research-domain split. Use
`proposed_research_domain.json` for that split. `proposed_execution_additions.json`
lists the 1,950 additions separately for review.

These are exact reviewed snapshot counts, not permission to auto-expand. A new
file, source change, different discovery result or staged Markdown change before
the final capture requires an explained delta and refreshed review identities.

## 4. Proposed environment and generated-artifact boundary

The existing runner inherits environment. M2 must enforce rather than assume:
SKIP_TESTS unset/0; TB_FILTER unset/empty; PYTHONPATH/PYTHONHOME/LD_PRELOAD unset;
the runner's bytecode/unbuffered settings; and the two declared capture hash seeds.
Record resolved tool paths/availability/content hashes and relevant library/Vulkan
configuration at freeze and reject unexpected drift. The observation pack hashes
12 tool executables where available; no GPU probe or toolchain test was run.

Include both Icarus and reachable Verilator fallback inputs. Include Vulkan host
and shader inputs regardless of current device availability. Report a later
conditional skip explicitly; do not count it as device execution.

Generated executables, temporary benches, frame outputs and caches are outputs,
not arbitrary pre-existing trusted inputs. Require the existing fresh campaign
paths and declare/hash any build input actually reused; generated recipes and
source inputs must be retained. Record Git HEAD/index and tracked Markdown diff
state because the hygiene gate depends on them. A source hash alone does not
freeze a discovery set or the citation gate's inputs.

External Python/system libraries, compiler runtime and Vulkan driver remain
environment dependencies. This proposal is a bounded repository source closure
plus explicit environment attestation, not a hermetic OS image, independent
hardware qualification or complete external-library restoration claim.

## 5. Proposed M2 implementation amendment — not authorized by this document

Limit executable changes to `research/ssm4/sources.py`, within the existing
150-line module limit. Preserve SSM-4 math, fixtures, all expected outcomes,
predecessor identities and exact `check_repo.sh`. If that limit requires a new
module or another edit, stop and review the changed path/count budget first.

Replace leaf-only capture with the reviewed boundary selection and two manifest
roles. Keep `sources.json` as the complete path-to-hash union for compatibility;
store research/execution metadata separately and preserve both inside the source
archive and artifact digest set. Generated provenance files are excluded from
the source selection. Compare contents, modes AND membership at entry and exit.
Recompute the exact discovery sets and validate environment/tool identities.

Implement only after approval. Then run bounded source-closure checks, including
omitted Python/HDL/C++/deadline-helper controls, new discovery member, removal,
mode drift, symlink, changed imported helper, environment bypass, optional tool
identity change and recursive-provenance exclusion. Do not run the qualification
suite for these checks. Recheck SG-0's 159 and SSM-3's 75 preserved identities.

The current snapshot hashes are provided for every existing input. The approved
future edit to sources.py necessarily has a new digest; show that exact diff and
digest before final freeze rather than pretending today's digest is executable
evidence for unimplemented M2 code. No new source paths are proposed, so the
reviewed source-set count remains 2,188 unless an explicitly reviewed delta occurs.

Only after those checks pass should final capture be approved and the exact
1800-second campaign command reviewed. This read-only tranche grants neither
source edits nor campaign launch. Attempts consumed remain 0/1.

## 6. Preparation verification and limitations

The proposal checker verified all 2,188 file hashes/sizes/modes, 55 classified
script identities, all discovered entry files and four representative omission
controls. SG-0 159, SSM-3 75 and the current 238-entry inventory match their
prior identities. These checks validate the proposal data, not a future guard
implementation or the qualification tests.

The initial failed-preparation raw log remains missing and disclosed; its
failure.json and labelled excerpt are retained. The separately recorded 18/18
corrective PASS remains valid. No failure record is reinterpreted or discarded.
No final source freeze, source-manifest installation, main regression, framebuffer
replay, hardware operation or qualification launch was performed here.
