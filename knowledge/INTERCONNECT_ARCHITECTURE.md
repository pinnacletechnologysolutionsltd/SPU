# SPU Interconnect Architecture — Tiers, Homogeneity, Determinism Boundary

Planning doc (2026-07-08). Fixes the connectivity model from bare pins to
the Internet, states the southbridge homogeneity contract, and maps what
multi-compute actually requires before RTL is written. Normative
vocabulary: `knowledge/SPU_LEXICON.md`. Deployment geometry:
`ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7. Prior art: the archived ESP32-S3
analysis in `docs/archive/legacy/MULTIPLATFORM_SOUTHBRIDGE_STRATEGY.md`
(superseded on MCU choice, still useful on WiFi trade-offs).

## 0. Two planes, one boundary

Everything below carries exactly two traffic classes:

- **Command plane** — request/response, single-master: the southbridge
  SPI protocol contract, 8 opcodes (`docs/SOUTHBRIDGE_SPI_PROTOCOL.md`).
- **Coherence plane** — one-way, periodic, fail-silent: whisper lines
  (`docs/WHISPER_V1_SPEC.md`).

**The determinism boundary:** the SPU's timing guarantees (Fibonacci
dispatch, deterministic cycle counts, bit-exact replay) end at the FPGA
pins. Every transport beyond the pins — MCU, USB, radio, IP — carries
frames *unchanged in content* but adds nondeterministic latency. Bridges
therefore relay frames; they never extend timing claims. This is why both
frame formats are fixed-length and self-checking: they survive any
transport without renegotiation, and a listener can validate a frame
without trusting the path it took.

Corollary for multi-compute: clusters are **coherence-aligned, not
cycle-aligned**. Each node keeps its own deterministic internal schedule;
cross-node ordering is established by frames (sequence numbers, dissonance
reports), not by shared clock phase. We do not promise lockstep across
boards, and papers must not imply it.

## 1. Tier model

| Tier | Fabric class | Host path | Planes |
|---|---|---|---|
| **T0 — bare pins** | iCE40UP5K / GW1N-1 / iCESugar-class (SPU-4 Sentinel, SOM-SIDECAR spins) | none — PMOD/pin headers | whisper out on a UART pin; command = raw SPI slave pins or a preloaded program; a bench Pico can drive it, but nothing is resident |
| **T1 — southbridge** | Tang 25K and larger | RP2350 (SD boot, hydration, USB CDC) | both planes, homogeneous contract (§2) |
| **T2 — cluster links** | FPGA ↔ FPGA, wired | `spu_node_link` + whisper between boards | both planes intra-constellation (§3) |
| **T3 — network bridge** | anything ↔ LAN/Internet/radio | southbridge- or host-owned tunnel | both planes encapsulated (§4–5) |

T0 is an *exemption, not a degraded T1*: the smallest fabrics get pins
because a resident MCU would dwarf the node. Everything Tang-25K-sized and
up speaks the same southbridge contract.

## 2. Southbridge homogeneity contract (T1)

One protocol, one console grammar, any large-enough board. Concretely:

1. The SPI opcode set — 8 opcodes: `0xA0` manifold, `0xAC` status, `0xAD`
   scale table, `0xAE` QR commit, `0xAF` HEX projection, `0xB0` sentinel
   telemetry, `0xB1` instruction write, `0xA5` RPLU config write — is
   **frozen as protocol v1**. Extensions add opcodes; existing opcodes
   are never repurposed. `docs/SOUTHBRIDGE_SPI_PROTOCOL.md` §"Version &
   Compatibility Promise" is the contract text (done, 2026-07-08).
2. The RP2350 USB CDC console grammar is part of the contract — host
   tooling written against one board works against all boards.
3. Adding a board = a pin map + constraints file. **No protocol forks per
   board.** Board differences live in exactly one table (per-board `.cst`
   plus a pin-map row), the way the bench adapter locks its pin
   assignments to silicon-verified firmware.
4. Current coverage: Tang 25K (proven), Wukong A7 J11 (proven),
   Colorlight i9 (planned — same contract when it arrives), iCESugar-class
   (T0 exempt).

The homogeneity contract is what makes "flash a spin to an eval board"
scale: the host library (spin catalog §4) is written once against the
contract, not per board.

## 3. Multi-compute preparation (T2) — what actually has to exist

The cluster RTL that exists (`spu4_cluster_bridge`, `spu_node_link`,
`spu13_cluster_controller`) is **intra-chip**: frames move on parallel
16/32-bit ports. Board-to-board multi-compute needs pieces that do not
exist yet, in this order:

1. **Single-board cluster probe** (no new hardware): one SPU-4 satellite +
   SPU-13 governor over the cluster bridge on the Wukong (per the
   2026-07-08 decision: Tang is the satellite-class board, Wukong the
   governor board — for the single-board probe the Wukong hosts both
   sides). Proves the aggregation semantics with zero link risk.
2. **`spu_node_link` serialization contract** (one-page doc before RTL,
   like whisper v1): the parallel frames need a wire format for a PMOD
   cable between two boards. Candidate: reuse the whisper line discipline
   (fixed-length ASCII, XOR, UART phy) for the satellite→governor
   direction, and a framed binary UART format for the 32-bit governor
   broadcast. Boards have independent clocks — the format must be
   self-synchronizing (UART already is) and every frame self-checking
   (both already are). No shared clock, no source-synchronous strobes.
3. **Two-board silicon**: Tang (satellite) ↔ Wukong (governor) over a
   PMOD-to-PMOD cable. This is Arlinghaus §7 next-step (1), and it waits
   only on the second board being on the bench at the same time.
4. **Whisper tunneled to the host** through the southbridge CDC — the
   governor's uplink becomes visible to a PC, which is also the first
   half of the network bridge (§5).

## 4. Radio links (constellation transports)

Assessed against the two planes. The design rule falls out of the frame
formats: **whisper is radio-native** (one-way, periodic, loss-tolerant,
fail-silent, self-checking — a lost line is indistinguishable from
silence, which is already a defined state); **the command plane needs a
reliable transport** (it is request/response with state).

| Transport | Whisper (coherence) | Command plane | Notes |
|---|---|---|---|
| **LoRa** (RFM95-class on southbridge SPI) | excellent — an 18-byte line at ≤1 Hz fits km-range links and EU 868 MHz 1% duty limits with huge margin | no — latency and loss | the remote-sentinel story: solar SPU-4 nodes whispering over LoRa |
| **ESP-NOW** (ESP32 as radio coprocessor) | good — 250 B frames, low latency | marginal — acknowledged but unordered | adds a second MCU family; keep as experiment |
| **BLE** (Pico 2 W) | fine for phone/bench demos | no | telemetry showcase, not infrastructure |
| **WiFi/IP** (Pico 2 W or ESP32) | fine (UDP, §5) | yes (TCP, §5) | full bridge; nondeterministic; the SDK already carries lwIP/CYW43 |

## 5. Conventional network bridge (LAN/Internet) — feasible now, at T1

The bridge is a southbridge (or host-PC) function. The FPGA never speaks
IP — an FPGA-side TCP stack would violate both the Lithic discipline and
the determinism boundary for zero benefit. Encapsulation:

- **Whisper → UDP**: one line per datagram, unmodified (it is already
  fixed-length and checksummed). Optional multicast group per
  constellation so any listener sees all beacons. Loss model identical to
  a serial link: a missing datagram is a missed period.
- **Command plane → TCP**: one session = one master (preserving
  single-master SPI semantics end-to-end); framing = opcode + length +
  payload + CRC. The session owner is the *only* command master while
  connected.

Hardware ladder, cheapest first:

1. **Host-PC bridge, zero new hardware**: a Python daemon on the bench PC
   speaks USB CDC to the RP2350 and exposes UDP/TCP on the LAN. The host
   library it builds on (`software/spu_host/`, §2/spin catalog §4) is
   done as of 2026-07-08; the bridge daemon itself is not yet written —
   it is a thin wrapper adding a UDP/TCP front end to `SPUHostClient`.
2. **Pico 2 W southbridge variant**: same firmware plus lwIP; the node
   joins the LAN itself. WiFi + BLE for free.
3. **W5500 wired Ethernet module** on the RP2350's SPI: cheap, wired,
   robust; good for permanent bench/cluster installs.
4. **Colorlight i9 native PHYs**: already earmarked as "Ethernet
   experiments" in `docs/fpga_board_scaling_strategy.md`; PHY part numbers
   to be verified when hardware arrives. Treat as research (a MAC in
   fabric), not as the plan of record.

**Security note (claim discipline):** the v1 bridge assumes a trusted
bench/LAN. The command plane carries instruction writes — exposing it to
the open Internet requires authentication and is explicitly out of scope
for v1; whisper (read-only telemetry) is the only plane that may cross
untrusted networks, and even then it discloses node health. State this
wherever the bridge is documented.

## 6. Order of work and open questions

Keyboard-only, in order: (1) southbridge protocol doc gains version
header + compatibility promise; (2) host-PC bridge daemon + host library
(one deliverable — the library's transport abstraction is "serial or
socket"); (3) node_link serialization one-pager; (4) single-board cluster
probe RTL against the Arlinghaus checklist. Hardware-gated: two-board
link (second board on bench), Pico 2 W / W5500 / LoRa variants (bench
budget), i9 Ethernet (board arrival).

Open questions: Pico 2 W vs W5500 as the first resident bridge (defer to
bench-budget time); whether the governor's whisper uplink should also be
mirrored on its own T0 pin for MCU-less monitoring; multicast group and
port conventions for UDP whisper.

*CC0 1.0 Universal.*
