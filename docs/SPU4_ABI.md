# SPU-4 customer ABI — v1.1

**v1.0 status: FROZEN 2026-08-16.** **v1.1 appended 2026-08-17: adds `id`,
a read-only identity port. No existing port's meaning changed — see §6.**
**Module:** `hardware/rtl/core/spu4/spu4_customer_wrapper.v`
**Executable form of this document:** `hardware/tests/spu4/spu4_customer_wrapper_tb.v`

This is the interface a customer integrates against. It is the contract layer
named in the SPU-4 product strategy, and until now it did not exist — the claim
ledger pointed at `spu4_standalone_top`, which is a bring-up vehicle, not a
product surface.

Every guarantee below has a numbered check in the testbench, written so that it
fails if the guarantee is withdrawn. A contract nobody can observe breaking is
not a contract.

---

## 1. Why this module exists rather than `spu4_standalone_top`

`spu4_standalone_top` was named as the product interface in
`docs/SPU4_PRODUCT_CLAIMS.md` without anyone having decided what that interface
*was*. Three defects followed from that, each found by accident and weeks apart:

| Found | Defect |
|---|---|
| 2026-08-14 (T7.4) | `dissonance` was a `spu4_core` port only. The fault contract's allowed sentence was false for the named product interface |
| 2026-08-16 (§3.2j.1) | The residual summed four 16-bit addends in 17 bits, so a **maximal** residual read `0x00` — perfectly laminar |
| 2026-08-16 (this work) | **`uart_tx` and `node_tx[31:0]` are declared outputs with no drivers at all.** Both read `z` in simulation |

The third is the clearest statement of the problem. The "cluster link" is a
comment placeholder with no logic behind it, and every consumer — including the
silicon probe — left both ports unconnected, so nothing ever noticed. A customer
who wired `uart_tx` to a pin would get a floating output and a working-looking
build.

These are one failure repeated: **a product surface asserted in a document and
never exercised.** Freezing an ABI, with a testbench that asserts it, is the
structural fix.

### What is deliberately excluded, and why

- **Program memory and the sequencer.** The programmable path is *not closed*
  in this design. **Partly addressed 2026-08-16** — `spu4_standalone_top` now
  has an `OPERAND_SRC` parameter, and at `1` the register file feeds the ALU,
  so `QROT Rd` rotates the quadray held in `Rd` and writes it back. That is a
  real register → ALU → register loop, proven by
  `hardware/tests/spu4/spu4_operand_src_tb.v` by poisoning the input pins and
  confirming the result still follows the register contents.

  **It is still not enough to justify a programmable ABI, for a reason the
  wiring cannot fix:** `spu4_euclidean_alu` has **no opcode input and no
  second operand port**. It performs the QROT circulant transform and nothing
  else. `alu_op` is decoded and connected to nothing. So `QADD` cannot execute
  regardless of operand routing, and `QLDI` has no path from the immediate
  into a register. Those need changes to the arithmetic core — the module
  carrying the §3.2j.2 silicon evidence — and are a separate decision.

  `OPERAND_SRC` defaults to `0` (pins), so the shipped bitstream is unchanged;
  verified by rebuilding `spu4_probe` and confirming `0061b02f…` reproduces
  bit-exactly after the change. One operation per `start` remains the smallest
  useful contract for v1.0.
- **`sentinel_mode`, `piranha_pulse`.** Research-era concepts, not product
  behaviour.
- **UART and cluster-link ports.** These are *adapters* layered on this
  wrapper, not part of the base contract — and both are undriven today.
- **`MEM_DEPTH` / `ADDR_W`.** Implementation parameters of the excluded
  sequencer.

Excluding something is not deleting it. `spu4_standalone_top` is unchanged, and
this wrapper is purely additive, so **no existing bitstream or silicon-evidence
hash moves because of it** — §3.2j's pending bench run stays valid.

---

## 2. Port list

```verilog
spu4_customer_wrapper #(
    .OPERAND_W(16)
) u_spu4 (
    .clk(clk), .rst_n(rst_n),
    .start(start), .busy(busy), .done(done),
    .a_in(a), .b_in(b), .c_in(c), .d_in(d),
    .coeff_f(f), .coeff_g(g), .coeff_h(h),
    .a_out(qa), .b_out(qb), .c_out(qc), .d_out(qd),
    .dissonance(diss), .status(status), .id(id)
);
```

