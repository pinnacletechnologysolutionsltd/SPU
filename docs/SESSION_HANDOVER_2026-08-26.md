# Session Handover — 2026-08-26

## 0. Scope note

Two threads tonight. SPU-4 (the primary programme) moved for real: parts
landed, encoder wired, ENC_PPR calibrated, a real firmware bug found and
fixed. GPU/rasterizer work (parked-by-default downtime filler, per
[[spu4-edge-node-focus]]) was picked back up as a filler while the encoder
was being wired, produced one solid negative result, then got stuck behind
real bench flakiness and was paused mid-experiment, not finished.

Nothing committed tonight except the INA226 runbook/contract doc catch-up
(`32a6238`, done early in the session, before the encoder work started — see
below). The ENC_PPR firmware fix and the handoff-doc update are **uncommitted
as of this note** — ask before assuming they're pushed.

## 1. SPU-4 / INA226 — encoder wired, ENC_PPR calibrated, real bug fixed

**Parts landed** ([[session-2026-08-17-hardware-order-timing]]). This is the
first physical progress on the actual primary programme since the 2026-08-16
focus narrowing — everything before tonight was prep/doc work done waiting
for parts.

- Committed first (`32a6238`): the orphaned 2026-08-20 doc-accuracy pass
  (`docs/INA226_CAPTURE_RUNBOOK.md` §2a `ENC_PPR` calibration procedure,
  `docs/INA226_COARSE_MONITOR_CONTRACT.md` v4 correction) had been sitting
  uncommitted in the working tree since that date, resurfaced by an unrelated
  `git stash pop` during the 2026-08-25 GPU session. Reviewed and committed
  as-is — content was already correct, just never landed.
- **Encoder wired**: it's a 4-pin quadrature module (+, −, O1, O2), but
  `ina226_logger_v2.py` only counts single-channel rising edges (no direction
  decode), so only one output channel (O1) goes to GP6; O2 is unused.
- **Real bug found and fixed, uncommitted**: `ina226_logger_v2.py`'s `main()`
  did an unconditional, unhandled I2C read to the INA226 as its very first
  action. Running it with only the encoder wired — exactly what §2a's own
  text describes as the calibration setup — crashed immediately
  (`OSError: [Errno 5] EIO`), contradicting the runbook. The runbook had
  explicitly flagged itself as "reviewed-but-unexercised" since 2026-08-20;
  this is that exercise finding a real gap. Fixed: the identity-check read
  is now `try/except OSError`-wrapped; on failure the logger prints an
  explicit `CALIBRATION-ONLY MODE` banner and streams `pulses` with
  sentinel-zero `bus_mV`/`shunt_uV`/`current_uA` — never silently fabricated
  as real data. A real capture with the INA226 present and responding is
  unaffected. `tools/bench_metrics/test_ina226_logger_v2.py` (17/17) and
  `TB_FILTER=ina226 python3 run_all_tests.py` (64/64) both pass after the
  change.
- **`mpremote` added to `.venv`** (was missing; no prior documented tool for
  copying `main.py` onto the Pico 2 existed in this repo). Used for every
  file transfer and reset tonight, hash-verified after each copy.
- **ENC_PPR calibrated: `ENC_PPR = 1`.** 12 pulses / 10 hand-turned
  revolutions = 1.2, rounded to 1. Two early attempts (10, 112) were wildly
  inconsistent and got discarded — not a hardware fault, a coordination
  problem: a fixed 20-45s capture window made it too easy to mismatch
  "exactly 10 revolutions" against a chat-relayed "start now." Switching to
  an **open-ended capture** (start turning whenever ready, say "done", stop
  the capture after — idle time before/after doesn't add pulses, so timing
  precision stops mattering) fixed that immediately: three independent
  reads all landed on exactly 12. Encoder is directly on the hand wheel, no
  gearbox in between, so a PPR this low is consistent with a single-slot
  photointerrupter-style RPM sensor disc (common on hobby gearbox kits like
  this one), not a fine multi-slot shaft encoder — `pulses` resolution as a
  covariate will be coarse by construction, not a defect. Reflashed and
  confirmed live: board reports `ppr=1`, no `WARNING ppr=0`.
- Full detail in `docs/INA226_SESSION_HANDOFF.md`'s new 2026-08-26 section
  (that document's own convention: living state doc, newest section on top).

**Next**: wire the INA226 (§2b of the runbook), confirm real pulse counts on
the fully assembled rig with the motor free-running (§2a step 7), then
block 0. Nothing else blocking.

## 2. GPU/rasterizer — one solid negative result, then paused on bench flakiness

Picked up [[spu13-gpu-rasterizer-audit-2026-08-24]]'s item 10 (the
framebuffer-readout probe's real, reproducible `(50,50)`-onward pixel
mismatch on real hardware, absent in zero-delay sim) as downtime filler while
the encoder was being wired. **Not the primary programme — paused
mid-experiment tonight, not concluded.**

- **Traced the FSM's step→settle→read timing by hand**: correct, matches the
  same single-register-stage latency already proven in `spu_gpu_top.v`.
  Rules out the prior session's leading hypothesis (a settle-timing gap in
  this probe's own sequencer) — sim already covers the failing region
  bit-exact, so a bug reachable by that trace would show in sim too, and
  doesn't.
