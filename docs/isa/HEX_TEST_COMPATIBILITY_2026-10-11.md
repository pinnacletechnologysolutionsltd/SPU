# HEX test compatibility repair

Status: full frozen decoder regression rerun PASS; integrated CPU timing pending.
Candidate: exact-digital decoder campaign, frozen preparation_01 CPU source.
Sparse Jet MAC remains closed at standalone simulation qualification.

The [first regression](../../build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/regression_01/result.json)
FAILED, exit 1, in 1,435/5,400 seconds. Repository regression had one error:
the HEX test called private `uut.qr_lane`, while the candidate's identical
addressing role is named `exact_qr_lane`. Dual-core traces, standalone index
checks, private exact-core checks and 128 retained kernels passed their stages;
the complete regression did not pass, so CPU timing remains gated.

The frozen core also retains historical HEX timing: telemetry reads the already
selected QR lane on acceptance, then selects the instruction's source. The live
core has a settle phase and observes the instruction's selected source. These
profiles are distinct; replacing a helper call alone cannot establish parity.
No CPU RTL or arithmetic/retirement semantics are changed by this repair.

The test now checks all 256 byte indices through public QLDI commit-lane
telemetry and HEX dispatch instead of a private function. Its default preserves
the live alternating-source, signed 16-bit telemetry and exactly-once checks.
An explicit `SPU_HEX_PRESELECT_PROFILE` fixture is used only for the frozen
candidate; it performs a source-selection transaction before asserting the
selected-lane result. The first transaction still checks retirement/pulse
discipline, but its value is outside that selected-source assertion. This is
legacy compatibility qualification, not repaired selected-source semantics.

[Focused evidence](../../build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/hex_compatibility_review_01/focused_review.json):
live strict and frozen preselected profiles pass. The strict profile rejects
the frozen core, preserving the timing distinction; corrupted expected
telemetry also rejects. Both positive profiles cover all 256 public indices.

[Preparation_02](../../build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/preparation_02/compatibility_review.json)
copies and verifies the original 2,050-file independent checkout, selected CPU
payload, corpus, tools and evidence. The candidate fixture explicitly selects
the legacy profile; the source core remains byte-identical. Old packages and
FAILED evidence are preserved. Owner approval is recorded and bound to the repaired package hashes.

The approved rerun is one additional regression attempt, 5,400 seconds wall-clock
and cumulative. The campaign permits two regression attempts total, capped at
10,800 seconds, and retains one 7,200-second timing attempt: 18,000 seconds total. It repeats the declared dual traces, all 128 kernels, repository,
scoped, trace/math and mandatory 25 MHz Padé gates. The consumed regression slot
is not reused. The original unused 7,200-second integrated timing slot remains
reserved and gated on the replacement regression's durable COMPLETE/exit 0 and
explicit required-regression PASS. No timing launch or automatic retry follows
from these focused results.

After ratification, the exact launcher is:

```bash
python3 build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/preparation_02/scripts/launch_stage.py regression
```

Integrated acceptance remains legal routing, complete required timing coverage,
no unconstrained required paths and PASS at 25 MHz. The Padé build is a separate
regression gate; it does not establish integrated CPU or sparse timing.

The replacement [regression result](../../build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/regression_02/result.json)
completed with exit 0 in 3,184/5,400 seconds. Repository checks passed 243/0;
all declared scoped, trace/math and separate Padé build gates passed. The
explicit required-regression PASS clears the existing integrated timing gate.
This establishes the declared regression scope, not integrated fit or timing.

The timing launch guard blocked the initial launch before slot reservation:
the system package log records Python 3.14.7-1 → 3.14.8-1 after regression
completed. The existing result and preparation_02 remain unchanged.
[Preparation_03 tool review](../../build/spu_surd_register/main_cpu_integration_20261007/exact_digital/decoder_campaign_20261011/preparation_03/tool_rebind_review.json)
binds the new executable, shared Python library and standard-library dependencies.
All 2,050 qualification sources and selected CPU RTL retain their tested hashes;
previously recorded non-Python tool identities are unchanged. Regression remains
qualified under its recorded runtime; no new Python-version regression is claimed.

The timing-only package also corrects inherited frontend command paths, preserving
normalized source order, options and parameters. Launch controls exercise source
and tool drift, missing/ambiguous regression results, wrong PASS status, missing
approval, consumed slots and prohibited regression launch. Each rejection leaves
the runner uncalled and its fixture ledger unchanged. The isolated preflight
mounts the passed regression read-only and hides the live source checkout.
The original one-attempt 7,200-second timing budget and 18,000-second campaign cap
remain unchanged. Integrated acceptance still requires legal routing and complete
required timing coverage with PASS at 25 MHz.
