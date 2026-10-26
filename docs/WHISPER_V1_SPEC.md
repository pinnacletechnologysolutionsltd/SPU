# Whisper v1 — Coherence Plane Frame Contract

One-page contract, written before RTL (per `ARLINGHAUS_SPATIAL_SYNTHESIS.md`
§7 next-steps order). Normative vocabulary: `knowledge/SPU_LEXICON.md`
("Whisper protocol", "Dissonance"). Topology per the 2026-07-08 decision:
**satellites on Tang 25K or smaller fabrics; governor on Wukong Artix-7**;
the governor's upstream whisper reaches the host via the RP2350 USB CDC.

## 1. Semantics (unchanged from v0)

Whisper is the **coherence plane**: a node continuously asserts its own
algebraic coherence. Silence means incoherent or dead — the protocol is
fail-silent by construction. A node MUST NOT whisper while non-laminar.
Whisper never carries commands; the command plane (southbridge SPI /
`spu_node_link` broadcast) is separate and request-response.

v0 (`spu_whisper_sane.v`, wired in spu4/system tops): `SANE\n` over UART
each second while `is_laminar`. v1 supersedes the line format; the
semantics, transport (UART, 115200-8N1), and cadence discipline carry over.

## 2. Frame format

One fixed-length 18-byte ASCII line per period:

```
W1 ii ff dd ss xx\n
```

| Field | Bytes | Meaning |
|---|---|---|
| `W1` | 2 + space | protocol version literal |
| `ii` | 2 hex + space | node id: `00` governor, `01`–`0D` satellites (≤13) |
| `ff` | 2 hex + space | flags: bit0 `snap_locked`, bit1 `henosis_since_last` (a Henosis pulse fired during the elapsed period), bit2 `relayed` (line reports another node's state), bits 3–7 zero |
| `dd` | 2 hex + space | dissonance = `min(\|ΣABCD post-Henosis\|, 255)` per the lexicon contract; `00` ⇔ laminar, `FF` ⇔ saturated |
| `ss` | 2 hex + space | application status byte. Current Arlinghaus use: bits 3–0 carry the satellite's semantic SOM label and bits 7–4 are zero. This field is not a sequence counter. |
| `xx` | 2 hex | XOR of all preceding bytes of the line (spaces included, `xx` and `\n` excluded), rendered as hex |
| `\n` | 1 | terminator |

Rationale for ASCII-hex over binary: matches the repo's golden-line
discipline (`SPU4:P …`, `SOM:P …`), is watchable on any serial console —
the hobbyist path — and costs 18 bytes ≈ 1.56 ms at 115200, negligible at
the 1 Hz default cadence.

Equivalence to the cluster-bridge 16-bit frame `{snap_locked,
dissonance[8], status[7]}`: `ff.bit0` ↔ snap_locked, `dd` ↔ dissonance,
low 7 bits of `ss` ↔ status payload. A whisper line is the UART rendering
of the same information — bridge RTL is reusable.

## 3. Emitter rules

1. Period: default 1 s, parameterizable; emission gated on `is_laminar`.
2. Emission is scheduled by a free-running counter, independent of
   workload and of the dissonance value — no data-dependent timing.
3. `ss` is sampled when a frame begins and remains stable for that frame.
   Missing or corrupt frames are detected by the fixed cadence, checksum, and
   three-miss rule; v1 does not provide a transport sequence counter.
4. A node emits **its own line** each period. A governor MAY additionally
   relay at most **one** satellite line per period — the highest-`dd`
   satellite — verbatim except `relayed` bit set. Bandwidth is thus
   bounded at 2 lines/period/node; no flooding, tier-up only.

## 4. Listener rules

1. A line is valid iff exactly 18 bytes, correct literal, correct XOR.
2. Any malformed or partial line counts as silence for that period.
3. Peer is declared incoherent after **3 consecutive missed periods**
   (timeout 3.5 × period), matching the `SYNC_FAIL_THRESH = 3` precedent
   in `spu_node_link`. One valid line clears the state.
4. Listeners never reply on the whisper plane.

## 5. Acceptance checklist (RTL, before board)

- [ ] TB: correct 18-byte line each period while laminar; XOR verified by
      the TB parser, not eyeballed.
- [ ] TB: emission stops within one period of `is_laminar` dropping;
      resumes with the current `ss` status byte after it returns.
- [ ] TB: `henosis_since_last` set exactly when ≥1 Henosis pulse occurred
      in the elapsed period, clear otherwise.
- [ ] TB: governor relay picks the max-`dd` satellite, sets bit2,
      preserves the satellite's `ii` and `ss`.
- [ ] TB: listener declares incoherent on the 3rd consecutive miss and on
      a corrupted-XOR storm; recovers on one valid line.
- [ ] Line start jitter: zero cycles against the free-running counter
      (assert in TB).
- [ ] `run_all_tests.py` green; satellite emitter fits alongside the
      SPU-4 Sentinel envelope on Tang 25K.

## 6. Open items / flags

- **Name collision:** `hardware/rtl/peripherals/artery/spu_whisper_tx.v`
  is unrelated PWI pulse-width telemetry using the "whisper" name.
  Candidate rename `spu_pwi_tx.v` before papers mention whisper; tracked
  here, not done silently.
- The `dd` mapping depends on the dissonance wiring OPEN in the lexicon
  (SPU-4 core does not yet drive the port). Wire per the lexicon proposal
  first; this spec inherits it.
- v2 candidates (out of scope): multi-hop gossip, per-axis dissonance
  vectors, whisper over the SPI plane for pin-starved boards.

*CC0 1.0 Universal.*
