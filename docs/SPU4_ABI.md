# SPU-4 customer ABI — v1.0

**Status: FROZEN 2026-08-16.**
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
  in this design. The register file's read ports (`rf_dout_a`, `rf_dout_b`,
  `r0_out`) are connected to the regfile and then used nowhere, and
  `mode_auto` is a hardwired `1'b0`, so the ALU always reads the input pins and
  register operands can never reach it. `spu4_standalone_top_tb` already
  carries a `FIXME` saying writeback is not integrated. Freezing an ABI over
  that would freeze a defect into the product. One operation per `start` is the
  smallest useful contract.
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
    .dissonance(diss), .status(status)
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

> This one encodes a lesson that cost three weeks. A raw asynchronous reset pad
> driving internal resets was the root cause of the A7 `spu_a7_top` outage
> (see the A7 reset post-mortem). A customer must not be able to reproduce that
> by wiring a button or a power-supervisor output straight to `rst_n`.

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

## 5. Evidence status

| Claim | Level |
|---|---|
| G1–G6 hold | **Simulation.** `spu4_customer_wrapper_tb`, 19 checks |
| Latency ∈ [180, 183], bound 200 | **Simulation**, 124 operations |
| QROT reference fixture reproduces `0x0155` | **Simulation**, matching the vector proven in silicon at §3.2j |
| This wrapper on hardware | **NOT PROVEN.** No board has run it |
| Resource cost | **Synthesis estimate only** — see §5.1 |

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

**Three caveats, all of which matter:**

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
bits read `0` and may later gain meaning; the meaning of an existing port never
changes. A breaking change is **v2.0** and a new module name.

## 7. Open, not blocking

1. **A placed-and-routed cost, and an Fmax.** §5.1 is a synthesis estimate
   only; neither number is closed until the wrapper goes through P&R in a real
   board top.
2. **A silicon run.** The natural vehicle is the existing SPU-4 probe, which
   would move its bitstream — so this should be batched with the §3.2j bench
   re-run already owed, not taken separately.
3. **Adapters.** SPI, streaming and memory-mapped front ends layer on this
   wrapper. None are in v1.0.
4. **The programmable path.** If the sequencer's writeback is ever closed, a
   programmable variant can be added as a separate module. It must not be
   retrofitted into this one.
