# Simulator integration policy

Adopted: 2026-10-19. Standing engineering principle.

The simulator is the cumulative software reference for the qualified SPU
architecture. Every qualified, architecturally observable SPU capability gets
a corresponding simulator implementation and conformance test before its
software ecosystem integration is complete.

Qualification establishes eligibility for integration. Simulator conformance
establishes that a particular implementation matches the qualified behavior.
Neither follows automatically from the other. Physical FPGA qualification is
a separate claim and may remain pending while functional semantics are integrated.

## Integration and release

1. Freeze instruction semantics, arithmetic domain/widths, canonicalization,
   overflow/refusal behavior, exceptions and observable state transitions.
   Include destination, flag, PC and memory effects on failure and atomicity.
2. Implement the capability in its named simulator profile. Preserve existing
   behavior and compatibility tests. Use a new profile/version for incompatible
   changes; never silently reinterpret previously accepted programs.
3. Run shared fixtures against independently established expected results,
   the simulator and RTL simulation where applicable. Test bounds, failure
   paths and exact post-state, as well as successful arithmetic. Mark missing
   comparisons NOT RUN; agreement between two implementations alone is not
   independent mathematical correctness.
4. Release with ISA documentation, limitations, reproducible examples, passing
   feature/compatibility tests and a build-specific capability manifest. Keep
   software, RTL, implementation-tool and physical evidence separate.

Integrate surd-register instruction groups progressively as their contracts
qualify. Normalization and Pell transforms require their own bounded semantics,
refusal and canonicalization contracts; physical route status alone does not
decide eligibility. Preserve the existing T1d compatibility profile. SSM, SG-0,
QSG-3 and RP0 remain experimental according to their individual evidence and
contracts until their machine semantics qualify. This policy promotes none of
their current claims and authorizes no new hardware commitment or frozen retry.

## Capability manifest

Each released build must expose a small machine-readable manifest before
program execution. Its implementation identity must distinguish the standalone
C++ `spu-sim`, this repository's Python entry point and the legacy C++ VM;
see the [software guide](software_guide.md). Profile names alone are insufficient.

Required top-level fields are `schema_version`, `implementation`, `profile`,
`source_revision`, `build_id` and `capabilities`. Each capability record contains:

| Field | Meaning |
|---|---|
| `support` | `implemented`, `experimental` or `unsupported` in this build/profile |
| `semantic_contract` | Versioned specification reference; null if none qualifies |
| `tests` | Registered feature-test identifiers covering that support |
| `conformance` | `pass`, `fail` or `not_run` for this exact identity |
| `evidence` | Conformance result reference bound to source/build, profile, fixtures and test identity; null when unrun |
| `rtl_functional` | Separate evidence reference and status, or `not_run` |
| `physical` | Separate evidence reference and status, or `not_run` |

The following is a format illustration, **not a capability inventory**:

```json
{
  "schema_version": 1,
  "implementation": "example-only",
  "profile": "example-only",
  "source_revision": "example-only",
  "build_id": "example-only",
  "capabilities": {
    "example_capability": {
      "support": "unsupported",
      "semantic_contract": null,
      "tests": [],
      "conformance": "not_run",
      "evidence": null,
      "rtl_functional": "not_run",
      "physical": "not_run"
    }
  }
}
```

Generate or check support entries against the simulator's registered feature
tests during build/release validation. Require tests for implemented and
experimental entries; an unsupported entry may have rejection tests. A test
name's existence does not establish a pass. Bind passing conformance records
to actual results and exact build inputs, including local source changes;
reject stale evidence and mismatches. Unknown capabilities are unsupported
for program compatibility decisions. Never label a capability simply
`qualified` without stating which evidence dimension qualified.

The manifest reports build support, not guaranteed acceptance of every input;
arithmetic bounds, instruction subsets and refusal behavior remain in the
referenced contract. Physical claims must cite the
[hardware evidence ledger](hardware_evidence.md). Synthesis/timing evidence
belongs in its own record and cannot substitute for physical observation.

This adoption adds policy and a manifest format only. Runtime manifest emission
and test-result binding are not implemented by this document. Existing builds
must not be advertised as satisfying the new release requirement until checked.
