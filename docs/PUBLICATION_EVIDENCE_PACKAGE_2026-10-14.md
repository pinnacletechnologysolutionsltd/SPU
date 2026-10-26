# Publication evidence package — 14 October 2026

Prepared for editorial review and inspection. Publication has not occurred.
The downloadable local bundle is
`build/publication/evidence_20261014/package_01.zip`, with a matching
SHA256SUMS file. It contains selected source snapshots, fixture inputs, raw
qualification logs, claim records and review reports. It is an evidence
selection, not a complete FPGA toolchain or a clean repository release.

## Claims and evidence

| Item | Publication wording | Evidence and limit |
| --- | --- | --- |
| Surd Register arithmetic | Exact bounded values `(a+b√3)/d`, with explicit positive denominator and atomic retirement | [Paper draft](papers/SURD_REGISTER_PAPER_DRAFT.md); mathematics unchanged by AOR-S1 accounting |
| AOR-S1 | Isolated software qualification complete: 91 operation, 5 kernel, 11 comparator and 13 alias witnesses; 26 mutation controls; frozen-source checks | [Reconciled acceptance](../build/aor_s1/implementation_qualification_20261014/closeout_reconciliation_01/acceptance.json); finite coverage and separate-agent review, not independent human verification |
| Repository regression | 244 PASS, 0 FAIL, plus the contracted trace/math gates | [Repository result](../build/aor_s1/implementation_qualification_20261014/repo_01/result.json) and retained raw stdout; checkout was dirty |
| Padé regression | Build completed in 509 seconds; 34.80 MHz is a tool-reported post-route estimate | [Original result](../build/aor_s1/implementation_qualification_20261014/pade_01/result.json); 25 MHz timing qualification remains pending timing-model coverage/provenance review |
| Latest Surd CPU candidate | Placement PASS: 51,197 cells in distinct BELs, with retained legality and topology checks | [Placement closeout](../build/spu_surd_register/backend_compatibility_20261012/integrated_context_closeout_01/REVIEW.md); routing/timing blocked by incomplete timing coverage |
| CPU timing blocker | Missing DSP timing variants, stub Artix LUT/FF delays and unresolved speed-grade provenance | [Audit](../build/spu_surd_register/backend_compatibility_20261012/routing_timing_preparation_01/timing_model_audit.json); findings apply to that frozen CPU backend/database. Check the exact Padé model separately |
| Standalone Surd wrapper | Retained routing reports characterize a separate wrapper; 46.90 MHz is a tool estimate | Paper §6.2 and its E7 record; no measured clock or integrated CPU timing claim; timing-model review must precede timing qualification |
| Offline GPU walkthrough | Baseline ideal/device RGB agrees for 307,200 pixels; edited scene has three finite-depth tie differences | [Walkthrough](gpu_scene_preview.md) and [diagnosis](../build/parallel_tranches_20261014/pixel_diagnosis_01/explanation.json); software-model scope |

AOR-S1 uses a separate integer/Pell-power representation. Its checked `1*a`
is a logical accounting convention, not a mathematically necessary operation or
measured hardware work. No AOR hardware, silicon, speedup or energy claim follows
from software qualification. Historical 234-DSP integrated mapping and latest
80-DSP placement counts describe different configurations and are kept separate.

The original AOR closeout incorrectly accepted the Padé timing gate and used
the historical CPU timeout as the latest status. The
[reconciliation](../build/aor_s1/implementation_qualification_20261014/closeout_reconciliation_01/REVIEW.md)
supersedes those interpretations. Original logs, freezes and reports remain
unchanged so readers can follow the correction.

## Bundle inspection

From the repository root:

```bash
cat docs/PUBLICATION_EVIDENCE_PACKAGE_2026-10-14.md
python3 -m json.tool build/publication/evidence_20261014/package_01/manifest.json
sha256sum -c build/publication/evidence_20261014/SHA256SUMS
```

Archive members retain repository-relative paths beneath `evidence/`. The
manifest records the original path, copied member, size and SHA256 for each
selected file. README describes exclusions and claim limits. Commands recorded
in historical job evidence document what ran; executing them would be a new
campaign. This package inspection launches no qualification or FPGA jobs.

The bundle omits large netlists, chip databases, tool binaries and complete
external dependencies. The selected CPU reviews identify fuller retained local
evidence. Surd paper links outside the selection require the repository and
those artifacts. Thus it permits inspection of the selected qualification
evidence but does not promise complete FPGA rebuild reproducibility. GPU image
provenance gaps remain explicit in the
[catalogue](GPU_RETAINED_ARTIFACT_PROVENANCE_2026-10-14.md).

## Suggested public update

> We are developing bounded exact arithmetic for values involving √3. Our
> Surd Register work stores coefficients and an explicit denominator, and
> publishes results only when the exact tuple fits its contract.
>
> A separate AOR-S1 software experiment has completed directed qualification,
> including fault injection and repository regression. The latest Surd CPU
> backend candidate also passes placement checks. Routing and timing remain
> blocked by incomplete timing-model coverage—a limitation we are documenting
> alongside the results.
>
> We are preparing the arithmetic, verification records and engineering
> limitations for inspection. We welcome questions about the representations,
> test coverage and FPGA implementation costs.

Publish the paper draft, an accessible website/GPU explanation and short
engineering updates using the same claim table. The paper still needs its
related-work comparison and review of original resource/timing provenance.
This package is ready for editorial review; it does not resolve those research
gates. Services/contact messaging can describe demonstrated engineering work
without implying qualified system performance.
