# Bench bill of materials

**Living document.** The interlock BOM previously lived only inside
`SESSION_HANDOVER_2026-07-28.md`, where it was going stale; this is now the
single place to look before placing an order.

Prices are indicative NZD for a New Zealand buyer. Sourcing notes matter more
than prices — see §4, and note the interlock is **LCSC**, not DigiKey.

---

## 1. Have, working

| Item | Notes |
|---|---|
| Raspberry Pi Pico 2 | INA226 logger. MicroPython v1.28.0, `ina226_logger.py` as `main.py` |
| RP2350-Zero | SPI southbridge. Keep separate from the logger so the two roles never contend |
| Tamiya 75026 Mini Motor Set | 280 mA rated. **Ships with a rubber tube — that is the intended repeatable friction load** for `elevated_load` and `current_limited_stall`. Use it rather than improvising |
| ZK-5KX bench supply | Provides the CC clamp. The INA226 measures current, it does not limit it |
| JBL Cinema SB180 PSU (salvaged) | 18.44 V open circuit, red = positive. Unplug at the wall before working on it |
| Wukong Artix-7 100T, Tang Primer 25K | J11 bottom row only; top row backfeed-damaged and retired |
| 100 Ω resistors, 4× inline on SPI | **Installed.** Caps fault current at ~33 mA/pin. Current backfeed mitigation |
| 1N4001-class diodes | **Have** (confirmed 2026-08-16). Flyback across the motor |
| Enamel (magnet) wire | **Have** (confirmed 2026-08-16). This is the soldered sensor harness stock — see the stripping note in §2 before using it |
| 8-channel logic analyzer (fx2lafw) | **Have** — moved up from §2 on 2026-09-05. It earned the purchase immediately: every timing figure in `hardware_evidence.md` §3.8 was measured with it, and `J10IDENT` (driving each header pin at a distinct octave to settle a pin order two vendor documents disagreed about) is only possible with one. Note it is **High Speed USB** and must NOT be placed behind a Full-Speed isolator |

## 2. Need — buy now

**Decided 2026-08-08 (John): the spare INA226 is to be ordered, and the sensor
harness will be soldered rather than Dupont.** Both were already on this list;
this records them as decided rather than proposed.

> **Status 2026-08-11: still NOT ordered** (confirmed with John). The 08-08
> wording said "is being ordered", which read as actioned and was not. This is
> the longest-lead item on the dataset track and does not depend on the PCB —
> do not let it queue behind the bench_adapter layout. The custom Rev B
PCB and the power-ready interlock remain deferred — see §5 — because the damage
class they address has not recurred since the 100 Ω resistors went in, while
the failures that *have* cost sessions are connector- and module-side, which is
what these two items address at a fraction of the cost.

**Order the same variant.** The capture contract hard-codes `rshunt_mohm: 100`,
`shunt_lsb_uV: 5/2`, `current_lsb_uA: 25` and I2C address `0x40`
(`software/datasets/ina226_coarse_monitor_v3.json`). A module with a different
shunt does not merely read differently — every row fails the contract's
`shunt_equation` residual check, and the validator rejects the whole session.
Check the `R100` marking before wiring anything.

