# SPU-13 Engineering & Governance Contract

This file defines the mandatory engineering constraints, functional agent roles, and verification gates for the SPU codebase. It is loaded as the root engineering contract.

---

## Development Ethos

**Make experiments cheap, conclusions rigorous, and releases dependable.** The SPU is an experimental mathematical computing architecture; this repository is a research workshop. The simulator, hardware releases and public tools are separate deliverables with stronger standards. Rigor is proportional to the consequence of the work, not to the number of commands run; it is never weakened for convenience. Classes A/B/C and their execution limits are defined only in [`spu_strategy/RESEARCH_EXECUTION_POLICY.md`](spu_strategy/RESEARCH_EXECUTION_POLICY.md) (AGENTS.md §4.3), which is authoritative; this section redefines neither. Emphasis by class:

* **A:** keep experiments small and reproducible; record hypothesis, baseline, result and limitations; keep informative negative results; close an investigation when its question is answered. A result is not an architectural guarantee.
* **B:** keep changes isolated, attributable and in small reviewable commits; run the relevant targeted tests and required regressions (§4); do not mix workstreams.
* **C:** frozen specifications, explicit acceptance criteria and strong provenance; report simulation, synthesis, timing closure and physical validation separately.

Operating rules:

* Execute an already-authorized task rather than proposing another preparation stage; finish its ordinary steps without re-asking permission. Running an isolated Python experiment does not need the procedure of an RTL, ISA or FPGA change.
* Do not repeat completed audits or ask what repository evidence already answers. Escalate only genuinely unresolved decisions, conflicts or risks.
* Add gates, campaigns or documents only when they materially improve correctness or reproducibility.
* Keep research findings distinct from qualified implementation claims.
* Frozen contracts, attempt/budget limits, explicit HOLD decisions and authorization boundaries always take precedence.

## 1. System Context & Tech Stack

* **Architecture:** SPU-13 (13-axis cuboctahedral manifold cortex) & SPU-4 Sentinel (4-axis Quadray satellite/edge node).
* **Exact Arithmetic Domains:** Bit-exact, deterministic arithmetic over $\mathbb{Q}(\sqrt{3})$, $A_{31}$, and $\mathbb{Z}[\varphi]/L_p$ (Lucas Phinary). **$A_{31}$ is an algebra, not a field** — the 4-dimensional split biquadratic algebra $\mathbb{F}_p[x,y]/(x^2-3,\,y^2-5)$ over $p = M_{31}$, with basis $[1, \sqrt{3}, \sqrt{5}, \sqrt{15}]$. Because 3 and 5 are both quadratic non-residues mod $M_{31}$, their product 15 is a residue, so $\sqrt{15}$ already lies in $\mathbb{F}_p$ and the extension **splits**: $A_{31}$ contains zero divisors and not every non-zero element is invertible. The hardware traps these via `FLAGS.V`. See `knowledge/MATHEMATICAL_FOUNDATIONS.md` §8.3 and the `A₃₁` entry in `knowledge/SPU_LEXICON.md`.
* **Hardware Toolchain:** Verilog HDL with OSS CAD Suite (Yosys + nextpnr-himbaechel). Primary hardware targets: Tang Primer 25K (probe/bring-up) and Wukong Artix-7 100T (silicon evidence).
* **Software Toolchain:** Python 3.10+ (emulator, oracles, assemblers), C++17 (oracle bit-parity).
* **Design Rule:** Single-purpose "Lithic" modules (50–150 lines). Split concerns rather than growing oversized files.

---

## 2. Functional Roles & Governance Protocol

Engineering tasks follow a portable, 3-role governance protocol (any tool or human can fill any role):

1. **Spec Author (Strategist / Drafter):**
   * Formulates mathematical representations, architectures, and contract specifications.
   * Drafts machine-actionable contracts in `spu_strategy/` using [`spu_strategy/contract_template.md`](knowledge/contract_template.md).
   * **Rule:** Must write command-first instructions with exact shell invocations; zero speculative prose.

2. **Halt-and-Flag Implementer (Analytical Reviewer & Coder):**
   * **Pre-Execution Review (Halt & Flag):** Inspects incoming specs for unhandled edge cases, clock/timing hazards, or logical contradictions. If a defect is found, **HALT immediately and flag the flaw** with a minimal proposed correction rather than implementing broken logic or silently rewriting the architecture.
   * **Precision Execution:** Executes surgical, literal code edits (50–150 line Lithic modules) strictly within the defined scope.
   * **Rule:** Zero speculative abstractions or out-of-scope refactorings.