| Port | Dir | Width | Meaning |
|---|---|---|---|
| `clk` | in | 1 | All logic is synchronous to the rising edge |
| `rst_n` | in | 1 | Active low. **May be driven asynchronously** — see G6 |
| `start` | in | 1 | Assert one cycle to begin. Ignored while `busy` |
| `busy` | out | 1 | An operation is in flight |
| `done` | out | 1 | **Level**, not a pulse. Results valid. Held until the next accepted `start` |
| `a_in`…`d_in` | in | signed 16 | Quadray operands, captured on an accepted `start` |
| `coeff_f/g/h` | in | signed 16 | Circulant coefficients, captured on an accepted `start` |
| `a_out`…`d_out` | out | signed 16 | Registered results, stable while `done` |
| `dissonance` | out | 8 | Saturating \|a+b+c+d\| of the completed operation |
| `status` | out | 8 | See below |
| `id` | out | 16 | **v1.1.** Synthesis-time constant identifying ABI version and wrapper variant. See §2a |

### `status` bits

| Bit | Name | Meaning |
|---|---|---|
| 0 | `busy` | Mirrors `busy` |
| 1 | `done` | Mirrors `done` |
| 2 | `henosis` | A Φ-fold normalisation fired during this operation |
| 3 | `saturated` | `dissonance` read `0xFF` for this operation |
| 4 | `start_ignored` | A `start` arrived while busy. Sticky until the next accepted `start` |
| 7:5 | reserved | Read `0` |

`start_ignored` exists so handshake misuse is *reported* rather than silently
absorbed. A customer polling only `done` would otherwise never learn that a
command was dropped.

---

## 2a. `id` — identity, v1.1

**Why this exists.** This RTL is meant to be reused: as a modular spin on a
different fabric, or built into a custom ASIC. Once that happens, the person
holding the silicon is not necessarily the person who set the Verilog
parameters — they have a chip, maybe a datasheet, and no guarantee the two
still agree. `id` lets them ask the silicon directly rather than trust
paperwork. It is a synthesis-time constant, not a register: nothing to reset,
nothing that can drift between power-cycles.

**Deliberately small.** RISC-V's `misa` discovery register works fine on its
own terms; what actually causes RISC-V compatibility pain is the size of the
*discoverable space* behind it — dozens of optional extensions and vendor
customs that turn "what does this chip support" into a combinatorial lookup.
`id` avoids that shape on purpose: one 16-bit word, a handful of fixed
fields, no open-ended extension registry. If a real need for more discovery
surface shows up later, it appends — see §6 — it does not grow this word.

### Bitfield

| Bits | Name | Meaning |
|---|---|---|
| 15:12 | `ABI_MAJOR` | Breaking-change version. `1` for this module. A breaking change is v2.0 **and a new module name** (§6), so this nibble cannot change without a rename — it exists mostly as a sanity check, not a live discriminator |
| 11:8 | `ABI_MINOR` | Additive-append version. `1` as of this port's own addition. Bumps whenever v1.x appends a port or gives a reserved bit meaning |
| 7:4 | `WRAPPER_ID` | Which product variant this is. `1` = the QROT-only Euclidean ALU wrapper — the only variant that exists today. A future wrapper (e.g. a SOM-classifier product surface over `spu4_som_edge`) gets the next unused value. Values are never reused, even if a variant is retired |
| 3:0 | reserved | Reads `0`. Same rule as `status[7:5]`: may gain meaning in a later v1.x append |

For this release, `id` = `16'h1110`.

