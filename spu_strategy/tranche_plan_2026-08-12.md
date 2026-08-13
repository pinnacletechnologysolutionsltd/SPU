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

## T3 — Decide the axiomatic gatekeeper (design, not cleanup)

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

**Most substantive item queued (found 2026-08-12):** the paper names the
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
- **T7.2 — The claim set.** Write down what SPU-4 is asserted to do, each claim
  tagged THEOREM/RTL/SILICON exactly as the papers are. A product claim set is a
  claim ledger with commercial consequences, and the discipline transfers
  directly. Cross-vendor bit-identity and bounded latency are the lead claims;
  the arithmetic is the mechanism, not the pitch.
- **T7.3 — Fault reporting.** Interacts with T3. "Deterministic detection that
  cannot report its own faults" is the weaker product. Resolve the gatekeeper
  question before the claim set is fixed, not after.
- **T7.4 — Integration surface.** What a customer actually receives: source,
  constraints, a reference top, a bring-up procedure, and the regression they
  can run themselves. The fresh-clone check is already the discipline here.

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