3. **Integration Auditor (Verification & Repo Gatekeeper):**
   * **Automated Gatekeeper:** Runs deterministic verification via `bash tools/verify_repo.sh`.
   * **Integrity Gate:** Validates that any "silicon-verified" claim cites [`docs/hardware_evidence.md`](docs/hardware_evidence.md).
   * **Hygiene Enforcement:** Sweeps untracked temporary files (`tmp_*`, `scratch_*`, root `.vcd` dumps).

---

## 3. Hard Constraints (The "Never" List)

1. **NO Floating Point or Runtime Division Operators in RTL:** Synthesizable RTL must not use runtime `/` or `%` operators or infer divider/modulo hardware. Exact quotient generation using bounded shift, compare, and subtract algorithms is permitted only under a reviewed algorithm contract. Binary GCD and quotient generation must preserve exactness and verify zero remainder before commit. All arithmetic is exact in $\mathbb{Q}(\sqrt{3})$, $A_{31}$, or $\mathbb{Z}[\varphi]/L_p$.
2. **NO Branches in Hot Paths:** Control flow compiles to multiplexer Boolean polynomials.
3. **NO Unbacked Silicon Claims:** Never claim a feature is "silicon-verified" unless backed by a specific entry in [`docs/hardware_evidence.md`](docs/hardware_evidence.md). Otherwise, state `testbench-verified`, `simulation-only`, or `unmeasured`.
4. **NO Manual Edits to Generated Files:** Never hand-edit `software/lib/irotc_catalog.py`, `spu13_irotc_codes.mem`, `spu13_irotc_golden.mem`, or `rplu2_boot_tables.bin`. Always run their generator scripts.
5. **NO Vacuous Assertions:** Testbench assertions must be falsifiable (cannot assert against constants or untoggled signals).
6. **NO Root Directory Clutter:** Temporary scripts, waveform dumps (`*.vcd`), and test binaries must never be committed to the root directory.

---

## 4. Mandatory Verification Commands

Before declaring any task complete or committing changes, execute the required gates:

