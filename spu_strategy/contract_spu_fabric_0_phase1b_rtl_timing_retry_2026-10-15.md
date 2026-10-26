# SPU-FABRIC-0 Phase 1B RTL Timing Check — Retry Proposal

**Status:** DRAFT — OWNER AUTHORIZATION REQUIRED
**Prior attempt:** `build/spu_fabric/fabric_0_phase1b_rtl_timing_20261015/`
**Scope:** Repeat the same selected RTL timing check with a parser-only repair
**Scheduler / hardware:** Excluded

## 1. Prior attempt and diagnosed cause

The first authorized attempt completed with exactly one `FAILED` marker, exit
code 1, and runtime 10 seconds. Unit:
`spu-runner-20261014T234125Z-867019`.

The W32 `surd_w32:min_negation_overflow` vector completed in RTL with invalid
status 0, normalization requested, and harness-reported latency 107 cycles.
The expected timing value matched. The checker failed before recording that
case because its output parser required every aggregate latency field to be a
decimal integer. The existing harness prints `x` for an empty category's
average (here, `fit=0`), so the summary did not match the parser. This was a
checker-output parsing defect, not an RTL/oracle disagreement. The saved
stdout, stderr, command, and return-code files remain in the prior attempt's
artifact directory.

## 2. Repair

`software/experiments/spu_fabric_0_rtl_timing_check.py` now accepts decimal or
`x`/`X` aggregate fields, but requires numeric min/max values for the active
single-vector category. It records the command and its artifact paths in
`result.json` before execution, saves stdout/stderr/status before examining
the command return code, and records `FAILED` plus the diagnostic on failure.

The retry uses the same selected records, source timing reference, frozen
traces, RTL, harness, parameters, and comparison rules. It does not change the
C2 schedule proposal or run any scheduler.

| Input | SHA-256 |
| ----- | ------- |
| `software/experiments/spu_fabric_0_rtl_timing_check.py` | `5f3776c22a362044c122376a19e137bb62ed15e056b39466ebf6090238f2080b` |
| `software/experiments/spu_fabric_0_timing_reference.py` | `80b753da559a19b4a3fc3dada6829806846b74449513040bc52adfdc516a603d` |
| `fixtures/spu_fabric_0/manifest.json` | `24e7e35204baa8ee1e44a1cb09f788073a2bf721045190acb2a120ad1081ca13` |
| Isolated trace | `18585af72c7f65b4767e0526890424e56218af9eb20a6dbf90d943bf30c8a440` |
| Burst trace | `4db6e7458794b4a36f07d2cfd29a135f4301fb1a9e46ec73f77dc7f5b1060067` |
| Steady trace | `64359fdf2079299bbc1bfe95fe1b439f601084be288b62c9ace234dd5c4f3844` |
| Existing RTL harness | `31ce5470a8b8f565e607b3452123e4f04ff927773970fa7a73a51880c6a4eaa0` |
| Surd multiply RTL | `0cebd08aec2cd9ea6603ae655b9a15d65d9651eca958e1935137bd6deb04fdaa` |
| Surd normalizer RTL | `4d43e03f3745326a3f7d26fcf7a34219c8bc0ba1a4826a568eb3c74ab82291fa` |
| Binary GCD RTL | `e994552b50f34017b176d91303ac6c85774748d64d4014755d0979d6fcd3097c` |
| Exact quotient RTL | `2a78246d9ab13d439ee0be88b57dd58029d1d5ed0e77fcd61d1bac4837fd15cd` |

## 3. Proposed new bounded allocation

The prior one-attempt allocation is exhausted. This retry is a new campaign
and requires a new explicit owner authorization.

- Maximum attempts: 1.
- Per-attempt timeout: 120 seconds.
- New campaign cumulative budget: 120 seconds.
- Automatic retries: none.
- Execution: detached runner with desktop notification attempt.
- Output: `build/spu_fabric/fabric_0_phase1b_rtl_timing_retry_20261015/`.
- Runner evidence: `<output>/runner/`.
- Checker artifacts: `<output>/artifacts/`.
- No scheduler, synthesis, placement, routing, FPGA programming, or board I/O.

Before launch, verify all pinned hashes and verify that the proposed output
directory is absent. The exact proposed command is:

```bash
tools/run_detached_job.sh \
  --output build/spu_fabric/fabric_0_phase1b_rtl_timing_retry_20261015/runner \
  --timeout 120 \
  --notify-desktop \
  -- python3 software/experiments/spu_fabric_0_rtl_timing_check.py \
    --output-dir build/spu_fabric/fabric_0_phase1b_rtl_timing_retry_20261015/artifacts
```

The first attempt remains preserved and classified as a checker failure. A
second attempt can only be interpreted after exactly one terminal marker is
present. Its scope is selected intrinsic timing confirmation only and cannot
authorize Phase 1B scheduler evaluation.
