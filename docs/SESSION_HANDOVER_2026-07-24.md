# SPU-13 Session Handover — 2026-07-24

## Stop state

- Local `master` matches `origin/master` at `a12485b` (paper fixes below).
  Nothing unpushed as of this handover.
- Last independent full-regression audit: 173/173, verified directly, not
  read from a report.
- GTP has been intermittently unavailable (usage-limit / Codex reset
  instability); its own availability window is not reliably known. Treat it
  as opportunistic, not scheduled.

## Karatsuba three-product Z[phi] multiplier — Phases 0 through 6-standalone CLOSED

Full detail: `docs/ZPHI_KARATSUBA_INTEGRATION_PLAN.md`,
`docs/ZPHI_KARATSUBA_MULTIPLIER.md`, `docs/hardware_evidence.md` §3.2l.

- Phases 0-5: complete, independently re-derived (not just read) before each
  next phase began, pushed. The three-product candidate
  (`spu13_zphi_mul_serial_karatsuba.v`) is the **production default** in
  both tensegrity RTL consumers as of Phase 5 (commit `c1fe58f`); the
  four-product reference remains selectable
  (`USE_ZPHI_KARATSUBA=0` / `ZPHI_KARATSUBA=0`) for one-parameter rollback.
- **Phase 6 standalone half CLOSED, silicon-proven 2026-07-24** (commit
  `c6a83ad`): fresh `TENSEGRITYPROBE` bitstream built from clean commit
  `8aaaeaa`, seed 2 (deliberately distinct from the Phase 4 matrix's
  1/7/13), DirtyJTAG SRAM-loaded, UART returned `TGR:P V:7 E:00` repeated
  200x over 15 seconds with zero variance. This is real, live-hardware
  confirmation — a physical Xilinx Artix-7 100T was detected via JTAG
  (IDCODE `0x3631093`) before anything was written.
- **`TENSEGRITYLINK`'s full transactional confirmation is the one
  remaining piece of the entire plan.** It needs live RP2350-to-FPGA SPI,
  the exact connection class that already damaged two boards via backfeed
  — explicitly gated on the power-ready interlock, and a deliberate
  decision was made *not* to attempt it without the interlock even though
  parts are ~1 week out. Do not relitigate this without new information.