```bash
# 1. Automated Repo Hygiene & Regression Gate (Runs full suite + citation checks)
bash tools/verify_repo.sh

# 2. Scoped Triage Gate (during active development; legacy discovery, not release results.
#    The release gate is the unfiltered default run, driven by tools/release_tests.txt)
TB_FILTER=<subsystem_prefix> python3 run_all_tests.py

# 3. ROTC / IROTC Trace Equivalence Gate
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py

# 4. Math Oracle & Parity Gates
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py

# 5. FPGA Synthesis Check (Artix-7 100T Padé build)
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

### 4.1 Scope-Specific Verification

The full gates above apply when a change affects RTL, hardware behavior,
arithmetic kernels, shared test infrastructure, or the repository-wide
verification runner. Use the following focused gates for changes that stay
inside these narrower scopes:

* **Documentation and navigation only:** run
  `python3 tools/doc_audit.py --actual-pass 238`, execute any changed
  user-facing commands, and run `git diff --check -- <changed paths>`.
* **Filesystem metadata or build-inventory tooling only:** run
  `python3 software/tests/test_build_artifact_inventory.py`,
  `python3 tools/build_artifact_inventory.py --help`, and
  `git diff --check -- <changed paths>`. The fixture test must cover hidden
  paths, symlinks, counts, repeated-name/size candidates, and output refusal.
* **Offline T1d evaluator or its user path:** run the focused S1, S2, and S3
  tests (`test_gpu_scene_compiler_s1.py`, `test_gpu_device_model_s2.py`, and
  `test_gpu_pixel_inspect_s3.py`) and execute the documented preview/edit/
  inspect commands. Do not run unrelated ROTC/math gates or FPGA synthesis
  unless the change also affects those systems.

When a change crosses scopes, use the union of their focused gates. Changes to
RTL, hardware build flows, arithmetic kernels, or shared verification
infrastructure retain the full gates in §4, including the Artix-7 synthesis
check where applicable.

### 4.2 Long-Running Tool Jobs

For synthesis, place-and-route, full regressions, and other long-running tools:

* Do not make an agent session own the lifetime of deterministic work expected
  to exceed 60 seconds. Launch it through the repository's detached runner:

  ```bash
  tools/run_detached_job.sh \
    --output build/<board>/<ticket-or-purpose>/<unique-id> \
    --timeout <frozen-seconds> \
    [--notify-desktop] \
    -- <exact-command> [args ...]
  ```

* The output directory must be a new child of `build/`; the launcher refuses
  overwrite. It preserves the quoted command, repository identity and dirty
  status, tool versions, timestamps, systemd unit, stdout/stderr, exit status,
  and a machine-readable result.
* After the launcher reports `LAUNCHED`, record the unit and evidence directory,
  then end the agent turn. Polling or waiting solely for deterministic job
  completion is prohibited. Linux owns execution; the model resumes only in a
  later invocation.
* Every detached job must attempt a local desktop notification after the
  durable terminal marker is written (`--notify-desktop` is accepted as an
  explicit, idempotent spelling). Notification delivery is never evidence,
  callback failure cannot change the job result, and notification does not
  authorize or automatically trigger follow-up work.
* A later agent may interpret the run only when exactly one terminal marker is
  present: `COMPLETE`, `FAILED`, or `TIMEOUT`. Absence of all three means the
  result is unavailable; never infer success from logs, elapsed time, a missing
  process, or an agent/session boundary.
* `COMPLETE` means exit 0. `FAILED` means a nonzero command exit. `TIMEOUT`
  means exit 124 from the frozen external wall-clock limit and is an
  infrastructure outcome, not a test failure. Do not extend the timeout or
  relaunch without authorization when the timeout is contract-frozen.
* **Bounded campaigns:** Repeated expensive attempts against the same
  unresolved gate require an owner-authorized, frozen budget specifying the
  maximum attempt count, per-attempt wall-clock timeout, and cumulative
  campaign budget. A launched attempt consumes a slot regardless of whether
  it completes, fails, times out, or becomes unavailable. Budget exhaustion is
  a valid terminal result and does not authorize another attempt, a longer
  timeout, a larger budget, or a substitute method without renewed owner
  authorization.
* Use a foreground managed execution session only for interactive hardware,
  commands expected to complete within 60 seconds, or environments where the
  detached-runner prerequisite fails. Persist the same evidence, and do not
  repeatedly summarize unchanged progress.

`systemd-run --user` survives terminal and agent-session closure. Survival
across logout requires user lingering; survival across reboot is not promised.
See [`docs/DETACHED_JOB_RUNNER.md`](docs/DETACHED_JOB_RUNNER.md).

**Agents decide and interpret; Linux executes and waits.**

---

### 4.3 Proportionate research execution

Apply [the research execution policy](spu_strategy/RESEARCH_EXECUTION_POLICY.md)
to owner-approved exploratory software and engineering validation. Class A
scope includes ordinary implementation, debugging, reruns and negative controls;
independent acceptance is a claim gate, not a prerequisite for investigation.
Existing regression gates for production/shared infrastructure and Class C
hardware, expensive-job, preservation and destructive-operation controls remain.
Frozen contracts transition only where explicitly named by that policy.

### 4.4 Qualification-to-simulator integration

The simulator is the cumulative software reference for the qualified SPU
architecture. Every qualified, architecturally observable capability must have
a corresponding implementation in the appropriate simulator profile and passing
conformance tests before software ecosystem integration is complete.
Qualification makes a capability eligible for integration; it does not establish
simulator conformance. Freeze semantics, arithmetic bounds, overflow/refusal and
exception effects, and observable state transitions before integration. Preserve
existing profile behavior; incompatible semantics require an explicit profile
version. Use shared fixtures with independently established expected results
and RTL simulation where applicable, including negative and boundary cases.

Report software conformance, RTL functional evidence, synthesis/timing and
physical FPGA qualification separately. Pending physical qualification does not
block integration of qualified functional semantics. Experimental research
interpreters do not become architectural reference behavior by existing.

Each released simulator build must expose a machine-readable capability
manifest tied to its implementation, profile and source/build identity. Check
support against registered feature tests; bind conformance claims to passing
results for that identity. Missing/stale evidence cannot imply qualification.
See [the simulator integration policy](docs/SIMULATOR_INTEGRATION_POLICY.md)
for the manifest fields and release obligations. This policy does not reopen
frozen campaigns or authorize hardware work.

## 5. Normative References & Catalogs

* **ROTC 0–35 Angle Catalog & Permutations:** [`knowledge/rotc_tables.md`](knowledge/rotc_tables.md)
* **ISA Reference & Opcodes:** [`knowledge/isa_reference.md`](knowledge/isa_reference.md)
* **Hardware Silicon Evidence Ledger:** [`docs/hardware_evidence.md`](docs/hardware_evidence.md)
* **SPU Lexicon & Terminology:** [`knowledge/SPU_LEXICON.md`](knowledge/SPU_LEXICON.md)
* **Contract Template:** [`spu_strategy/contract_template.md`](spu_strategy/contract_template.md)
