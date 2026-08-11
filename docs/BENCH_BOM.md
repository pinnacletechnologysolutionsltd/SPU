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
(`software/datasets/ina226_coarse_monitor_v2.json`). A module with a different
shunt does not merely read differently — every row fails the contract's
`shunt_equation` residual check, and the validator rejects the whole session.
Check the `R100` marking before wiring anything.

| Item | Qty | ~NZD | Why |
|---|---|---|---|
| **INA226 breakout (R100 shunt)** | **2** | 24 | One failed its VBUS channel 2026-08-07 with I2C and shunt both perfect. `SESSION_HANDOVER_2026-07-28.md` already advised a spare on cost grounds: the frozen contract has **no partial-redo path**, so a module failure mid-capture costs all thirty sessions |
| **IR slotted optical encoder** | 1 | 5–10 | The highest-value *scientific* purchase. All three prior negatives failed because features encoded operating condition rather than fault state; RPM is the covariate that lets the study condition on operating point instead of hoping. Current × speed also gives a torque proxy |
| **Dupont jumper set, or wire for a soldered harness** | — | 5–15 | Four distinct connector failures in one session on 2026-08-07 — a failing SDA line, two dropped grounds, a dropped VCC. A soldered four-wire harness to the sensor removes the entire class |
| **1N4001-class diode** | few | 2 | Flyback across the motor. Hygiene for switching an inductive load. Note: **not** a fix for an observed fault — the back-EMF damage theory was investigated and not supported |

Verify the `R100` marking on arrival. A different shunt invalidates the
current scaling, which is exact only for 0.1 Ω.

## 3. Need — later, not blocking

| Item | ~NZD | Why |
|---|---|---|
| ADXL345 or LIS3DH accelerometer | 10–20 | Opens the Phase D drone/BLDC vertical. Three axes plus magnitude maps onto the four-feature window. **Use for coarse anomalies only** — imbalance, looseness, impact. At 100 Hz, bearing diagnosis reproduces the Paderborn negative exactly |
| Second INA226 for multi-channel | 12 | Address-straps to 0x41–0x4F: same driver, same schema, same validator, zero new science. Differential supply-vs-load monitoring for the application note |

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
- **LCSC** — the interlock BOM, since that is where TLV3011B is stocked.
  Weeks of shipping, but nothing depends on it.
- **AliExpress** — accelerometer, spare encoder, anything with no deadline.

Do not let a slow order gate a fast one. If a tranche needs a part that has not
arrived, re-scope the tranche.
