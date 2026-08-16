# Bench procedure — §3.2j SPU-4 probe re-anchor

**Prepared 2026-08-16, to be executed next bench session.**
Copied from `docs/BENCH_PROCEDURE_TEMPLATE.md`. Part 0 and Part 1 are
**pre-registered** — written before the rig is energised, which is the whole
point of them. Fill in Part 2 onward as you go.

Both bitstreams are already built, hash-verified, and staged. **No build step
is needed at the bench.**

---

## Part 0 — Pre-registration

| Field | Value |
|---|---|
| Session ID | `2026-08-XX-spu4-reanchor` |
| Question | Does the SPU-4 probe rebuilt at HEAD — carrying T7.4's `dissonance` export **and** the 19-bit width fix — emit the expected 41-character line on Tang 25K silicon? |
| Prediction | `SPU4:P A=0000 B=0155 C=0155 D=0155 R=FF`, repeating, 115200 8N1 |
| Falsifier | Any deviation: a 36-char line (stale image), `R` ≠ `FF`, any field wrong, a mute UART, or a line that will not decode |
| Runs planned | **10 trial loads**, each capturing ≥20 consecutive lines. Plus 3 positive-control loads |
| Positive control | Flash `9599f5e4…` (pre-T7.4) — it **must** emit the **36-char** line with **no** `R=` field |
| Abort conditions | See the bottom of this file |

### Why this positive control is the right one

The failure this session is most exposed to is not the RTL — it is **"did the
new image actually load?"** A stale bitstream, a failed SRAM load, or a cached
capture would all present as a plausible-looking line. A control that merely
confirms the bench works cannot distinguish those.

So the control is the *previous* bitstream, which differs in exactly the way
under test: it lacks the `R=` field. If both images produce the same line, the
capture path is not reporting what is on the board, and the session is void.

`9599f5e4…22664` is the value `hardware_evidence.md` §3.2j records as flashed on
2026-07-08. It was rebuilt from commit `511f3f3` on 2026-08-16 and reproduced
**bit-exactly** — the fifth independent reproduction of that hash.

### What this session will NOT establish

One board, one session. It re-anchors a functional claim; it is **not** a
reliability rate, and it says nothing about other fabrics. The 161.11 MHz P&R
figure (CORRECTED 2026-08-17: was 160.38 MHz, nextpnr's post-placement
estimate) is a synthesis/P&R result and is **not** proven by this session —
keep the frequency claim and the functional claim separate.

---

## Part 1 — Rig (with the power off)

| Field | Value |
|---|---|
| Board + revision | Tang Primer 25K, bare dock |
| **Trial bitstream** | `build/bench_3_2j/TRIAL_head_0061b02f.fs` |
| **Trial SHA-256** | `0061b02f17a0f945110ad0aed269556568eb1412875268a3679baeb1cb56d67c` |
| **Control bitstream** | `build/bench_3_2j/POSCTL_pre_t74_9599f5e4.fs` |
| **Control SHA-256** | `9599f5e420f46515d99b57d2b256489440341166941be3bc9992b0b827222664` |
| Capture path | BL616 USB-CDC on **pin C3**, 115200 8N1 |
| Instruments | Board UART only |
| Device path — **by-id, never `ls -t`** | `/dev/serial/by-id/…` (record it) |
| Ambient / notes | |

**Verify both hashes at the bench before flashing anything:**

```bash
sha256sum build/bench_3_2j/*.fs
```

Neither file is in git (`build/` is ignored). If they are missing, regenerate:

```bash
# trial — current HEAD
bash build_25k_spu4_probe.sh
cp build/tang_primer_25k_spu4_probe.fs build/bench_3_2j/TRIAL_head_0061b02f.fs

# positive control — pre-T7.4, reproduces 9599f5e4...
git worktree add /tmp/pre_t74 511f3f3
cd /tmp/pre_t74 && bash build_25k_spu4_probe.sh && cd -
cp /tmp/pre_t74/build/tang_primer_25k_spu4_probe.fs build/bench_3_2j/POSCTL_pre_t74_9599f5e4.fs
git worktree remove /tmp/pre_t74 --force
```

### Power path

This probe draws almost nothing and drives no actuator, so the breadboard
resistance problem from 2026-08-06 does not apply. Note it and move on.

- [ ] USB power only, no external supply, no load current
- [ ] Device path recorded as a fixed `by-id` name: `____`

### SPI / backfeed

Not applicable — this probe is standalone with no RP2350 attached. **If an
RP2350 is connected anyway**, apply the standing sequencing rule: FPGA powered
first, RP2350 connected after; reverse on the way down. The 100 Ω series
resistors are installed.

---

## Part 2 — Execution

