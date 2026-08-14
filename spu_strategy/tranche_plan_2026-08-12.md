# Tranche plan — from 2026-08-12

Written at the close of the typestate-paper/audit session. Ordered by whether
something downstream is blocked on it, not by size.

## The theme that generated most of this list

Three separate defects today were the same shape: **an artifact that looks like
evidence and cannot fail.**

- `run_all_tests.py` counted a bench printing no verdict as a pass.
- `axiomatic_fault !== 1'b0` was asserted in a bench and two board probes
  against a signal hard-tied to zero.
- Four counts were propagated between documents rather than re-derived, two of
  them by me, in the same session in which I wrote a contract forbidding it.

None was caught by the typestate machine, and the published paper says so in
its limitations. That section is now load-bearing rather than decorative. The
first three tranches all attack this class directly.

---

## T1 — Harness honesty sweep (highest priority)

**Why now:** the no-verdict rule landed today and will expose benches that were
being counted as passes. Fixing what it surfaces is the immediate follow-on.

**Scope:**
1. Every bench the new rule reports as NO VERDICT — diagnose and fix. The
   karatsuba bench is known: it passes when built by hand with both
   `spu13_zphi_mul_serial_karatsuba.v` and `spu13_zphi_mul_serial.v`, and
   produces nothing under the runner, so the runner's source selection is
   incomplete. Suspect the same filesystem-order module dedup as the 2026-07-19
   fresh-clone blocker.
2. **Vacuous-assertion audit.** For every bench assertion, is there a reachable
   state in which it fails? Three vacuous checks were found today by accident
   while doing something else; nobody has looked on purpose. A condition
   comparing against a constant-driven signal is the signature.

**Done when:** the suite reports zero NO VERDICT, and every removed or repaired
assertion is listed with what it did and did not cover.

**Progress 2026-08-14 — the aggregator itself could not fail.** The sweep was
applied to the benches but not to `run_all_tests.py`'s own accounting.
`lucas_pass`, `pade_batch_pass`, `hc_pass` and `digon_pass` were summed into
`total_pass` with **no fail counterpart**, so a failing or deleted oracle
dropped the headline by one while `Total FAIL` still printed 0. A missing file
printed nothing at all. Seven suites also contributed to the total while
printing no section of their own, so 193 could not be reconciled from the
transcript — the visible sections summed to 186.

Fixed: four `_fail` counters added and included in `total_fail`, missing files
now print `MISSING — counted as a failure`, and all seven suites print a
section. Negative control: deleting `test_hyper_catalan_oracle.py` now yields
`Total PASS: 192 / Total FAIL: 1` where it previously yielded `192 / 0`.

Also repaired: `pade_eval_compare_tb.v` reported ref/local mismatches under the
label "timeout(s)", since one counter serves both conditions.

**Still open in T1:** the vacuous-assertion audit proper — "is there a reachable
state in which this fails" — has been done opportunistically, not
systematically.

---

## T2 — Count provenance: audit and apply

GTP delivered the first sweep (`gtp_findings_count_provenance_2026-08-12.md`,
753 occurrences over 108 files). Two things remain:

1. **Claude audits the sweep.** It has already been shown to be right where I
   was wrong, which raises rather than lowers the value of checking it.
2. **Apply the MISMATCH rows.** `docs/STATE_MACHINE_HARNESS.md:92` and three
   places in `docs/ROTC_KINEMATICS_PAPER.md` still carry the 8/8 that should be
   9/9 (lines 388, 468, 480). **Verified 2026-08-12: the ROTC paper is
   "Draft v0.1 — 2026-07-10", pre-TeX, with no DOI**, so these are ordinary
   draft edits and no version discipline applies. An earlier revision of this
   plan said it was published; that was wrong.

**Add to the sweep definition:** "can this artifact fail at all" is now a
verdict category, not just "does the number match."

---

## T3 — Decide the axiomatic gatekeeper — RESOLVED 2026-08-14

**Decision (John, 2026-08-14): wire it in, on its own bits.**

The gatekeeper was in fact instantiated in `spu13_core.v` on 2026-08-13 in
commit `7b80a59`, before this section was updated — so the "do not leave it as
it is" instruction was already overtaken, and both this plan and the 08-13
handover continued to describe the decision as open. That gap is closed here.

