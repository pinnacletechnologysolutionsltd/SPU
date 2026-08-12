# Session handover — 2026-08-12

Typestate paper published twice, then an audit that found four wrong test
counts, two of them mine. Three separate instances of the same underlying
defect. Written as work landed, per the standing rule.

---

## 1. Publication — typestate paper v1.0 and v1.1

Both are live on Zenodo.

| Version | DOI | Anchor tag | Commit |
|---|---|---|---|
| v1.0 | `10.5281/zenodo.21866717` | `v0.1-typestate` | `2ecf1c0` |
| v1.1 | `10.5281/zenodo.21895480` | `v1.1-typestate` | `6097b7b` |

**The concept DOI is still unconfirmed.** `…717` is the *version* DOI for v1.0,
confirmed by John. By the N/N+1 pattern of the RPLU and LUCAS records the
concept DOI is probably `…716`, but that is inferred. Check "Cite all versions"
on the record page, then fix the row in the memory DOI map and add the third
badge to `README.md:13-14`, which still carries only RPLU and LUCAS.

### Tag discipline — the rule that came out of this

v1.0 shipped with nine URLs pinned to `v0.1-typestate`. When v1.1 needed a
corrected PDF the instinct was to move that tag. **That would have been wrong:**
it silently changes what a published record's citations resolve to, and
falsifies the paper's own sentence saying the citations are pinned.

The rule now is: **a tag a published PDF cites is frozen permanently.** Cut a
new one, repoint every URL, rebuild, publish as a new Zenodo version under the
same concept DOI. `v0.1-typestate` and `v1.1-typestate` must never move. Both
were curl-verified as resolving after the v1.1 push.

### What v1.1 actually fixed

Rendering defects only — no claim, tier, or evidence changed. Worth describing
that way, since it is a third category alongside RPLU's corrigendum and LUCAS's
enhancement:

- The **AI disclosure was mangled**. `tools/build_typestate_pdf.py` skipped the
  line starting `**AI disclosure:**` but not its two continuation lines, so
  page 1 of the published v1.0 opened with an orphaned fragment beginning
  "synthesis, and editorial revision". The obvious fix is wrong — the
  front-matter lines are consecutive, so a continuation rule that does not stop
  at the next `**Field:**` lets the Author rule swallow the disclosure entirely.
- **Three glyphs dropped** in §2.1. Inline code routes through `\path{}` into
  the monospace face, which had no font set and fell back to Latin Modern Mono.
  That face lacks φ, τ and ⊢, so the formal model rendered "let ▯ denote the
  ring automorphism". Fixed with `\setmonofont{DejaVu Sans Mono}`.
- **"tonight"** in the limitations section — undatable in a DOI-bearing record.

`tools/build_typestate_pdf.py` was untracked and is now committed; it produces a
published artifact. It also now reads the date from the markdown rather than a
hardcoded `\date{}`, which would have stamped 10 August on a 12 August revision.

---

## 2. The count audit — four wrong figures, two of them mine

GTP added six bench counts to the paper's RTL ledger rows after v1.1 published.
Audited by running every bench:

| Row | Claimed | Actual | |
|---|---|---|---|
| R1 | 8/8 acceptance tests | **9/9** + 2000 randomized REDUCE | wrong |
| R2 | 336 bit-exact checks | **336** | correct |
| R3 | 120 cases @ 12 clocks | **120 @ 12 clks** | correct |
| R4 | guard TB 9/9 cases | **9/9** | correct |
| R4 | regression 37 PASS | **50 PASS** | wrong, stale |
| R6 | 43 and 25 checks | **43 and 25** | correct |

**Two of my four "corrections" were themselves wrong and had to be reverted:**

- I counted `PASS: angle` lines in `test_rotc_vm_rtl_trace.py`, got 72, and
  wrote that the bench reports no total. It prints `(42 cases, 336 checks)` and
  `ALL 336 CHECKS PASSED`. I did not look for an aggregate before asserting
  there wasn't one.
- I read `build/spu13_tensegrity_guard_tb.vvp`, a **stale binary**, and got 5
  fixtures. Rebuilt from source it emits 9. The same trap gave 7 instead of 9
  for the rotor bench an hour earlier — and the contract I wrote for GTP that
  morning explicitly forbids running a pre-existing `.vvp` without rebuilding.

The 37 originated with me: quoted from `hardware_evidence.md` §3.2l into an
audit note without re-running it, then picked up from there. It was true on
2026-07-14 and the suite has since grown to 50.

---

## 3. The pattern behind most of today

**Three defects, one shape: an artifact that looks like evidence and cannot fail.**

