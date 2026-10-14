# About SPU and Pinnacle

John Curley leads the SPU project at Pinnacle Technology Solutions Ltd.
The work explores exact arithmetic, geometric computation and FPGA implementation.
The [company website](https://pinnacletechglobal.com/) introduces Pinnacle's
hardware and software research and provides its public contact details.

## What you can inspect

The **CPU work** investigates a bounded Surd Register with integer coefficients,
an explicit denominator and atomic result publication. The latest backend
candidate has passed placement checks. Routing and timing qualification remain
blocked by incomplete timing-model coverage.

The **GPU work** includes a streaming rasterizer and software paths for inspecting
triangle scenes. Physical observations are recorded in the
[hardware evidence ledger](hardware_evidence.md); software-model examples have
their own scope. The selected package includes a walkthrough of an ideal image
and a finite-width model, including documented depth-tie differences.

The **verification work** includes exact software references, directed tests,
fault injection and source-bound evidence records. AOR-S1 has completed its
isolated software qualification. It establishes no AOR hardware, silicon,
speedup or energy result.

Start with the [overview and claim table](START_HERE.md), then follow its
[selected evidence package](START_HERE.md#inspect-the-evidence) for source
snapshots, reviews and raw logs. The work is experimental; the evidence describes
specific configurations rather than a qualified complete system.

## Get in touch

For company enquiries and collaboration, use
[Pinnacle's public contact details](https://pinnacletechglobal.com/#contact).
The company currently describes its focus as development, outreach and promotion.

For a technical question or a reproducible issue, use the
[SPU issue tracker](https://github.com/pinnacletechnologysolutionsltd/SPU/issues).
Useful feedback includes:

- Is the arithmetic representation clear, and which example would help?
- Which failure case or independent check should the verification add?
- What timing-model coverage and delay provenance would you require before
  accepting an FPGA timing result?

The front README stays brief; this page provides the project and company context.