- One environment finding worth knowing before touching this again:
  **synthesis is not bit-reproducible run-to-run in this environment**
  (yosys version drift most likely). Do not rerun `synth` against an
  existing `_ZK{n}_S{seed}` artifact name to "double check" it — this
  overwrote real Phase 4 evidence once already (recovered by relying on
  the untouched P&R sibling artifacts and correcting the doc claim
  honestly — see commit `8aaaeaa`'s message for the full story). Give any
  future ad-hoc verification build a seed not already in use.

## SU3 — evidence gap open, gated same as TENSEGRITYLINK

Full detail: `spu_strategy/gtp_contract_su3_evidence_gap_2026-07-22.md`.

- The standalone SU3 proof (2026-07-04, exact QR hex values, guard-delay
  tuning) has **no corresponding entry anywhere in `hardware_evidence.md`
  or git history** — exhaustively searched (whole-repo grep, git log -S
  on the exact hex strings, `docs/archive/`, untracked files). Path A
  (recover lost evidence) is closed out as genuinely not findable.
- Path B (fresh Wukong re-run) is the only way forward, and it needs the
  same interlock as `TENSEGRITYLINK` — it's also fresh RP2350-to-FPGA SPI.
- Two small, hardware-independent paper fixes were applied 2026-07-24
  (commit `a12485b`): added the missing contact email to SU3's author
  block, and corrected its bibliography's stale "(in preparation)"
  citations for RPLU/LUCAS, both published now with real DOIs.
- **RPLU v0.2 bundling was investigated and ruled out**: `spu13_zphi_mul_serial`
  is instantiated only by the two tensegrity consumers, nothing in
  RPLU2/Jet's M31/A31 domain — an old session-memory note suggesting this
  bundling was a stale plan that didn't survive contact with how the work
  actually developed. Don't resurrect it without re-checking.

## Bench hardware — INA226 capture does NOT need the interlock

This is the one thread that can move independently of the Digikey/interlock
timeline. See `docs/INA226_CAPTURE_RUNBOOK.md` and
`docs/INA226_COARSE_MONITOR_CONTRACT.md`.

Current inventory:
- INA226: in hand, shunt confirmed genuine `R100` (0.1ohm) — verified by
  direct multimeter measurement, not just the module's silkscreen marking.
- Breadboard kit: arrived.
- Pico 2: headers being soldered (unconfirmed complete as of this
  handover — check before assuming ready).
- Bench supply: settled on a used **ZK-5KX** module via Trade Me ($40 NZD,
  specs independently cross-checked against the genuine manufacturer
  specs — 0.6-36V, 5A, 80W, real adjustable CC/CV). Needs its own DC
  input; plan is a salvaged ~19V supply pulled from inside a soundbar.
  **That salvaged unit takes mains AC directly on its input side** — it
  has an insulating shield on 3 of 4 faces with no exposed traces on the
  fourth, which is an acceptable risk profile, but always unplug from the
  wall (not just switch off) before handling it, and don't assume primary-
  side capacitors are discharged just because it's unplugged.
- Actuator: a small hobby DC motor with an exposed shaft (not a fan) —
  chosen specifically because the repeated stall/friction-load maneuver
  the frozen contract requires (10 blocks, each needing one
  `elevated_load` and one `current_limited_stall` session) is safer and
  more repeatable on a bare shaft than on fan blades. The original
  "reuse it as a PC case fan afterward" plan was dropped — the HP SFF
  case has no spare fan mount.
- Interlock parts (74CBTLV3125PGG, MAX9063EUK+T — not MAX9062, wrong
  polarity — 137kOhm + two 10kOhm resistors already on hand, SOT23-5 and
  TSSOP-14 breakout adapters, spares of both ICs): BOM finalized, Digikey
  account in progress, order placed once funds available next week.

## Task list (human side)

1. Solder Pico 2 headers if not already done.
2. Verify the salvaged 19V supply's actual output voltage and polarity
   with the multimeter before wiring it to the ZK-5KX.
3. Source the DC motor (not gated on Digikey — get it from anywhere fast).
4. Once INA226 + Pico 2 + breadboard + ZK-5KX + motor are all ready: run
   the actual INA226 physical capture (30 sessions, frozen contract) —
   this is the decisive experiment and does not wait on the interlock.
5. Place the Digikey order once funds are available.
6. Once interlock parts arrive: breadboard and bench-verify the interlock
   per its documented bring-up sequence before touching TENSEGRITYLINK.
7. Send the Dr. Thomson email (personal-network warm contact).
8. Check GTP's availability opportunistically.

## Outreach — deliberately held, one open judgment call

- Show HN / broader community posting remains explicitly deferred "until
  the Karatsuba tranche is cleanly frozen." Phase 6-standalone just
  closed — whether that counts as frozen enough to revisit timing, or
  whether it should wait for full TENSEGRITYLINK closure too, is an open
  question for the project owner, not decided either way.
- LinkedIn/Davis-style warm-network outreach was discussed 2026-07-24;
  no action taken yet — see that conversation for the sequencing
  reasoning (warm outreach is meant to follow the Show HN/artifact-led
  step, not precede it).
- Camera/facial-recognition SOM idea: confirmed nothing is written down
  anywhere in this repo about it — it was a passing comment from a
  different, less rigorous AI chat, not a real plan. Don't resurrect it
  without deliberate scoping.

## Explicitly parked

- Custom bench-adapter PCB fabrication.
- Pricing, branding, logo work, custom-domain purchase.
- Camera/vision pipeline work.
- Any paper release beyond the two small SU3 text fixes already applied.

## Useful restart commands

```sh
git status --short --branch
git log --oneline --decorate origin/master..HEAD
python3 run_all_tests.py
python3 tools/ina226_capture_pipeline.py --help
openFPGALoader -c dirtyJtag --detect
```
