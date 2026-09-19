# SPU Repository Map

**Map date:** 2026-09-19
**Purpose:** bounded cleanup and SDK professionalization baseline

This map describes ownership and lifecycle boundaries. It is intentionally
short; the file inventory remains machine-generated from Git and filesystem
state rather than being maintained by hand.

## Top-level map

| Area | Role | Lifecycle rule |
|---|---|---|
| `software/` | Supported SDK, assembler/compiler, VMs, exact arithmetic, host tools, and software tests | Active by default; every implementation must identify its ISA profile or research status |
| `software/graphics/` | Comparative renderer laboratory | Active research/product surface: conventional control, Wildberger rational reference, and SPU hardware-semantic simulator |
| `software/common/` | C++ exact-arithmetic headers and parity tests | Supported library surface; C++ VM remains partial ISA-A until its matrix gaps close |
| `hardware/rtl/` | FPGA implementation | Active RTL is target-specific; profile and evidence level must be documented |
| `hardware/tests/` | RTL simulations and formal harnesses | Keep current verification; archive only when superseded and evidence provenance is preserved |
| `hardware/boards/` | Board constraints, synthesis recipes, probes, and manifests | Keep recipes that reproduce supported or evidence-bearing targets; do not delete solely because a board is paused |
| `examples/` | Curated user-facing programs and demonstrations | Supported onboarding surface; examples must run without hardware where advertised |
| `tools/` | Maintained development, generation, capture, and verification utilities | Keep reusable tools; archive one-off experiment drivers after evidence is linked |
| `docs/` | Current user, architecture, build, and evidence documentation | Current documents at the relevant index/root; historical material belongs under an established archive boundary |
| `docs/isa/` | ISA profile ownership and implementation matrix | ISA-A is current SPU-13; ISA-B is separate; ISA-C is partial |
| `spu_strategy/` | Owner-ratified contracts and planning records | Source records; retain and do not treat drafts as authorization |
| `knowledge/` | Mathematical, architecture, and language reference | Keep authoritative references; mark superseded profiles explicitly |
| `photonics/` | Research and exploratory photonic models | Research surface; non-authorizing unless a contract says otherwise |
| `fixtures/` | Immutable test vectors and decoded references | Keep if consumed by tests or cited as evidence; regenerate only through declared generators |
| `results/` | Frozen research outputs and measurements | Keep cited/evidence-bearing results; do not confuse them with build products |
| `build/` | Synthesis, P&R, simulation, and detached-job outputs | Generated and ignored; never commit routine build output |

## Active user path

The current public-facing software path is:

```text
examples/
  -> software/tools/ and software/spu13_asm.py
  -> software/spu_vm.py (ISA-A reference execution)
  -> software/common/ and software/vm/ (C++ parity work)
  -> software/graphics/ (renderer comparison and simulator)
  -> hardware/rtl/ and hardware/boards/ (FPGA realization)
```

The current graphics path is documented in
`docs/COMPARATIVE_GRAPHICS_LAB.md`. The SPU beam-renderer simulator described
there is a target surface; it is not yet evidence that all listed simulator
files exist or are bit-exact against RTL.

## ISA boundaries

- **ISA-A:** current SPU-13 execution profile. See
  `docs/isa/ISA_PROFILE_PROVENANCE.md`.
- **ISA-B:** separate Wheeler–Feynman/next-generation adapter profile.
  It must remain explicitly selected and must not silently replace ISA-A.
- **ISA-C:** partial C++ VM implementation of the ISA-A family.

VM opcodes, SPI transport command words, board probe protocols, and GPU scene
formats are separate interfaces unless a decoder or trace proves otherwise.

## Retention and cleanup policy

### Keep active

Retain code required by current builds, tests, supported examples, active
RTL, board definitions, reusable tooling, authoritative mathematical oracles,
or the current ISA-A software path.

### Archive

Archive superseded probes, historical bring-up scripts, frozen experiment
drivers, and one-off diagnostics when they support a cited result or preserve
important provenance. Each archived experiment should have a short README
stating its result, evidence link, date, and that it is unsupported.

Use the repository's existing archive conventions before introducing a new
top-level directory. Do not move files merely to make the tree look tidy.

### Remove from Git

Generated build directories, caches, `.pyc`, routine logs, temporary
simulation outputs, downloaded dependencies, and reproducible binaries should
remain ignored rather than tracked. Immutable fixtures, golden vectors, and
evidence captures are exceptions and must be cited.

### Restore or complete

Missing or diverged functionality belongs in a separate contract. Current
known gaps include C++ ISA-A parity, duplicate assembler opcode declarations,
explicit ISA-B RTL namespacing, and completion of the SPU beam-renderer
simulator. Cleanup must not silently fix these gaps.

## Audit procedure

For each future cleanup pass:

1. Generate a fresh tracked/untracked inventory and build-artifact report.
2. Classify only ambiguous directories or code families manually.
3. Check callers, tests, contracts, evidence citations, and generators.
4. Move or delete only with a recorded disposition; never use directory age
   as the sole criterion.
5. Run the repository gate from the documented baseline.

The machine inventory is intentionally not committed by this document. A
future release process may generate a timestamped inventory under `build/` or
the session workspace without adding repository churn.

## Verification baseline

The repository hygiene gate launched for this cleanup is recorded under
`build/repository_cleanup/verify_repo_20260919/`. Its terminal marker is
`COMPLETE`; interpret the accompanying `result.json` and logs for the exact
exit status and test details. This map itself is documentation-only and does
not establish new hardware or silicon evidence.