The instantiation as landed read `axiomatic_level` from `phinary_cfg[3:2]`,
which is **inside** the `phinary_chirality` field (`phinary_cfg[8:1]`,
`spu13_core.v:437`). Every board top passing `16'h000C` — chirality 6, used by
`spu13_tang25k_som_top.v` and `spu_a7_math_top.v` — therefore decoded to
`2'b11 = OFF`. The newly wired guard was dead on the SOM spin, which is the
product wedge, while looking fully connected.

Resolved by moving the level to `phinary_cfg[10:9]`; bits 15:9 were
unallocated (verified: no other reader). `spu13_core_som_opcode_tb.v` gains
**TEST 7**, a field-independence control that drives the literal board-top
value `16'h000C` and asserts RCA₀ stays armed. Negative control: reverting the
RTL to `[3:2]` makes TEST 7 fail with `fault=0 type=00`.

**Still true, and now recorded in the RTL comment:** this is bounded telemetry,
not proof of fault-freedom. `FAULT_FRACTIONAL` remains unreachable
(`is_fractional` tied to 0) and the module has no oracle/trace/poison suite.
GTP's dossier conclusion — that wiring-in was premature on those grounds —
was not wrong; the decision here is to keep it wired and honestly scoped
rather than revert, with the three-layer bar left open as follow-on work.

### Original framing (retained for context)

`hardware/rtl/core/spu13/spu13_axiomatic_gatekeeper.v` is a **complete**
fault-detection implementation — real conditions, real fault types
(`FAULT_BIT_OVERFLOW`, `FAULT_FRACTIONAL`, …) — and it is **instantiated
nowhere**. As of today `spu13_core.v` drives its `axiomatic_fault`,
`fault_type` and `fault_count` outputs to explicit constants with a comment
saying they are not evidence of fault-freedom.

Two honest options, and this is John's call because it is a product decision:

- **Wire it in.** Requires defining fault semantics for the core path and
  taking them through the three-layer discipline. Real work.
- **Delete it.** Honest, cheap, and reversible from git.

**Do not leave it as it is.** A fully implemented guard sitting unconnected is
the most convincing-looking dead code in the repository.

**Product angle:** "deterministic anomaly detection that cannot report its own
faults" is a weaker sell than one that can. If SOM is the wedge, this may want
to exist — designed deliberately, not inherited.

---

## T4 — Two more subsystems to the strict bar — COMPLETE

The methods paper targets ≥4 subsystems with oracle + trace equivalence +
poison proofs. Today's SPI bench made it **three**: ROTC, IROTC, SPI protocol.

Lucas MAC is now complete. The focused suite, oracle-to-RTL trace, and poison
proofs pass; the full regression is now 193/193. The remaining candidate is
SOM/BMU:

| Subsystem | Has | Needs |
|---|---|---|
| Lucas MAC | oracle, 59-vector trace, poison proofs | **complete** |
| Batch inverter | oracle, 10-case regenerated trace, collision and poison proofs | **complete** |
| SOM/BMU | oracle + trace equivalence + gatekeeper positive control | full poison proof and independent fault oracle |

SOM is no longer completely blocked after T3 wiring, but it remains below the
strict bar. T4 is closed at five strict-bar subsystems; SOM/BMU remains the
next verification candidate, pending an independent fault oracle and full
poison proof.

---

## T5 — Typestate paper v1.2 (batched, not scheduled)

**Trigger:** a bench session that moves a claim from RTL to SILICON — most
plausibly the full 60×2 IROTC catalog. Not residuals alone.