**What `id` is not.** It does not enumerate optional hardware blocks (there
are none in this wrapper — no ECC, no configurable feature count) and it does
not attempt to describe `spu4_som_edge`'s `NUM_FEATURES` or any other RTL
parameter this module does not itself carry. Extending `id`'s meaning ahead
of a real second variant would be exactly the over-generalization this design
is trying to avoid. When a second variant is actually built, it either gets
its own `WRAPPER_ID` value under this same word (if it shares the port
shape) or its own module and its own `id` word (if it doesn't) — decided
then, against the real module, not now against a hypothetical one.

---

## 3. The guarantees

**G1 — every declared output is driven.** No port reads `X` or `Z`, at any
time, including before the first operation. Checked at reset release, after an
operation, and after a re-assert of reset. The check carries a negative control
proving the X/Z detector can fire, so the passes are not vacuous.

**G2 — operands and coefficients are captured on an accepted `start`.** The
customer may change every input on the very next cycle without disturbing the
operation. This is a real addition, not a restatement: the bare ALU requires
`F`, `G`, `H` to stay stable for the whole operation and does not itself
enforce it, and `spu4_standalone_top` wires the pins straight through.

**G3 — results are registered and held.** `a_out`…`d_out` change only at
completion and then hold until the next accepted `start`. They do not flicker
mid-operation. `done` is low from reset until the first result.

**G4 — `start` during `busy` is ignored and reported.** The operation in flight
is unaffected; `status.start_ignored` latches and clears on the next accepted
start.

**G5 — latency is bounded.** See §4.

**G6 — reset is synchronised and returns the contract to a defined state.**
`rst_n` may be driven asynchronously; it is synchronised internally
(async assert, sync release). After reset, `busy`, `done` and `status` are all
zero.

> **Integration requirement, added 2026-08-16: hold `start` off for at least
> 2 clocks after `rst_n` rises.** The synchroniser is a two-flop chain, so
> `rst_n` going high does not immediately release the datapath — a `start`
> asserted on the first cycle is swallowed and the operation never begins.
>
> This was found by the first real integration (`spu13_tang25k_spu4_abi_probe`)
> and had been missing from this document. Its symptom is silent and easy to
> misread: `busy` and `done` both stay low and the wrapper looks dead rather
> than mis-driven. The probe waits 16 clocks, which is comfortable margin.
>
> It is stated as a requirement rather than fixed in RTL because latching an
> early `start` would mean accepting an operation while the datapath is still
> in reset, which is worse. A customer-visible `ready` output is a candidate
> for a future v1.x append — it would be an appended port, which the
> compatibility promise allows.

> This one encodes a lesson that cost three weeks. A raw asynchronous reset pad
> driving internal resets was the root cause of the A7 `spu_a7_top` outage
> (see the A7 reset post-mortem). A customer must not be able to reproduce that
> by wiring a button or a power-supervisor output straight to `rst_n`.

**G7 — `id` is a fixed, correct constant, unaffected by reset.** `id` reads
`16'h1110` before the first operation ever runs, and it reads the same value
after a re-assert of reset — proving it is wiring off the module's identity,
not state that could reset to something else or drift. See §2a for the
bitfield.

---

## 4. Latency — bounded, not fixed

**Measured 2026-08-16 over 124 operations** (four hand-picked corners including
both signed extremes and zero, plus 120 randomised):

| | Clocks |
|---|---|
| Minimum observed | **180** |
| Maximum observed | **183** |
| **Contract bound** | **200** |

**Latency is bounded, not fixed.** It varies with operand and coefficient
values because the multiplier is serial. This distinction is stated explicitly
because a customer scheduling around the core can only use a constant if
latency is data-independent, and here it is not.

The testbench asserts both the 200-clock bound *and* that the data-dependent
spread stays within 8 clocks. The second check exists so that a change
introducing a large data-dependent stall fails even while staying under the
bound.

At the 12 MHz reference constraint, 200 clocks is ~16.7 µs per operation. The
reference build closes at 160.38 MHz, so the bound is ~1.25 µs at that rate —
but **the frequency claim and the latency claim are separate**, and only the
12 MHz figure has silicon behind it.

> `docs/SPU4_PRODUCT_CLAIMS.md` lists bounded latency as an open product gate.
> This closes the *measurement* half of it in simulation. It is not silicon
> evidence: no board has run this wrapper.

---

## 4a. Silicon vehicle

`hardware/boards/tang_primer_25k/spu13_tang25k_spu4_abi_probe.v` is the first
build that instantiates this wrapper. Until 2026-08-16 the ABI reached no
`.ys`, no board top and no manifest entry — it was verified only against its
own testbench, which is the same shape as the defects it was written to
prevent.

Golden line, decoded byte-for-byte off `uart_tx` by
`hardware/tests/spu13/spu13_tang25k_spu4_abi_probe_tb.v` (17 checks,
**v1.1: 16→17, the `id` field added**):

```
ABI:P B=0155 C=0155 D=0155 R=FF S=0A L=0B7 I=1110
```

- `S=0A` — `done` and `saturated` set, `busy`, `henosis` and `start_ignored`
  clear. `henosis` is **decoded and reported, not predicted**: whether the
  Φ-fold fires for this fixture is an RTL fact, and asserting a guess would
  be a fabricated expectation.
- `L=0B7` — **183 clocks measured**, matching the simulated 180–183 range and
  inside the 200-clock bound. **Confirmed on silicon 2026-08-16**, 10/10 loads,
  which closes the bounded-latency product gate with hardware evidence
  (§3.2j.3).
- `R=FF` is correct, not a fault; the QROT fixture's residual is 0x3FF.
- `I=1110` — **v1.1's `id` field, confirmed on silicon 2026-08-17**, 10/10
  loads, matching §2a's bitfield exactly (`hardware_evidence.md` §3.2j.6).
  Wired through with no decoding in the probe itself.

Deliberately a **separate target** from `spu13_tang25k_spu4_probe`: that
probe's bitstream is pinned by §3.2j and by a pre-registered bench procedure
with images already staged, so adding the wrapper to it would have voided that
preparation.

## 5. Evidence status

| Claim | Level |
|---|---|
| G1–G7 hold | **Simulation.** `spu4_customer_wrapper_tb`, 21 checks |
| Latency ∈ [180, 183], bound 200 | **Simulation**, 124 operations |
| QROT reference fixture reproduces `0x0155` | **Simulation**, matching the vector proven in silicon at §3.2j |
| This wrapper on hardware | **PROVEN 2026-08-16** — Tang 25K, 10/10 loads, `hardware_evidence.md` §3.2j.3 |
| `id` on hardware | **PROVEN 2026-08-17** — Tang 25K, 10/10 loads, `I=1110` matching §2a exactly, `hardware_evidence.md` §3.2j.6 |
| Resource cost | **Post-P&R, measured** — see §5.1. Predates `id`; a 16-bit constant net is expected to be negligible but has not been re-measured |

Do not describe this wrapper as silicon-proven. The *core beneath it* has
silicon evidence (§3.2j, 2026-07-08); the wrapper does not, and the two are
different claims — which is the distinction this whole document exists to
enforce.

### 5.1 Resource cost — synthesis estimate, 2026-08-16

`yosys 0.63+87`, `synth_gowin -family gw5a`, the wrapper as top with the ALU
and serial multiplier beneath it:

| Cell | Count |
|---|---|
| LUT1 / LUT2 / LUT3 / LUT4 | 40 / 21 / 142 / 91 — **294 LUTs total** |
| MUX2_LUT5 | 35 |
| ALU | 119 |
| DFF / DFFCE / DFFRE | 12 / 2 / 419 — **433 flops total** |

**Post-P&R, 2026-08-16 (pre-`id`, v1.0)** — `spu13_tang25k_spu4_abi_probe`,
the real board top:

| | Value |
|---|---|
| LUT4 | **1,044 / 23,040 = 4.5%** |
| ALU | 500 |
| DFF | 381 |
| Fmax (`u_abi.clk`) | **160.26 MHz**, as originally recorded — **now in question, see the flag below** |
| Bitstream | `1e70739d…` reproduced 2× |

**Post-P&R, 2026-08-17 (v1.1, with `id` wired into the probe's UART line)**:

| | Value |
|---|---|
| LUT4 | **1,066 / 23,040 = 4.6%** (+22 over the pre-`id` build) |
| ALU | 500 (unchanged) |
| DFF | 381 (unchanged) |
| Fmax (`u_abi.clk`) | **142.25 MHz**, the final post-route figure (see flag below on which of nextpnr's two numbers this is) |
| Bitstream | `23ba4a3f…`, commit `daabf25`, rebuild reproduces it bit-exactly |

`id` itself is a synthesis-time constant net — no new flops, no new ALU
cells — which is exactly what the unchanged ALU/DFF counts confirm. The +22
LUT4 is attributed to the probe's UART message logic growing by one field
(four more `h()` hex-nibble decodes and a wider `msg_byte` case), not to `id`
itself, which is just a 16-bit wire bundle. **This is inference from the cell
delta, not a checked claim** — the nextpnr critical-path report for this build
does not run through the message-byte mux at all; it runs through
`spu4_dissonance.v`'s residual adder chain into an ABC-mapped LUT chain and
into a flip-flop, unrelated to either `id` or the UART logic. Do not repeat
"the UART mux is on the critical path" as a checked fact; it isn't, and an
earlier draft of this document said so without checking.

> **Flag: nextpnr prints two `Max frequency` lines per run, and this
> document has been citing the wrong one.** The first appears right after
> placement (an *estimate*, before the router has run); the second, following
> a full `Critical path report`, appears at the very end of the run and is
> the final post-route figure. Rebuilding the pre-`id` commit to get the
> LUT4/ALU/DFF numbers above surfaced this: the **160.26 MHz** already
> published for that build (here, in `hardware_evidence.md` §3.2j.3, and in
> `board_build_manifest.json`) is the placement-stage estimate — the actual
> final post-route figure from that same build is **211.60 MHz**. For the new
> `id`-bearing build the two figures are 183.52 MHz (estimate) and 142.25 MHz
> (final); 142.25 MHz above is correctly the final one. **Not yet corrected
> across the repo** — this needs its own pass to fix §3.2j.3, this table's
> pre-`id` row, and the manifest entry consistently, and to check whether
> other Fmax citations elsewhere have the same mistake. Flagged rather than
> silently rewritten because it touches already-published silicon evidence.
> **Both figures are the PROBE**, not the wrapper alone — see below —
> regardless of which one turns out to be the currently-published error.

**That figure is the PROBE, not the wrapper alone** — it includes the UART
engine, the test FSM and the LEDs. For scale, `spu4_probe` (standalone top +
sequencer + decoder + regfile + ALU + the same UART fixture) is 982 / 462 /
336. So the ABI probe is slightly *larger* despite excluding the sequencer,
decoder and register file: the capture and result registers that buy G2 and G3
cost roughly what the programmable path cost. That is the price of the
guarantees, and it is worth stating rather than hiding.

**Three caveats on the yosys estimate below, all of which matter:

1. **This is a yosys cell count, not a placed-and-routed figure.** The repo has
   already been burned once by quoting a synthesis estimate as a resource
   measurement (T7.0, the "~400 LUT" figure). These are not comparable to the
   probe's 982 LUT4 / 462 ALU / 336 DFF, which is post-P&R on a different
   design.
2. **The 115 IBUF and 82 OBUF in the raw report are an artifact** of
   synthesising this as a top-level module. Instantiated inside a customer
   design, as intended, there are no IO buffers.
3. **The flop count includes the contract itself.** The capture registers
   (7 × 16 = 112) and result registers (4 × 16 = 64) are what buy G2 and G3.
   That is the price of the guarantees, and it is deliberate.

---

## 6. Compatibility promise

Within **v1.x**: ports are added only at the end of the list; reserved `status`
bits (and, as of v1.1, reserved `id` bits) read `0` and may later gain meaning;
the meaning of an existing port never changes. A breaking change is **v2.0**
and a new module name.

**v1.1, 2026-08-17: `id` appended.** Every port from v1.0 keeps its position,
width and meaning; `id` is added at the end of the list per this rule. G1–G6
and their checks are untouched; this release adds G7 and does not renumber
the others.

## 7. Open, not blocking

1. ~~A placed-and-routed cost, and an Fmax.~~ **CLOSED 2026-08-16** — see
   §5.1. 1,044 LUT4 / 500 ALU / 381 DFF via `spu13_tang25k_spu4_abi_probe`.
   **The `160.26 MHz` figure recorded alongside it is now flagged as likely
   wrong** — see the flag in §5.1. Reopening this item's Fmax half, not its
   LUT/ALU/DFF half.
2. **A silicon run.** **Corrected 2026-08-16:** this previously said to batch
   it into the existing SPU-4 probe. That is wrong — §3.2j is now
   pre-registered with both bitstreams already built and staged, and modifying
   `spu4_probe` would void that preparation. The vehicle is the separate
   `spu4_abi_probe` (§4a), which can be flashed in the same bench sitting as a
   distinct block **after** §3.2j is sealed.
3. **Adapters.** SPI, streaming and memory-mapped front ends layer on this
   wrapper. None are in v1.0.
4. **The programmable path.** If the sequencer's writeback is ever closed, a
   programmable variant can be added as a separate module. It must not be
   retrofitted into this one.
5. ~~`id` has no board run and is not wired into `spu4_abi_probe`'s UART
   output.~~ **CLOSED 2026-08-17** — see §4a and §5. `id` is now the probe's
   `I=` field, confirmed 10/10 loads on Tang 25K (`hardware_evidence.md`
   §3.2j.6). Resource cost also measured while closing this: 1,066 LUT4 (+22)
   / 500 ALU / 381 DFF (both unchanged) — see §5.1.
6. **The Fmax methodology flag in §5.1.** `160.26 MHz` (pre-`id`) and
   possibly other Fmax citations in this repo may be nextpnr's post-placement
   estimate rather than the final post-route figure. Needs a dedicated pass
   across §3.2j.3, this document's §5.1, and `board_build_manifest.json` —
   discovered 2026-08-17 as a side effect of the `id` resource measurement
   above, not yet acted on.