- **Added a byte-shift diagnostic** to `tools/read_gpu_framebuffer.py`
  (uncommitted): always dumps the raw stream to
  `build/gpu_framebuffer_readout_raw.bin`, and on mismatch, tests whether a
  small byte-offset shift collapses the count — distinguishes a UART
  framing/dropped-byte bug from a real content bug. Validated against a
  synthetic single-byte-drop before trusting it on hardware.
- **Real capture result: shift test is flat at 70,190 mismatches across
  every offset tested (-4..+4).** This is a genuine negative result — rules
  out UART framing entirely, and exactly reproduces the prior session's
  count and location (`(50,50)` onward, `(15,0,0)` expected vs `(0,0,0)`
  got). Real, on-silicon, content-level disagreement with the oracle,
  confirmed not to be a host-side artifact.
- **Started a controlled settle-time experiment**: added a genuine module
  parameter `SETTLE_EXTRA_CYCLES` (default 1, byte-identical to today's
  behavior — sim regression re-confirmed 76,804/76,804 after adding it) to
  `spu13_tang25k_gpu_framebuffer_readout_probe.v` (uncommitted), to test
  whether more real settle margin changes the real-hardware result. Built
  and flashed a `SETTLE_EXTRA_CYCLES=8` variant via a scratch `.ys` override
  (`chparam`, not checked in) — Fmax stayed healthy (54.16 MHz vs the real
  25 MHz clock). **Never got a clean read of this experiment** — see below.
- **Real, recurring bench flakiness, independent of the RTL change**: across
  the session, the Tang 25K link died silently multiple times — once from a
  lost SRAM config after a power cycle (openFPGALoader reports success even
  when the load doesn't take effect until the *next* power cycle — a
  previously-documented quirk, [[tang25k-bl616-stuck-recovery]]), once from
  the dock's BL616 debugger spontaneously dropping into DFU
  (`349b:6160`) without anyone shorting anything — also previously
  documented, fixed the same way (plain power cycle). **New finding
  tonight**: even the known-good baseline bitstream (not just the settle=8
  experiment) went completely silent after a fresh reflash on one occasion,
  proving the instability isn't caused by the RTL edit. One self-inflicted
  mistake, corrected: briefly opened a second competing reader (`head -c`)
  on the same port while a real capture was still running, which can split
  the incoming bytes between two readers — don't do that again, always let
  one read own the port for its full duration.
- **Paused here, by agreement, given the bench's demonstrated unreliability
  tonight** — not because the experiment is uninteresting, but because
  continuing to reflash/retry a flaky link wasn't producing new information,
  just burning time. The `SETTLE_EXTRA_CYCLES=8` bitstream has never been
  successfully read.
- **One more attempt made after this was first written** (John: "let's give
  it a run, if it doesn't work we'll close the session"): fresh reflash of
  the settle=8 bitstream, confirmed live via a raw byte check, then a real
  read attempt — stalled again, this time with zero read progress over 15s
  (`/proc/<pid>/io` `rchar` unchanged) at the *exact same byte count*
  (1,758,607) as an earlier stall earlier tonight, on a different process —
  strong evidence the marker-sync loop is reliably choking at a reproducible
  point rather than just running slow. USB identity stayed normal
  (`0403:6010`, no DFU dropout this time), so it's a different failure
  signature again. Closed out per that agreement — this needs a session
  where the bench itself gets debugged first (reseat cables, try a
  different USB port/cable, check for a marginal power/ground issue),
  before the actual RTL question can be answered.

**If this resumes**: the settle-time experiment is half-built and ready —
just needs a clean re-flash-and-read of
`build/tang_primer_25k_spu13_gpu_framebuffer_readout_probe_settle8.fs`
(already built, on disk) once the bench is behaving. If it changes the
mismatch pattern, that's a real settle-margin issue invisible to zero-delay
sim and nextpnr's STA. If it doesn't, timing is ruled out entirely and the
`(50,50)`-onward disagreement needs a different hypothesis — possibly a
genuine silicon/toolchain effect worth a fresh angle, not a re-run of the
same experiment.

## References

- Commit: `32a6238` (INA226 doc catch-up, this session).
- Uncommitted, ask before assuming landed: `tools/bench_metrics/ina226_logger_v2.py`
  (calibration-only mode fix, `ENC_PPR=1`), `docs/INA226_SESSION_HANDOFF.md`
  (new section), `tools/read_gpu_framebuffer.py` (shift diagnostic),
  `hardware/boards/tang_primer_25k/spu13_tang25k_gpu_framebuffer_readout_probe.v`
  (`SETTLE_EXTRA_CYCLES` parameter), plus the untracked framebuffer-readout
  probe files from 2026-08-25 (`spu_tang25k_clk_pixel_div2.v`, the synth
  script, build scripts, `test_gpu_framebuffer_readout_probe.py`).
- [[spu4-edge-node-focus]], [[spu13-gpu-rasterizer-audit-2026-08-24]],
  [[tang25k-bl616-stuck-recovery]], [[tang25k-stty-after-reenum]] (memory).
- `docs/INA226_CAPTURE_RUNBOOK.md`, `docs/INA226_SESSION_HANDOFF.md`,
  `docs/INA226_COARSE_MONITOR_CONTRACT.md`.