**RESOLVED 2026-08-14 — do not re-fix.** The ½Z[φ] premise item below landed in
the published v1.2. `THEOREM_LICENSED_TYPESTATE_PAPER.md` lines 51–57 now state
it outright ("live in `½Z[φ]`, not in `Z[φ]`… the generated catalog stores the
doubled…"), and line 28 reads "IROTC supplies catalog rotations whose stored
doubled numerators are exact Z[φ] values" — the imprecise wording quoted below
is gone. `docs/LUCAS_MAC_PAPER.md` §1.2.1 carries the same material for the
Lucas paper, though that one is **not yet deposited** (see the v0.3 note at the
end of this section).

~~**Most substantive item queued (found 2026-08-12):**~~ the paper names the
doubling theorem three times and never states the premise that motivates it —
the A₅ matrix entries are **½Z[φ]**, not Z[φ]. Line 28's "IROTC supplies exact
Z[φ] catalog rotations" is imprecise in exactly the direction previously
identified as a false claim; the rotations are ½Z[φ] and it is the stored
numerators 2M that lie in Z[φ]. Line 38 ("registers holding Z[φ] pairs") is
correct, since doubling puts them there. Not a result error and not urgent
alone, but a reader currently gets a theorem with a name and no premise.

Also accumulated: the corrected counts (landed), the SPI case
study now meeting the strict bar, and the SOM coverage reframing. Front matter
is already marked *working draft toward version 1.2* so a rebuilt PDF cannot
masquerade as the published v1.1.

**Discipline established and worth keeping:** freeze the old tag permanently,
cut a new one, repoint every URL, rebuild, publish as a new Zenodo version
under the same concept DOI. `v0.1-typestate` and `v1.1-typestate` must never
move — published PDFs cite them.

**And push the tag.** On 2026-08-13 the v1.2 deposit went live while
`v1.2-typestate` and all 11 commits sat local-only, so every
`blob/v1.2-typestate/…` URL in the published PDF 404'd. Found and fixed
2026-08-14 (`git push origin master --follow-tags`). Add "tag is on origin" to
the release checklist — it is the one step with no local symptom.

### T5b — LUCAS v0.3 deposit (queued, not urgent)

`docs/LUCAS_MAC_PAPER.md` is 23 lines ahead of the published v0.2: §1.2.1
"Integral representation at the icosahedral boundary" and an RTL-trace/poison
paragraph, both added in `7b80a59`. The **`.tex` has neither** — it is a
hand-written IEEEtran source, not generated from the Markdown, so the PDF at
`docs/LUCAS_MAC_PAPER.pdf` (30 Jul) is stale and cannot be deposited as-is.

John's call 2026-08-14: not urgent. The note to Andy Thomson promised the
material would be added, not that it would be deposited immediately. Add it
when accurate.

To do when picked up: port both additions into the `.tex`; add a Contributions
entry in the existing "*Added in version 0.2:*" style; bump version strings at
`.tex` lines 22, 40, 374 and `.md` line 637; rebuild; diff the PDF text against
the `.md`; freeze `v0.2-lucas`, cut and **push** `v0.3-lucas`; deposit under
concept DOI `10.5281/zenodo.21447440`. Character: **enhancement**, not
corrigendum — nothing in v0.2 was false.

Standing gap this exposed: `.md` and `.tex` are maintained separately with no
parity check and diverged silently for a day. A heading-comparison test is
cheap and would have caught it.

---

## T6 — Re-derive the public regression number

After T1 settles, the README's suite total needs re-deriving **on a fresh
clone** — the only honest reproduction check, per the 2026-07-19 blocker. The
number will likely go down. A smaller true number is the correct outcome and
should be described as such rather than quietly updated.

---

## T7 — SPU-4 as a product (now the primary direction)

John's call, 2026-08-12: SPU-4 becomes the commercial focus, developed and
released as a product rather than a paper artifact. That reorders everything
above — T1/T2/T3 remain worth doing because they protect the claims a product
has to make, but they are no longer the point.

**T7.0 — RESOLVED 2026-08-13.** The ~400-LUT figure is a synthesis/P&R
estimate, not a silicon resource measurement. The exact standalone probe build
was rerun with `bash build_25k_spu4_probe.sh`; it produced the ledger bitstream
SHA-256 `9599f5e420f46515d99b57d2b256489440341166941be3bc9992b0b827222664`
and closed at 168.58 MHz against the 12 MHz constraint. The functional silicon
result remains backed by `docs/hardware_evidence.md` §3.2j. Product wording
must keep those two claims separate.

Then, in rough order:

- **T7.1 — RESOLVED: reusable IP block.** README and the SPU-4 architecture
  now identify the commercial product as a reusable core/block; Tang 25K is a
  reference-validation vehicle, not the product. The generic core, decoder,
  register file, ALU, sequencer, and standalone wrapper are present. A board
  kit may follow as a reference design, but it is not the primary product
  boundary.
- **T7.2 — RESOLVED 2026-08-13.** `docs/SPU4_PRODUCT_CLAIMS.md` records what
  SPU-4 is asserted to do, with each claim tagged by evidence level. Cross-vendor
  bit-identity and bounded latency remain open product gates.
- **T7.3 — RESOLVED 2026-08-13.** `docs/SPU4_FAULT_REPORTING_CONTRACT.md`
  defines the base product as deterministic arithmetic plus bounded telemetry,
  not comprehensive self-fault detection. `henosis_pulse`, `dissonance`,
  `busy`, and `done` are explicitly not universal fault indicators. Hardened
  fault detection is a separate optional package requiring its own RTL,
  oracle, poison, and silicon evidence.
- **T7.4 — Integration surface.** What a customer actually receives: source,
  constraints, a reference top, a bring-up procedure, and the regression they
  can run themselves. The fresh-clone check is already the discipline here.

  **Decide first (found 2026-08-14): does the product wrapper export
  `dissonance`?** It is a port of `spu4_core` only;
  `spu4_standalone_top` does not have it and `debug_status` does not contain
  it. That makes the fault contract's allowed sentence — "reports … a
  saturating Quadray residual" — false for the wrapper the claim ledger names
  as the product interface.

  Adding the port was tried and **reverted**: it grew the probe 835 → 865 LUT4
  and moved the bitstream SHA off `9599f5e4…22664`, the value
  `hardware_evidence.md` §3.2j records as silicon-proven and that T7.0 was
  closed on. So the choice is a real trade, not a cleanup: narrow the wording,
  add the port and re-anchor §3.2j with a bench run, or split the probe and
  product wrappers. Options are written up in
  `docs/SPU4_FAULT_REPORTING_CONTRACT.md`.

  **General lesson worth keeping:** the probe top is the silicon anchor. Any
  RTL edit reachable from it can invalidate a documented bitstream hash, and
  the only way to notice is to rebuild and compare. Add that check before
  touching `spu4_standalone_top` or anything under it.

---

## T9 — Silicon evidence has no source anchor (new, 2026-08-14)

Found while checking whether the T3 gatekeeper rewiring disturbed a documented
bitstream. It does not stop there.

**`docs/hardware_evidence.md` records a bitstream SHA-256 for essentially every
silicon result and pins none of them to a source state.** Zero occurrences of a
source tag, source commit, or tree-state reference in the whole file. Each hash
identifies an artifact; nothing identifies the code that produced it.

The consequence is that "we record the hash of every bitstream we flashed"
reads as a reproducibility guarantee and is not one. You cannot tell, for any
entry, whether HEAD still builds it — only by rebuilding and comparing, and
only if you can also guess which build script produced it, which the entries do
not say either.

Concretely today:

- The SPU-4 probe (§3.2j) **does** still reproduce from HEAD —
  verified twice on 2026-08-14, `9599f5e4…22664`. That is what made the file
  look sound.
- The SOM entries (§3.2g.4 `946574dc…`, §3.2g.5 `8753c492…`) date from
  2026-07-17. Commit `7b80a59` instantiated the axiomatic gatekeeper **inside
  the `ENABLE_CORE_SOM` generate branch** of `spu13_core.v` on 2026-08-13,
  which changes the logic those spins synthesise. Those hashes are therefore
  near-certainly no longer reproducible from HEAD, and were already stale
  before today's `[10:9]` move compounded it. Not yet measured — measuring it
  is the first task here.

**Work:**

1. For each silicon entry, record the commit (or tag) and the exact build
   command. The build command is missing for several entries too.
2. Rebuild what is cheap to rebuild and mark each entry
   REPRODUCES / DIFFERS / UNKNOWN against HEAD.
3. For DIFFERS, keep the historical hash — it records what was flashed — and
   say plainly that HEAD no longer produces it. Do **not** overwrite a silicon
   hash with a fresh build; that would claim a bitstream was tested when it
   was not.
4. Decide whether re-anchoring means a new bench run or an explicit
   "evidence pinned to commit X" note. The second is cheap and honest.

This is the same defect class as the rest of the plan — an artifact that looks
like evidence and cannot fail — but sitting under the strongest claims in the
repository rather than the weakest.

**Running in parallel (John):** bench PCB layout, the Andy Thomson
correspondence, and the AI-contribution/README work.

---

## T8 — The A7 reset post-mortem

Still the strongest single piece of evidence that the work is done properly:
a three-week silicon outage localised layer by layer to a raw reset pad driving
async resets. Fully reconstructed in the handover notes, so the writing cost is
low, and it doubles as the portfolio piece for contract work.

---

## Not tranches — standing rules earned today

1. **Never read a pre-existing `.vvp`.** Rebuild from source or record
   UNRUNNABLE. Two wrong numbers today came from stale binaries (7 instead of 9,
   5 instead of 9).
2. **Look for the aggregate before claiming a bench reports no total.** The 336
   was printed all along.
3. **A figure that was true when written is not evidence later.** The 37 was
   correct on 2026-07-14 and wrong by 2026-08-12.
4. **Published tags are frozen.** Cut a new one; never move one a PDF cites.
