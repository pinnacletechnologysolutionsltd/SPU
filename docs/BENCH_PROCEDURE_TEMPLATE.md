# Bench procedure template

Copy this file per measurement session. Fill it in **as you go**, not afterwards.

Nothing here is new discipline. Every rule below was learned on this bench, at
cost, and the provenance is cited so it can be argued with rather than obeyed.
The output of a completed session is a `docs/hardware_evidence.md` entry in the
§3.2e.6 shape — the template is arranged so that filling it in *produces* that
entry, with no transcription step where numbers can drift.

**The model to imitate is §3.2e.7.** Read it once before your first session: it
is hash-pinned, ten runs, an internal positive control, and an explicit
statement of what it does not establish.

---

## Part 0 — Pre-registration (before power on)

> Write this before the rig is energised. If it is written afterwards it is a
> description of what happened, not a prediction, and it cannot be wrong —
> which is what makes it worthless.

| Field | Value |
|---|---|
| Session ID | `YYYY-MM-DD-<slug>` |
| Question | *One sentence. What are you trying to find out?* |
| Prediction | *What do you expect, numerically?* |
| Falsifier | **What result would prove the hypothesis wrong?** |
| Runs planned | *N ≥ 10. State it now.* |
| Positive control | *What configuration should FAIL in this session?* |
| Abort conditions | *What would make you stop and discard?* |

**If you cannot name a falsifier, you are not running an experiment.** You are
collecting a demonstration, which is fine — but label it as one and do not put
it in the ledger as evidence.

**On the positive control.** A negative control (the known-good image passes)
only proves the bench works. A positive control — a configuration that *must*
fail — proves the fault is still reproducing *today*. Without it, "the fix
worked" is indistinguishable from "the fault wasn't reproducing this session."
The divided-clock result was decisive precisely because the 50 MHz build failed
0/10 in the same session the 25 MHz builds passed 10/10.

---

## Part 1 — Rig (with the power off)

| Field | Value |
|---|---|
| Board + revision | |
| Bitstream path | |
| **Bitstream SHA-256** | `sha256sum <path>` |
| **Bitstream byte count** | `ls -l <path>` |
| Supply, set voltage, current limit | |
| Instruments (make/model, or "board UART only") | |
| **Device paths — fixed, by-id** | `/dev/serial/by-id/...` |
| Ambient / notes | |

### Power-path check — do not skip

At 200–300 mA a breadboard power path measured **0.96 Ω, degrading to 1.44 Ω
within one session** (2026-08-06). That is 0.29 V rising to 0.43 V of drop
*while measuring*. Every current and bus-voltage number taken across it
describes the breadboard, not the circuit.

- [ ] Power path is soldered or screw-terminated — **no breadboard rail carries
      load current**
- [ ] Actuator return goes **directly to the supply terminal**
- [ ] A separate thin sense wire runs from that terminal to logic ground
- [ ] Measured supply voltage **at the load**, no-load and at full load:
      `____ mV` / `____ mV`, droop `____ mV`
- [ ] Droop is stable over 60 s (note any drift)

### Device paths

Use `/dev/serial/by-id/...`, never `ls -t`, never a bare `/dev/ttyACM*`.
Three wrong results came from selecting a port with `ls -t` against three
connected devices. Record the full by-id path above.

---

## Part 2 — Execution

| # | Run | Command | Raw capture file | Result |
|---|---|---|---|---|
| 1 | control (neg) | | | |
| 2 | control (pos) | | | |
| 3 | trial 1 | | | |
| … | | | | |

Rules:

- **Save raw output to a file per run.** Not to the terminal, not to a summary.
  §3.2e.7's ten `build/lucas_200step/run{1..10}.log` files are what made it
  auditable months later.
- **One run is not a result.** Report the *rate* — `10/10`, `7/10` — never a
  single observation. Six retractions on 2026-08-04/05 trace to one measurement
  standing in for a distribution.
- **N ≥ 10 to characterise, N ≥ 20 before calling anything clean.**
- **Do not stop early on a good result.** Finishing the planned N is what
  distinguishes a measurement from a search for a pass.
- **If you change the rig mid-session, the session restarts.** Note it and
  start the run count again.

### If you added instrumentation

Adding observability moves placement. **Prove the instrumented build still
reproduces the fault before interpreting any trace** — a trace from a build
that no longer reproduces looks authoritative and describes a working design.

---

## Part 3 — Interpretation

- **What does the number aggregate over?** Reported Fmax describes the single
  worst path in the design, not the path your test exercises — which is why it
  showed no correlation with functional failure across 120 measurements. Ask
  this of every summary statistic before treating it as a predictor.
- **Suspect your instrumentation before the hardware.** Wrong port, wrong net,
  shared ground, stale bitstream. Rule those out explicitly and write down that
  you did.
- **Distinguish did-not-reproduce from did-not-happen.** An intermittent fault
  that stayed away is not a fix.
- **State what this does NOT establish.** One bitstream, one board, one session
  is a behaviour, not a reliability rate.

---

## Part 4 — Seal

The session is not finished until this exists.

- [ ] Raw captures committed or archived at a stated path
- [ ] Ledger entry drafted in `docs/hardware_evidence.md` with the §3.2e.6
      shape: **date, scope, build/load commands, bitstream SHA-256, raw proof
      lines, positive control, interpretation, limitation**
- [ ] Pass **rate** quoted, not a single run
- [ ] Every claim that will be made elsewhere from this session cites the new
      section number
- [ ] If the result was negative — **write it up anyway.** Failed hypotheses
      and retractions stay in the record. They are the most credible thing in
      the repository.

---

## Abort conditions — stop and discard the session

- Supply droop at load exceeds tolerance or drifts during the run
- Ground reference shared with a load-current path
- Device path selected by anything other than a fixed by-id name
- The bitstream on the board cannot be tied to a known SHA-256
- The positive control **passed** (the fault is not reproducing — you cannot
  learn anything about a fix today)
- Rig changed mid-run

A discarded session that is written down is worth more than a completed one
that is not, because the next person — including you in three weeks — learns
the abort condition without paying for it again.
