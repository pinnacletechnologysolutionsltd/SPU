# Bench session — bench-supply characterisation, 2026-08-10

Instantiated from [`BENCH_PROCEDURE_TEMPLATE.md`](BENCH_PROCEDURE_TEMPLATE.md).
Procedure: [`INA226_CAPTURE_RUNBOOK.md`](INA226_CAPTURE_RUNBOOK.md) §2,
"Characterise the bench supply".

**Fill this in at the bench, as you go.** Its output feeds
`--supply-limit-ma` into the frozen manifest at `init`, which all thirty
sessions inherit and which cannot be corrected afterwards without re-running
them.

> **Order matters: solder the harness BEFORE measuring.** The runbook is right
> that this needs no INA226, but quantity #2 is measured *at the `VIN−`/actuator
> node* — i.e. across the power path — and the supply trim that follows is
> entirely a function of that path. At 300 mA through the breadboard's measured
> 0.96–1.44 Ω that is 0.29–0.43 V of error, drifting within the session.
> Quantities #1 and #3 are robust (a CC supply holds its clamp regardless of
> series resistance until it hits voltage compliance), but #2 and the trim are
> not. Soldering is also itself a rig change, so measuring first means measuring
> twice.

---

## Part 0 — Pre-registration (complete before power on)

| Field | Value |
|---|---|
| Session ID | `2026-08-10-supply-characterisation` |
| Question | What are the bench supply's true open-circuit voltage, loaded voltage, and CC-clamp current, and by how much does the front panel disagree with a DMM? |
| Prediction | Panel reads **low by roughly 10 %** on current, per the 2026-08-06 single-shot prior (280 mA displayed against 307.4 mA measured). Loaded voltage after soldering should droop **far less** than the 290–430 mV seen through the breadboard. |
| Falsifier | Panel agrees with the DMM **within 2 %** across all five current readings. That would make the 08-06 discrepancy a one-off misread rather than a calibration offset, and the panel usable for coarse work. |
| Runs planned | **5 minimum per quantity**, 4 quantities. Report min / median / max. |
| Positive control | **Not applicable, and labelled as such.** This is a characterisation plus one falsifiable claim about panel accuracy — not a fix-verification, so there is no configuration that "must fail". Do not let the completed sheet imply otherwise in the ledger. |
| Abort conditions | See bottom. |

---

## Part 1 — Rig (power off)

| Field | Value |
|---|---|
| Supply make/model | |
| Set voltage / current limit | |
| DMM make/model | |
| DMM jack used for current | **10 A jack** (lowest burden) — confirm: ☐ |
| Actuator | ☐ 280 mA continuous rating confirmed |
| Ambient / notes | |

### Power-path rebuild — complete and tick before any measurement

- [ ] Power path **soldered or screw-terminated** — no breadboard rail carries
      load current
- [ ] Actuator return goes **directly to the supply terminal**
- [ ] Separate **thin sense wire** from that terminal to Pico GND (not sharing
      the load path)
- [ ] Flyback diode (1N4001-class) **anti-parallel across the actuator's own
      terminals**, cathode to positive, mounted **at the motor**
- [ ] Confirmed the flyback is **not** in series with the measured path
- [ ] Module marked **`R100`** (or: INA226 not yet fitted — N/A this session)

### Safety, before enabling output

1. [ ] Voltage set with output **disabled**
2. [ ] Current limit set **and verified**
3. [ ] No loose wire can short VIN+ to logic pins
4. [ ] Actuator stoppable without fingers near blades
5. [ ] Physical power cutoff within reach

---

## Part 2 — Measurements

### #1 Open-circuit voltage — DMM at terminals, output on, no load

| run | 1 | 2 | 3 | 4 | 5 | min | median | max |
|---|---|---|---|---|---|---|---|---|
| DMM (mV) | | | | | | | | |
| Panel (mV) | | | | | | | | |

### #2 Loaded voltage — DMM at the `VIN−`/actuator node, motor free-running

| run | 1 | 2 | 3 | 4 | 5 | min | median | max |
|---|---|---|---|---|---|---|---|---|
| DMM (mV) | | | | | | | | |
| Panel (mV) | | | | | | | | |

Droop (#1 − #2): `____ mV`   ·   Stable over 60 s? `____`   ·   Drift noted: `____`

### #3 Regulating current at the CC clamp — DMM in series, 10 A jack, stall ≤ 1.5 s

> **Duty cycle: ≤ 1.5 s stalled, then ≥ 30 s unblocked to cool.** CC circuits
> drift with temperature and a stall test enters exactly that regime — which is
> why five readings, not one.

| run | 1 | 2 | 3 | 4 | 5 | min | median | max |
|---|---|---|---|---|---|---|---|---|
| DMM (mA) | | | | | | | | |
| Panel (mA) | | | | | | | | |

### #4 Panel-vs-DMM disagreement

| Quantity | Panel median | DMM median | Error % | Within 2 %? |
|---|---|---|---|---|
| Open-circuit V | | | | |
| Loaded V | | | | |
| CC clamp I | | | | |

**Falsifier check:** all three within 2 % → prediction refuted, record it.

---

## Part 3 — Trim and freeze

- [ ] Supply trimmed so the **loaded rail sits near 3000 mV** (measured at the
      load, after soldering)
- [ ] Measured limit ≤ actuator's **280 mA continuous** rating (`init` refuses
      a limit above it)
- [ ] Value to feed `init --supply-limit-ma`: `______ mA`
- [ ] Basis stated: median of five, not a single reading

> **Freeze after this.** Every physical and electrical change must be complete
> before the first block-0 capture. There is no partial-redo path — altering the
> rig mid-campaign makes later blocks incomparable and the only remedy is
> re-running all thirty sessions.

---

## Part 4 — Seal

- [ ] Numbers recorded **in this file**, not only in the terminal
- [ ] Copied into [`INA226_SESSION_HANDOFF.md`](INA226_SESSION_HANDOFF.md) so
      the next session reads rather than re-derives them
- [ ] min / median / max quoted — **never a single figure**
- [ ] The 2026-08-06 priors (3100 mV, 307.4 mA vs 280 mA displayed) explicitly
      marked **superseded**
- [ ] DMM burden noted: measured limit may differ slightly from what the INA226
      later reports through its own R100 — the two are not measuring an
      identical circuit
- [ ] Prediction outcome written down **either way**

---

## Abort conditions — stop and discard

- Droop at load exceeds tolerance or **drifts during the run** (the 08-06
  failure mode: 0.96 Ω → 1.44 Ω within one session)
- Ground reference shares a path with load current
- Stall exceeds 1.5 s, or the actuator is not allowed to cool
- Rig changed mid-session — note it and restart the run count
- Any reading taken through a breadboard rail carrying load current

A discarded session that is written down is worth more than a completed one
that is not.