Load with SRAM (not flash), so each run is a fresh configuration:

```bash
openFPGALoader -b tangprimer25k build/bench_3_2j/TRIAL_head_0061b02f.fs
```

Capture to a **file per run**, never to the terminal:

```bash
mkdir -p build/bench_3_2j/captures
timeout 20 cat /dev/serial/by-id/<FIXED-NAME> \
  | tee build/bench_3_2j/captures/trial_run01.log
```

### Run order — controls first, deliberately

Run the positive control **before** the trials. If it is run afterwards and
fails, every trial before it is already in doubt.

| # | Run | Image | Capture file | Expected | Result |
|---|---|---|---|---|---|
| 1 | pos control | `POSCTL_…9599f5e4` | `posctl_run01.log` | **36-char**, no `R=` | |
| 2 | pos control | `POSCTL_…9599f5e4` | `posctl_run02.log` | 36-char | |
| 3 | pos control | `POSCTL_…9599f5e4` | `posctl_run03.log` | 36-char | |
| 4 | trial 1 | `TRIAL_…0061b02f` | `trial_run01.log` | **41-char**, `R=FF` | |
| 5 | trial 2 | `TRIAL_…0061b02f` | `trial_run02.log` | 41-char, `R=FF` | |
| … | trials 3–10 | | `trial_run03..10.log` | | |

**Rules that are not optional here:**

- **Reload the bitstream between every run.** Two captures from one
  configuration are one run, not two — the thing being sampled is the
  configure-and-start path.
- **One run is not a result.** Report `10/10`, not "it worked."
- **Do not stop early on a good result.** Finish all 10.
- **If the rig changes mid-session, the run count restarts.**

### Line-level check

Per run, confirm **every** captured line is identical, not just the first. A
line that changes between repeats is a finding, not noise.

```bash
sort -u build/bench_3_2j/captures/trial_run01.log | cat -A | head
```

`cat -A` matters: it makes the trailing `\r\n` and the exact character count
visible. The distinction under test is 36 vs 41 characters.

---

## Part 3 — Interpretation

Fill in:

- Trial pass rate: **__/10** runs, **__/__** lines
- Positive control: **__/3** runs emitted the 36-char line
- Did any trial line differ from `SPU4:P A=0000 B=0155 C=0155 D=0155 R=FF`?

**Before concluding, rule out explicitly and write down that you did:**

- [ ] Wrong device path (a by-id name was used)
- [ ] Stale bitstream (hashes verified at the bench)
- [ ] Cached/stale capture (the positive control is what proves this)

**`R=FF` is correct and expected, not a fault.** The QROT fixture settles at
A=0, B=C=D=0x155, a residual of 0x3FF, which saturates. A reading of `R=00`
would be the suspicious result — that is what a stripped or stuck-at-zero port
also produces, which is why both testbenches assert `FF`.

---

## Part 4 — Seal

- [ ] Raw captures committed or archived at a stated path
- [ ] **New** ledger entry written — §3.2j.2 — in the §3.2e.6 shape. **Do not
      edit §3.2j's measurements**; it records what ran on the board in July
- [ ] §3.2j's SUPERSEDED banner updated to point at the new entry
- [ ] `board_build_manifest.json`'s `spu4_probe` note updated: it currently says
      §3.2j is superseded *until* this bench run
- [ ] `docs/SPU4_PRODUCT_CLAIMS.md` updated if the silicon claim changes level
- [ ] Pass **rate** quoted, not a single run
- [ ] If the result is negative, **write it up anyway**

### What this closes

One session re-anchors **both** changes, because the golden line is unchanged
by the width fix — the QROT fixture's 0x3FF saturates under both 17 and 19
bits. That is why the width fix was taken *before* this bench run rather than
after: doing it afterwards would have cost a second session.

It also unblocks **T7**, the declared primary direction.

### What it does not close

The **customer ABI wrapper** (`spu4_customer_wrapper`, ABI v1.0) is **not** in
this bitstream and gains no silicon evidence from this session. It is a separate
future run — and per `SPU4_ABI.md` §7 it should be batched with something else
that already needs a bitstream move, not taken on its own.

---

## Abort conditions — stop and discard

- The positive control emits a **41-char** line → the capture path is not
  reporting what is on the board. Nothing learned; fix the rig first.
- Either bitstream's SHA-256 at the bench does not match the value above.
- The device path was selected by anything other than a fixed by-id name.
- The rig changed mid-run.
- The UART is mute on **both** images → bench-path fault, not an RTL result.
  Re-baseline against a known-good probe (e.g. `som_bmu_probe`) before
  interpreting anything.

A discarded session that is written down is worth more than a completed one
that is not.