> **STALE AS OF 2026-09-03 — read before ordering from this section.** Every
> item below is scoped to the INA226/SOM capture campaign, and that campaign was
> **shelved on 2026-09-03**. The reasoning still standing in this section ("the
> experiment is stopped until one arrives") no longer describes anything that is
> running. The campaign's queued successor is a *fixed-load retest* whose blocker
> is a mechanical fixture, not a part — see `SESSION_HANDOVER_2026-09-04.md` §5,
> which also records two zero-bench pre-steps that need no purchase at all.
>
> **AMENDED 2026-09-05, later same day: the retest IS going ahead** (John's
> call). So this section is not dead — it is *conditional*, on a scoping
> question that has not been answered:
>
> - **If the retest recaptures all 30 sessions** (a genuinely single-variable
>   experiment — only the load application changes), the spare-INA226 argument
>   is fully live again: `all_capture_sessions_must_validate: true` with no
>   partial-redo path means a module failure mid-campaign costs every session
>   captured so far. **Buy the spare.**
> - **If it recaptures only the 10 `elevated_load` sessions**, the exposure is
>   a third the size, and the spare is a judgement call rather than a
>   necessity.
>
> **Decide the scope before ordering, not after.** The encoder's co-blocking
> argument below also only applies to a full recapture — RPM cannot be
> retro-fitted to sessions that are being kept.
>
> The logic analyzer has been bought and moved to §1. The active *engineering*
> track remains graphics — see §2a.

**The list is three items as of 2026-08-16** — John confirmed diodes and enamel
wire are already on hand, so both moved to §1.

| Item | Qty | ~NZD | Why |
|---|---|---|---|
| **INA226 breakout (R100 shunt)** | **2** | 24 | One failed its VBUS channel 2026-08-07 with I2C and shunt both perfect. `SESSION_HANDOVER_2026-07-28.md` already advised a spare on cost grounds: the frozen contract has **no partial-redo path**, so a module failure mid-capture costs all thirty sessions |
| **IR slotted optical encoder** | 1 | 5–10 | The highest-value *scientific* purchase, and **co-blocking with the INA226** — see below. All three prior negatives failed because features encoded operating condition rather than fault state; RPM is the covariate that lets the study condition on operating point instead of hoping. Current × speed also gives a torque proxy |
| **8-channel logic analyzer** | 1 | 15–30 | **Recovered onto this list 2026-08-16.** The roadmap's 2026-07-19 amendment said "INA226 + logic analyzer + test-gear order is going in now", but the analyzer never appeared in this BOM when it was extracted from the 07-28 handover, and John confirmed he does not have one. It is the single instrument that would have shortened several SPI sessions this year — the A7 bring-up saga, the SCK≤clk_fast/6 ratio work, the boot-status decode debugging — all of which were diagnosed by inference from UART symptoms instead of by looking at the bus |

Verify the `R100` marking on arrival. A different shunt invalidates the
current scaling, which is exact only for 0.1 Ω.

### Why the encoder must arrive *with* the INA226, not after it

`software/datasets/ina226_coarse_monitor_v3.json` is
`status: frozen_before_physical_capture_or_scoring`, defines 30 sessions
(3 classes × 10, in 10 blocks) with `all_capture_sessions_must_validate: true`,
and its four features are **current-only**: `mean_current_mA`,
`peak_to_peak_mA`, `mean_abs_delta_mA`, `mean_abs_deviation_mA`. RPM appears
nowhere.

RPM therefore has to be recorded **while capturing** — it cannot be
retro-fitted. Buy the INA226, start the campaign, then add the encoder, and the
choice is between discarding sealed sessions and permanently losing the ability
to condition on operating point. That second outcome is precisely the flaw that
produced all three prior negatives.

The v1→v2 amendment record is the precedent: it was legitimate specifically
because `sessions_sealed_when_amended: 0`. The same latitude exists now and
closes the moment block 0 is sealed.

**Decide before ordering, not after:** whether RPM enters as a formal v3
contract amendment or as additive per-session metadata. Either is defensible;
capturing without it is not.

#### The mechanics of that decision, found 2026-08-16

Investigated while writing `ina226_logger_v2.py`. Adding RPM is a **contract**
change, not a tooling change, and two specific things enforce that:

- **`software/lib/ina226_capture.py:294`** compares the CSV header for **exact
  equality** against a 7-column frozen schema and raises *"CSV header differs
  from frozen schema"*. A fifth column makes **every capture file fail
  validation** — at seal time, long after the bench work is done.
- **`tools/bench_metrics/power_log.py`** had a hard-coded `len(parts) != 4`
  row filter that **silently dropped** every wider row — `continue`, not an
  error, so a whole session would capture zero samples and only announce it at
  seal. **Fixed 2026-08-16** to accept both widths and to choose its output
  header from the first data row instead of assuming one. That was a latent
  bug regardless of RPM.

So the options are concretely:

| Option | Cost | Notes |
|---|---|---|
| **v3 contract, `pulses` as a 5th column** | Bump `CSV_COLUMNS`, write contract v3, update the validator | Per-sample data, strictly most informative. Legitimate **only while `sessions_sealed_when_amended` is 0** — the v1→v2 precedent |
| Side-car file per session | No schema change | Correlating two files by timestamp is fragile, and a missing side-car fails silently |
| Session-level metadata only | Cheapest | The contract's `decision_unit` **is** "complete capture session", so this may genuinely suffice — but it loses per-window RPM stability checks |

**DECIDED 2026-08-16 (John): the v3 column.** Implemented same day —
`software/datasets/ina226_coarse_monitor_v3.json`, validator, pipeline,
synthetic fixture and tests all moved. `pulses` is a **covariate, never a
feature**; the feature list is unchanged at the same four current-derived
values, and the test suite asserts that so a future edit cannot quietly
invalidate the study. Negative controls confirm a pre-v3 file and a negative
pulse count are both rejected.

**Firmware is already written and tested** —
`tools/bench_metrics/ina226_logger_v2.py`, covered by
`test_ina226_logger_v2.py` (17 checks, in the regression). It logs **raw edge
counts**, not rpm: at 100 Hz one sample is 10 ms, so a 20-slot wheel at
1000 rpm gives ~3 edges per row and one edge is worth ~300 rpm. Over the
contract's 32-sample window it is ~107 edges, about 1% resolution. Log edges,
aggregate host-side.

### Sourcing the encoder — local stock not found, 2026-08-16

John could not find an IR slotted optical encoder locally. Since it is
co-blocking, do **not** let it sit on a single slow order.

**The bar is lower than "encoder" suggests.** RPM here is a covariate to
condition on, not a measurement. The three classes are `normal`,
`elevated_load` and `current_limited_stall` — stall is ~0 RPM, elevated load is
reduced, normal is free-running. Telling those apart needs pulses proportional
to rotation, nothing more. Accuracy is close to irrelevant.

| Option | Notes |
|---|---|
| **Ball-mouse salvage** | A ball mouse contains **two** IR slotted encoders, each with the slotted wheel already on a shaft. Free, immediate, no lead time. Try this first |
| TradeMe | Worth checking; spec barely matters for this job |
| Reflective IR (TCRT5000 / line-follower module) + a white mark on the shaft | Often easier to source locally than slotted types |
| AliExpress **in parallel** | A few dollars. Order alongside a local attempt — whichever arrives first wins |

**Parallel-source it.** Spending ~$5 twice to remove a four-week gate on a
30-session campaign is obviously correct. The standing rule in §5 — do not let
a slow order gate a fast one — applies with extra force to a co-blocking part.

**Whichever is used:**

- **Record pulses-per-revolution in the session metadata.** A salvaged mouse
  wheel and a bought encoder differ, and a raw pulse count is meaningless
  without it.
- **Prove it counts on the Pico before block 0 is captured.** The electronics
  are trivial; the mounting is the fiddly part, and the contract is frozen once
  capture starts.

### Note on the enamel wire

Enamel/magnet wire is fine harness stock, but the insulation is a varnish that
looks like bare copper. It must be stripped — thermally with a hot iron and
solder blob, or mechanically — before it will take a joint. An unstripped
strand gives a joint that looks good and conducts intermittently, which is the
same failure class as the four connector faults of 2026-08-07 that this harness
exists to eliminate. Tin every conductor and confirm continuity before wiring
the sensor.

## 2a. Need — graphics bench, added 2026-09-05

The active track. Ranked by **loss prevented per dollar**, following the
bench-safety ranking in
`spu_strategy/contract_graphics_first_priority_2026-09-04.md` §7. Nothing here
blocks RTL work — the display path and the rasterizer both work today
(`hardware_evidence.md` §3.8, §3.9). What these buy is a bench that stops
destroying things and stops producing results that cannot be trusted.

| Item | Qty | ~NZD | Source | Why |
|---|---|---:|---|---|
| **Nylon standoffs/spacers + M3 screws; non-slip mat** | — | 10–15 | Jaycar | **Top of the safety ranking, and the cheapest item on it.** `BENCH_ELECTRICAL_SAFETY.md` records the leading explanation for the RP2040-Zero's death as an unsecured programmer drifting against the Wukong's headers — its castellated edge carries VBUS, 3V3, GND and GPIO, so any contact bridges two powered systems arbitrarily. Two boards have been lost; this addresses the mechanism of the most recent one |
| **Spare RP2040/RP2350 board** | 1 | 10–20 | **Local** | One destroyed 2026-09-04, one in service, **zero spares**. A dead programmer stops all FPGA work outright. Buy local specifically: a spare that arrives in three weeks is not a spare |
| **DE-15 solder-cup connectors + hoods, small proto board** | 2 | 10–15 | Jaycar | §3.9 was obtained on a harness that **came up only after being prodded** — recorded as a caveat on that entry. Moves the three-resistor DAC off flying leads onto a board with a real connector, and gives a second harness for the CRT without disturbing the working one |
| **VGA gender changer / coupler (sacrificial)** | 1 | ~5 | Jaycar | So pins 9 (+5 V) and 12/15 (DDC) can be isolated per `BENCH_ELECTRICAL_SAFETY.md` **without cutting a cable** — John's stated constraint for the CRT. Sacrifice a $5 adapter, not a cable |
| ADuM3160 USB isolator board | 1 | 20–30 | AliExpress | **Not blocking, slow route is fine.** The 09-04 handover said "do not reconnect the monitor until an isolator is fitted", but that rested on the mains-earth ground-loop hypothesis, which `BENCH_ELECTRICAL_SAFETY.md` later **demoted** in favour of mechanical contact. Still worth having; no longer a gate. Full Speed suffices — and keep the fx2lafw analyzer off it, it is High Speed |

**Free measures that outrank most of the above:** everything on one power
strip, and the host laptop on battery. Both cost nothing and both address the
earth-potential path directly.

---

## 3. Need — later, not blocking

| Item | ~NZD | Why |
|---|---|---|
| ADXL345 or LIS3DH accelerometer | 10–20 | Opens the Phase D drone/BLDC vertical. Three axes plus magnitude maps onto the four-feature window. **Use for coarse anomalies only** — imbalance, looseness, impact. At 100 Hz, bearing diagnosis reproduces the Paderborn negative exactly |
| Second INA226 for multi-channel | 12 | Address-straps to 0x41–0x4F: same driver, same schema, same validator, zero new science. Differential supply-vs-load monitoring for the application note |
| 1% resistor set for an R-2R ladder (4 bit/channel) | ~5 | **Only if analytic coverage antialiasing is built.** The current DAC is three resistors, 1 bit per channel, 8 colours — enough for flat-shaded geometry and for the raw/unsmoothed state the CRT control requires. Coverage AA needs intermediate levels and therefore this ladder. Deliberately deferred: smoothing before the CRT experiment would blur the artifact the experiment exists to observe |

**Deliberately not buying:** acoustic MEMS mic, strain gauge, current
transformer / Hall phase-current front end. Each needs a genuinely new feature
layer, and the new feature layer is where all three negatives came from. The
high-rate current path is already parked in the roadmap as a separate costed
decision.

## 4. Power-ready interlock — parts settled, purchase deferred

**Status: not a current purchase.** Deferred 2026-08-04, reaffirmed
2026-08-07. The backfeed damage class is mitigated *now* by the 100 Ω series
resistors plus power sequencing (FPGA powered first, RP2350 connected after;
reverse on the way down). It remains the correct long-term fix and stays in
roadmap Phase B as a design item, but it gates nothing.

| Ref | Part | Notes |
|---|---|---|
| U1 | SN74CBTLV3125 | Bus switch |
| U2 | **TLV3011BIDBVR** | SOT-23, **6-pin**. Order this over `TLV3011BIDCKR` (SC70-6): easier to hand-solder, and SOT-23-6 breakout adapters are far easier to find |
| — | SOT-23-**6** breakout adapter | Not SOT-23-5, which the abandoned MAX9063 route needed |
| R | Divider **137k / 100k** | Sized for TLV3011B's 1.242 V reference. **Not** 137k/10k, which was for MAX9063's 0.2 V |

**Two same-family traps, both of which silently invert or break the safety
behaviour:**

- **TLV3011 vs TLV3012** — TLV3012 is push-pull; this circuit requires
  open-drain to pull `J2_OE_N` low. Confirm the "11".
- **MAX9062 vs MAX9063** — only if the fallback is ever used. Same family,
  same package, *opposite* input polarity.

**Source from LCSC, not DigiKey.** U2 reverted to TLV3011B specifically
because LCSC stocks it (`16f2f3d`); that is why the part is preferred rather
than merely equivalent — its noninverting input is externally accessible,
restoring a hysteresis feedback path MAX9063 cannot provide.

Bring-up procedure: `hardware/pcb/bench_adapter/power_ready_interlock_breadboard.md`.
Assembling it properly is plausibly an electrical-engineer task, which makes it
a funded activity rather than a bootstrap one.

## 5. Sourcing strategy from New Zealand

Lead time dominates cost at these amounts.

- **Local (Jaycar, Surplustronics, PB Tech)** — pay the markup for anything
  that *blocks work*. The INA226 pair belongs here: the experiment is stopped
  until one arrives, and a month of waiting costs far more than the premium.
  **The encoder belongs here too** (added 2026-08-16): §2 shows it is
  co-blocking, not follow-on, so a slow order for it delays the campaign just
  as surely as a slow INA226 — and starting without it is worse than waiting.
  The logic analyzer does not block the capture campaign and can go the slow
  route, unless an SPI problem is actively costing sessions.
- **LCSC** — the interlock BOM, since that is where TLV3011B is stocked.
  Weeks of shipping, but nothing depends on it.
- **AliExpress** — accelerometer, spare encoder, the ADuM3160 isolator, anything
  with no deadline.
- **Graphics-track split (2026-09-05):** the §2a mechanical and connector items
  are all local — they are cheap, they are what actually stop board losses, and
  a three-week wait on a $10 bag of standoffs is three weeks of the same
  exposure that has already cost two boards. Only the isolator goes slow.

Do not let a slow order gate a fast one. If a tranche needs a part that has not
arrived, re-scope the tranche.