1. `run_all_tests.py` counted a bench printing no verdict as a **pass** — if the
   process exited 0, `passed += 1`. So the suite total counted benches that
   verified nothing.
2. `axiomatic_fault !== 1'b0` was asserted as a failure condition in
   `spu13_som_bmu_tb.v` and in **two board probes**, against a signal assigned
   only at reset. The check could never fire.
3. Counts propagated document-to-document instead of being re-derived.

None is catchable by the typestate machine, and the published paper says so in
its limitations. That section is load-bearing, not decorative.

---

## 4. Changes landed

**SOM/BMU dead fault interface removed.** `axiomatic_level` was declared and
never read; `axiomatic_fault`/`fault_type`/`fault_count` were assigned only at
reset. Removed from `spu_som_bmu.v` and all **six** instantiation sites. Nothing
in `hardware_evidence.md` cited them, so no evidence was invalidated.

> **Process note:** I initially found five sites because I piped the search
> through `head` and acted on a truncated list. The sixth, `rplu_pipeline.v:153`,
> broke five benches until caught by the regression. Do not `head` a search whose
> output is the work list.

**Runner honesty fix.** `run_all_tests.py:411` and `:452` now report
`NO VERDICT` and count it as a **failure**. Silence is not success.

**New bench.** `hardware/tests/common/spu_spi_protocol_trace_tb.v` — the
oracle-vs-RTL trace equivalence the SPI case study never had. 26 state
comparisons, all 8 protocol states, 3 fault classes. The `-DNEGATIVE_CONTROL`
build fails on the *last* compared transition. `spi_protocol_oracle.py` is
unmodified, so the structural difference is intact.

**Knowledge doc reconciled** to the published paper. It claimed five completed
case studies against the paper's one completed harness. Now carries a coverage
table measured against the strict three-layer bar.

### Strict-bar coverage: three of five

| Subsystem | Oracle | Trace equivalence | Poison proofs | |
|---|---|---|---|---|
| ROTC | ✓ 69 checks | ✓ | ✓ | **met** |
| IROTC | ✓ 23 checks | ✓ 60 × 2 | ✓ | **met** |
| SPI protocol | ✓ 9/9 | ✓ 26 comparisons | ✓ | **met** (today) |
| Lucas MAC | ✓ 30 tests | — | — | not met |
| Batch inverter | ✓ | — | — | not met |
| SOM/BMU | ✓ 24 checks | ✓ | **impossible** | see below |

---

## 5. Open decision — the axiomatic gatekeeper

`hardware/rtl/core/spu13/spu13_axiomatic_gatekeeper.v` is a **complete**
fault-detection implementation with real conditions and fault types
(`FAULT_BIT_OVERFLOW`, `FAULT_FRACTIONAL`, …). **It is instantiated nowhere.**

`spu13_core.v` now drives its `axiomatic_fault`/`fault_type`/`fault_count`
outputs to explicit constants with a comment saying they are not evidence of
fault-freedom. Previously they were fed from the SOM BMU's dead port, so the
core's fault output has always been zero.

Two honest options — wire it in (requires defining fault semantics and taking
them through the three-layer discipline) or delete it. **Do not leave it.** A
fully implemented guard sitting unconnected is the most convincing-looking dead
code in the repository.

This is a product decision as much as an engineering one: "deterministic anomaly
detection that cannot report its own faults" is a weaker pitch than one that can.

Stale comments in `spu13_core_som_opcode_tb.v:158,170,182` still describe
`axiomatic_level` config bits that no longer reach anything.

---

## 6. State

- **Tree:** see `git status`. Commits from today: `6097b7b`, `8cabaa6`,
  `8eb4d2a`, `4099e80`, plus the SOM/runner work. **Unpushed at handover.**
- **Regression: 188 PASS / 1 FAIL.** Previously reported as 189/189. The
  delta is exactly the defect: `spu13_zphi_mul_serial_karatsuba_tb.v` printed no
  verdict and was being counted as a pass. Everything else recovered once
  `rplu_pipeline.v` was patched. The one failure is real and open — the bench
  passes when built by hand with both `spu13_zphi_mul_serial_karatsuba.v` and
  `spu13_zphi_mul_serial.v`, so the runner's source selection is incomplete
  (suspect the same filesystem-order dedup as the 2026-07-19 blocker). Still
  needs re-deriving on a **fresh clone** before the README number is updated —
  the only real reproduction check.
- **Paper front matter** reads *working draft toward version 1.2; published
  version is 1.1*, so a rebuilt PDF cannot masquerade as the published artifact.

Next tranches: `spu_strategy/tranche_plan_2026-08-12.md`.
