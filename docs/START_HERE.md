# Exact arithmetic, explained

SPU is an experimental computing project exploring exact arithmetic and geometric
operations in software and on reprogrammable chips called FPGAs. The question is
what these representations make possible, and what they cost to implement.

## A small example

Some geometric calculations involve √3. Storing a rounded decimal for it can
introduce rounding error. The Surd Register instead stores integer coefficients
and an explicit denominator: `(2 + √3)/3` is stored as `(2, 1, 3)`.

Consider multiplying two values:

```text
(2 + √3) × (2 − √3) = 4 − 3 = 1
```

For coefficient pairs `(a, b)` and `(c, d)`, the product pair is
`(a*c + 3*b*d, a*d + b*c)`. With `(2, 1)` and `(2, -1)`, it gives `(1, 0)`.
No decimal approximation of √3 is needed. For explicit-denominator registers,
the denominator is multiplied too, then reduced when normalization is requested.

You can check this identity with Python 3:

```bash
python3 -c 'a,b,c,d=2,1,2,-1; result=(a*c+3*b*d,a*d+b*c); assert result==(1,0); print(result)'
```

Expected output: `(1, 0)`. This is a small mathematical illustration, not a
hardware test or a qualification run.

The registers still have finite capacity. An operation publishes its result
only when the exact tuple meets the contract; otherwise it reports failure and
preserves the previous destination. Exactness describes the arithmetic, while
tests and implementation evidence establish how much of the design has been
checked.

## Demonstrated results and open work

Status at 14 October 2026. These are separate experiments and configurations.

| Work | Established result | Remaining boundary |
| --- | --- | --- |
| AOR-S1 software | Qualification complete: 91 operation cases, 29 kernel/comparator/alias cases, 26 mutation controls and frozen-source checks; repository regression recorded 244 PASS, 0 FAIL | Finite software coverage; no AOR hardware, silicon, speedup or energy claim |
| Padé FPGA build | Build completed; 34.80 MHz is a tool-reported post-route estimate | Timing qualification pending review of model coverage and delay provenance; exit 0 does not establish 25 MHz timing qualification |
| Surd CPU candidate | Placement PASS: 51,197 cells passed retained placement legality and topology checks | Routing/timing blocked by incomplete timing coverage; no routed or board result for this candidate |

AOR-S1 is a separate software experiment using integer coefficients and powers
of `2 + √3`. It does not change the Surd Register's explicit-denominator
arithmetic. Its checked `1*a` action is a declared logical accounting convention,
not a necessary mathematical operation or a measured hardware cost.

The CPU timing review identified missing DSP timing entries, stub delays and
unresolved speed-grade provenance in its frozen backend. The exact Padé timing
model also needs review; findings from one backend must be checked before being
applied to another. A reported frequency cannot establish timing for paths
the model omits or does not describe reliably.

## Explore it

The [software guide](software_guide.md) starts with two short source-based
commands and explains their expected output. No FPGA is needed.
The evidence archive includes a GPU walkthrough at
`evidence/docs/gpu_scene_preview.md`: it shows how to preview a two-triangle
scene, edit it, and inspect which triangle wins at a pixel. It separates an
ideal calculation from a finite-width software model, including three documented
depth-tie differences in the edited scene. Those image results have software-model
scope. The archive is selected evidence; running the walkthrough also requires
its software and fixture dependencies in the appropriate source checkout.

For the arithmetic and retirement design, read the Surd Register paper draft
in the evidence archive at `evidence/docs/papers/SURD_REGISTER_PAPER_DRAFT.md`.
It is a working manuscript; related-work comparison and resource/timing
provenance review remain open.

## Inspect the evidence

Download the [selected evidence package](assets/publication/2026-10-14/selected-evidence.zip)
and its [SHA-256 checksum](assets/publication/2026-10-14/SHA256SUMS).
The [file manifest](assets/publication/2026-10-14/manifest.json) lists all 104
selected files, their sizes and hashes. The package passed the owner's integrity
checks: no missing, extra or duplicate archive members. This establishes package
consistency, not independent validation of the experimental conclusions.

Inside the archive, start with `README.md` and `manifest.json`, then follow:

| Evidence | Location beneath `evidence/` |
| --- | --- |
| Publication claim table and qualifications | `docs/PUBLICATION_EVIDENCE_PACKAGE_2026-10-14.md` |
| Corrected AOR/Padé/CPU closeout | `build/aor_s1/implementation_qualification_20261014/closeout_reconciliation_01/` |
| Directed outcomes and mutation controls | `build/aor_s1/implementation_qualification_20261014/software_01/results/acceptance.json` |
| Raw repository and Padé logs | `build/aor_s1/implementation_qualification_20261014/repo_01/` and `pade_01/` |
| CPU placement review | `build/spu_surd_register/backend_compatibility_20261012/integrated_context_closeout_01/REVIEW.md` |
| CPU timing-model audit | `build/spu_surd_register/backend_compatibility_20261012/routing_timing_preparation_01/timing_model_audit.json` |

The package includes selected source snapshots and logs. Complete FPGA rebuild
dependencies—including large netlists, chip databases and external tools—are
omitted. Some links inside copied documents require the original repository and
retained local artifacts. Historical records remain intact; the reconciliation
record corrects their superseded timing and CPU summaries.

Earlier physical demonstrations have their own entries in the
[hardware evidence ledger](hardware_evidence.md). They do not qualify the current
Surd CPU or AOR experiment. Questions about the arithmetic, test coverage and
implementation costs are welcome through the
[repository's issue tracker](https://github.com/pinnacletechnologysolutionsltd/SPU/issues).

## The project and the company

John Curley leads the SPU project at Pinnacle Technology Solutions Ltd.
Read [about the project and contact routes](ABOUT.md), or visit
[Pinnacle's website](https://pinnacletechglobal.com/) for company information
and enquiries.

The research goals are to understand useful exact representations, their
implementation costs, and how geometric operations can fit a computing
architecture. The current results above are the evidence available today;
application speedups and energy advantages still require comparative measurement.
